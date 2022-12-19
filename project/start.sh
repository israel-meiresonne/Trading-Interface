#!/bin/bash

PY_ENV=env_3.9.13/bin/activate
FILE_DRAFT="start_draft.sh"
draft=$(cat "$FILE_DRAFT" | sed "s#source .*#source $PY_ENV#") ; echo "$draft" > "$FILE_DRAFT"

git branch | grep -E "^\* .+"
source "$PY_ENV"
python3 main.py
