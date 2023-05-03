#!/bin/bash

source .python3/bin/activate
export FLASK_APP=app.py
flask --debug run
