#!/bin/bash

cd gw2
while [ 1 ]
do
    python3 gw2.py --ctrl_port 10001 --job_port 8082
    sleep 5
done

