#!/bin/bash
pid=`cat run-app.pid` && kill $pid && rm run-app.pid && echo "killed"