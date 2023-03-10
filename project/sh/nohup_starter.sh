#!/bin/bash

START_FILE="$1"
# START_FILE='sh/start_main.sh'
SESSIONS_DIR='content/sessions/running'
PID="$$"
MAX_SLEEP=2073600
TRASH='/dev/null'
GIT_BRANCH=$(git branch | grep '*' | awk -F ' ' '{print $NF}' | sed 's#)##')
START_DATE=$(date -u "+%Y-%m-%d_%H.%M.%S")
SESSION_ID="$START_DATE"_"$GIT_BRANCH"

# SESSION_ID='2023-02-12_11.44.07_Solomon-v2.1.3.1'

SESSION_DIR="$SESSIONS_DIR/$SESSION_ID"
INPUTS_DIR="$SESSION_DIR/inputs"
INPUTS_VIEW_DIR="$INPUTS_DIR/view_$START_DATE"
STDIN_VIEW_FILE="$INPUTS_VIEW_DIR/view_stdin.pipe"
STDOUT_VIEW_FILE="$INPUTS_VIEW_DIR/view_stdout.txt"
ERROR_VIEW_FILE="$INPUTS_VIEW_DIR/view_error.txt"
PID_VIEW_FILE="$INPUTS_VIEW_DIR/view_pids.txt"

start_pipe(){
    ls -1 "$START_FILE" > "$TRASH"
    FLAG=$?
    if [ "$FLAG" != 0 ]; then
         return "$FLAG"
    fi

    # mkdir "$SESSION_DIR" &&
    #     mkdir "$INPUTS_DIR" &&
    #     mkdir "$INPUTS_VIEW_DIR" &&
    #     mkfifo "$STDIN_VIEW_FILE" &&
    #     nohup echo $((while true; do sleep "$MAX_SLEEP"; done) > "$STDIN_VIEW_FILE") >> "$STDOUT_VIEW_FILE" 2>> "$ERROR_VIEW_FILE" &!
    # WAKER_PID=$!

    (ls -1 "$SESSION_DIR" > "$TRASH"            2>&1    || mkdir "$SESSION_DIR")        &&
        (ls -1 "$INPUTS_DIR" > "$TRASH"         2>&1    || mkdir "$INPUTS_DIR")         &&
        (ls -1 "$INPUTS_VIEW_DIR" > "$TRASH"    2>&1    || mkdir "$INPUTS_VIEW_DIR")    &&
        mkfifo "$STDIN_VIEW_FILE" &&
        nohup echo $((while true; do sleep "$MAX_SLEEP"; done) > "$STDIN_VIEW_FILE") >> "$STDOUT_VIEW_FILE" 2>> "$ERROR_VIEW_FILE" &!
    WAKER_PID=$!

    # Read pipe to receive first input from While loop and start to loop
    # Without this step the PID of the sleep process shouldn't be get
    cat $STDIN_VIEW_FILE > "$TRASH" 2>&1 &
    CAT_PID=$!
    sleep 5
    kill "$CAT_PID"

    WAKER_CHILD_PIDS=$(ps -Af | grep "$WAKER_PID" | grep -Ev "grep|$PID" | sed -e 's#  *# #g' -e 's#^ ##' | cut -d' ' -f '2,3')
    WAKER_PIDS=$(ps -Af | grep -E $(echo "$WAKER_CHILD_PIDS" | sed 's# #|#g') | grep -v 'grep' | sed -e 's#  *# #g' -e 's#^ ##' | cut -d' ' -f '2' | sort -r | tr '\n ' ' ' | sed 's# $##')
    WAKER_PIDS_IN_COL=$(echo "$WAKER_PIDS" | tr ' ' '\n')

    ls "$STDIN_VIEW_FILE" > "$TRASH" &&
        nohup echo $(source "$START_FILE" < "$STDIN_VIEW_FILE" >> "$STDOUT_VIEW_FILE" 2>&1 ; kill $(echo "$WAKER_PIDS_IN_COL" && rm "$STDIN_VIEW_FILE") >> "$STDOUT_VIEW_FILE" 2>> "$ERROR_VIEW_FILE") > "$TRASH" 2>&1 &!

    ls -l "$STDIN_VIEW_FILE" > "$TRASH" &&
        exec 6> "$STDIN_VIEW_FILE" &&
        echo 'Yes'          >&6 &&
        echo "$SESSION_ID"  >&6

    echo "PPID:             $PPID"              >> "$PID_VIEW_FILE"
    echo "PID:              $PID"               >> "$PID_VIEW_FILE"
    echo "WAKER_PID:        $WAKER_PID"         >> "$PID_VIEW_FILE"
    echo "WAKER_CHILD_PIDS: $WAKER_CHILD_PIDS"  >> "$PID_VIEW_FILE"
    echo "WAKER_PIDS:       $WAKER_PIDS"        >> "$PID_VIEW_FILE"

    echo "Input1:   >&6"
    echo "Input2:   $STDIN_VIEW_FILE"
    echo "Output:   $STDOUT_VIEW_FILE"
}

# Main
start_pipe