#!/usr/bin/env bash
# Reproduce this example's run, judgment and receipt from the committed fixture outputs.
# Every check is deterministic, so no API key is needed and nothing leaves your machine.
set -euo pipefail
cd "$(dirname "$0")"
skillgate lint --deterministic-only
skillgate criteria --coverage
out=$(skillgate run --mode manual)
echo "$out"
run_dir=$(echo "$out" | sed -n 's/^Created \(.*\)\. Fill.*/\1/p')
cp -r fixture-outputs/rt-* "$run_dir/outputs/"
cp fixture-outputs/capture.yaml "$run_dir/capture.yaml"
skillgate judge
skillgate receipt
skillgate verify-receipt "$(ls -d receipts/*/ | tail -1)receipt.json"
skillgate check-stale
