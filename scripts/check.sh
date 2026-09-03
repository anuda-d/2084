#!/usr/bin/env sh
set -eu

python3 scripts/check_autonomous_loop_contract.py
python3 -m unittest discover -s tests -p 'test_*.py'

if git ls-files --error-unmatch GATES.md >/dev/null 2>&1; then
  echo 'GATES.md must remain untracked' >&2
  exit 1
fi

if test -n "$(git ls-files '.unlazy/**')"; then
  echo '.unlazy artifacts must remain untracked' >&2
  exit 1
fi

git diff --check
