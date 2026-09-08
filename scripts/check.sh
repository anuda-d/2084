#!/usr/bin/env sh
set -eu

python3 scripts/check_autonomous_loop_contract.py
python3 -m unittest discover -s tests -p 'test_*.py'

git diff --check
