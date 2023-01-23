#!/bin/bash

PY_ENV='env_3.9.13/bin/activate'
DRAFT_FILE="sh/start_draft.sh"
draft=$(cat "$DRAFT_FILE" | sed "s#source .*#source '$PY_ENV'#") ; echo "$draft" > "$DRAFT_FILE"

git branch | grep -E "^\* .+"
source "$PY_ENV"
python3 'main.py'
