#!/bin/bash
#RESTART
./stop.sh
./start.sh

tail -f logs/*.log