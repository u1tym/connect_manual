#!/bin/bash

cd gw2
while [ 1 ]
do
    python3 gw2.py --ctrl_port 10002 --job_port 5902 --logfile gw2_5902
    sleep 5
done

