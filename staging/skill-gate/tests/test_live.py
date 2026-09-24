"""One opt-in smoke test against the real judge model. Skipped unless SKILLGATE_LIVE=1.

    SKILLGATE_LIVE=1 ANTHROPIC_API_KEY=... pytest tests/test_live.py
"""

import os

import pytest

from skillgate.config import ModelConfig
from skillgate.judge import Check, judge_with_model
from skillgate.llm import AnthropicJSONModel
from skillgate.prompts import load_prompt

pytestmark = pytest.mark.live


@pytest.mark.skipif(os.environ.get("SKILLGATE_LIVE") != "1" or not os.environ.get("ANTHROPIC_API_KEY"),
                    reason="live test: set SKILLGATE_LIVE=1 and ANTHROPIC_API_KEY")
def test_live_judge_call(tmp_path):
    from skillgate.judge import CallLog

    class Cfg:
        def price(self, *a):
            return None

    model = AnthropicJSONModel(ModelConfig(provider="anthropic", model="claude-opus-5",
                                           settings={"effort": "low", "max_tokens": 4000}))
    log = CallLog(tmp_path / "log.jsonl", Cfg())
    out = "Decision: DENY\nPolicy: P2\nReason: The item was used: \"I've used it twice\"."
    res = judge_with_model(model, load_prompt("judge.v1"), Check("E1", "expectation", "The decision is DENY.", None),
                           "I've used it twice and don't need it anymore.", out, log, {})
    assert res["verdict"] == "PASS", res
    assert res["served_model"] == "claude-opus-5"
