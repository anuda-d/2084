#!/usr/bin/env sh
set -eu

python3 -m unittest discover -s experiments/tests -p 'test_*.py'
