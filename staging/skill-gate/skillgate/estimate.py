"""`skillgate estimate`: model calls, tokens and cost before anything is spent.

Token counts are estimated offline from character counts (no API call), with
assumed output lengths and a safety margin, all set in skillgate.yaml under
`estimate`. A paid step aborts when its estimate exceeds `budget.max_usd`,
unless the user passes --confirm-budget. A model with no configured price
cannot be estimated, so a paid step refuses to start.
"""

from __future__ import annotations

import math
from typing import Any

from skillgate.cache import Cache
from skillgate.cases import Case
from skillgate.config import Config
from skillgate.prompts import load_prompt
from skillgate.skill import Document, Skill
from skillgate.util import SkillGateError


def tokens(text: str, chars_per_token: float) -> int:
    return math.ceil(len(text) / chars_per_token) if text else 0


def _price(cfg: Config, model: str, inp: int, out: int, calls: int) -> float:
    if calls == 0:
        return 0.0
    cost = cfg.price(model, inp, out)
    if cost is None:
        raise SkillGateError(
            f"No price for model '{model}' in skillgate.yaml (pricing: {model}: {{input_per_mtok, "
            f"output_per_mtok}}). Skill Gate will not start a paid step it cannot estimate."
        )
    return cost


def model_checks_per_case(criteria: list, case: Case) -> int:
    return sum(1 for c in criteria if c.check is None) + sum(1 for e in case.expectations if e.check is None)


def estimate(cfg: Config, *, cases: list[Case], criteria: list, k: int, mode: str,
             skill: Skill | None = None, references: list[Document] | None = None,
             outputs: dict[str, str] | None = None, cache_keys: dict[str, str] | None = None) -> dict[str, Any]:
    """Estimate one run and its judging. `outputs` maps "case/repeat" to text when outputs exist."""
    e = cfg.estimate
    cpt = float(e["chars_per_token"])
    root = cfg.root
    result: dict[str, Any] = {"mode": mode, "k": k, "cases": len(cases), "assumptions": dict(e)}

    ex = {"calls": 0, "cached": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": None}
    if mode == "api":
        if cfg.executor is None:
            raise SkillGateError("API mode needs an executor section in skillgate.yaml")
        from skillgate.executor import assemble

        ex["model"] = cfg.executor.model
        out_assumed = int(e["executor_output_tokens"])
        if cfg.executor.settings.get("max_output_tokens"):
            out_assumed = min(out_assumed, int(cfg.executor.settings["max_output_tokens"]))
        cache = Cache(cfg.paths["cache"])
        for case in cases:
            system, user, _ = assemble(skill, references or [], case.rendered_input(root))
            for r in range(1, k + 1):
                if cache_keys and cache.get(cache_keys[f"{case.id}/{r}"]) is not None:
                    ex["cached"] += 1
                    continue
                ex["calls"] += 1
                ex["input_tokens"] += tokens(system, cpt) + tokens(user, cpt)
                ex["output_tokens"] += out_assumed
        ex["cost_usd"] = _price(cfg, ex["model"], ex["input_tokens"], ex["output_tokens"], ex["calls"])
    result["executor"] = ex

    jd = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": cfg.judge.model}
    prompt = load_prompt("judge.v1")
    template = tokens(prompt.system + prompt.user, cpt)
    assumed_output_text = "x" * int(e["executor_output_tokens"] * cpt)
    for case in cases:
        n = model_checks_per_case(criteria, case)
        if not n:
            continue
        inp = tokens(case.rendered_input(root), cpt)
        texts = {c.id: c.text for c in criteria if c.check is None}
        texts.update({x.id: x.text for x in case.expectations if x.check is None})
        for r in range(1, k + 1):
            out_text = outputs.get(f"{case.id}/{r}", "") if outputs is not None else assumed_output_text
            for text in texts.values():
                jd["calls"] += 1
                jd["input_tokens"] += template + inp + tokens(out_text, cpt) + tokens(text, cpt)
                jd["output_tokens"] += int(e["judge_output_tokens"])
    jd["cost_usd"] = _price(cfg, jd["model"], jd["input_tokens"], jd["output_tokens"], jd["calls"])
    result["judge"] = jd

    margin = float(e["margin"])
    result["total_cost_usd"] = round((ex["cost_usd"] + jd["cost_usd"]) * margin, 4)
    result["budget_usd"] = cfg.budget.get("max_usd")
    return result


def check_budget(cfg: Config, est: dict[str, Any], confirm: bool, what: str) -> None:
    budget = cfg.budget.get("max_usd")
    if budget is None:
        raise SkillGateError("Set budget.max_usd in skillgate.yaml before any paid step.")
    if est["total_cost_usd"] > float(budget) and not confirm:
        raise SkillGateError(
            f"Estimated cost of {what} is ${est['total_cost_usd']:.2f}, above the budget of "
            f"${float(budget):.2f}. Nothing was sent. Run `skillgate estimate` for the breakdown, then "
            f"raise budget.max_usd or pass --confirm-budget."
        )


def render(est: dict[str, Any]) -> str:
    ex, jd = est["executor"], est["judge"]
    lines = [f"Estimate for {est['cases']} case(s) × {est['k']} repeat(s), mode {est['mode']}:"]
    if est["mode"] == "api":
        lines.append(f"  executor {ex['model']}: {ex['calls']} call(s) ({ex['cached']} cached, free), "
                     f"~{ex['input_tokens']} input / ~{ex['output_tokens']} output tokens, ${ex['cost_usd']:.4f}")
    else:
        lines.append("  executor: manual mode, no API calls")
    lines.append(f"  judge {jd['model']}: {jd['calls']} call(s), ~{jd['input_tokens']} input / "
                 f"~{jd['output_tokens']} output tokens, ${jd['cost_usd']:.4f}")
    a = est["assumptions"]
    lines.append(f"  total with margin ×{a['margin']}: ${est['total_cost_usd']:.2f}"
                 + (f" (budget ${float(est['budget_usd']):.2f})" if est["budget_usd"] is not None else " (no budget set)"))
    lines.append(f"  assumptions: {a['chars_per_token']} characters per token; {a['executor_output_tokens']} output "
                 f"tokens per executor call; {a['judge_output_tokens']} per judge call")
    return "\n".join(lines)
