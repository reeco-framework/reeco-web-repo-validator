#!/bin/bash
# python3 -m venv .python3
source .python3/bin/activate
export FLASK_APP=app.py
#flask --debug run
nohup python3 app.py > run-app.log 2>&1 &
echo $!> run-app.pid
