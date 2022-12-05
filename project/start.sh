#!/bin/bash

git branch | grep -E "^\* .+"
source env_3.9.13/bin/activate
python3 main.py  
