#!/bin/bash

FIFO='draft/trash/input.pipe'
OUPUT='draft/trash/output.txt'
ls "$FIFO" > /dev/null 2>&1 || mkfifo "$FIFO"
python3 'main.py' < "$FIFO" > "$OUPUT" 2>&1 &!
exec 6> "$FIFO"
