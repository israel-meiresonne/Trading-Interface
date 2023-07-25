#!/bin/bash

DRAFT_FILE='sh/start_draft.sh'
TRASH='/dev/null'
SLEEP_TIME=15
# PAIRS[1]='COCOS/USDT'
# PAIRS[2]='CTXC/USDT'
# PAIRS[3]='DOGE/USDT'
# PAIRS[4]='GTO/USDT'
# PAIRS[5]='MITH/USDT'

# # # # # # # # #
#   Backtest    #
# # # # # # # # #

# REPORT_MODE='Record'
# FUNC='backtest2'
# STRATEGY='Solomon'
# DAY_ID='January_2023_10_April_2023'
# PAIRS[1]='COCOS/USDT'
# PAIRS[2]='CTXC/USDT'
# PAIRS[3]='DASH/USDT'
# PAIRS[4]='LINK/USDT'
# PAIRS[5]='XTZ/USDT'

# for i in {1..5} ; do
#     PAIR=${PAIRS[$i]}
#     echo "$(date -u '+%Y-%m-%d_%H.%M.%S') >> PAIRS[$i] => '$PAIR'"
#     nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!$DAY_ID!$PAIR" | sed "s#!#\n#g" | sh "$DRAFT_FILE" > "$TRASH" 2>&1) > "$TRASH" 2>&1 &!
#     if [ "$i" != 5 ]; then
#         sleep "$SLEEP_TIME"
#     fi
# done

# # # # # # # # # # #
#   Loop Backtest   #
# # # # # # # # # # #

# SESSION_ID="$1"
# REPORT_MODE='Record'
# FUNC='loop_backtest2'
# STRATEGY='Solomon'
# # DAY_ID='May_2021'
# # DAY_ID='May_2022'
# DAY_ID='20_October_2022_20_November_2022'

# for i in {1..5} ; do
#     echo "$(date -u '+%Y-%m-%d_%H.%M.%S') >> $i"
#     nohup echo $(echo "Yes!$SESSION_ID!$REPORT_MODE!$FUNC!$STRATEGY!$DAY_ID" | sed "s#!#\n#g" | sh "$DRAFT_FILE" > "$TRASH" 2>&1) > "$TRASH" 2>&1 &!
#     if [ "$i" != 5 ]; then
#         sleep "$SLEEP_TIME"
#     fi
# done

# # # # # # #
#   Other   #
# # # # # # #

FUNC='print_market_trend'
REPORT_MODE='Record'
# REPORT_MODE='Print'

# STRATEGY='Solomon'
# DAY_ID='May_2021'
# DAY_ID='May_2022'
# PAIR='BTC/USDT'
# PAIR="$1"

nohup echo $(echo "No!$REPORT_MODE!$FUNC" | sed 's#!#\n#g' | sh "$DRAFT_FILE" > "$TRASH" 2>&1) > "$TRASH" 2>&1 &!
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!$DAY_ID!$PAIR" | sed "s#!#\n#g" | sh "$DRAFT_FILE" > "$TRASH" 2>&1) > "$TRASH" 2>&1 &!
# echo "No!$REPORT_MODE!$FUNC!$STRATEGY!$DAY_ID!$PAIR" | sed "s#!#\n#g" | sh "$DRAFT_FILE"
