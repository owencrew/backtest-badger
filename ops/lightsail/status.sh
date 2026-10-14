#!/bin/sh
# Offline inventory only. Never load credentials, connect, fit, refresh or score.
set -eu
cd /opt/backtest-badger/current
export PYTHONDONTWRITEBYTECODE=1
result=0
.venv/bin/badger forward-status || result=1
.venv/bin/python -m backtest_badger.forward_scoring_operations status || result=1
exit "$result"
