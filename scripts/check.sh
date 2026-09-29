#!/usr/bin/env sh
set -eu

python3 -m unittest discover -s tests -p 'test_*.py'

git diff --check
git diff --cached --check
