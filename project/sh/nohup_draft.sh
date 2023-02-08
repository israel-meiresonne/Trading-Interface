#!/bin/bash

DRAFT_FILE='sh/start_draft.sh'
TRASH='/dev/null'
SLEEP_TIME=10

# # # # # # # # #
#   Backtest    #
# # # # # # # # #

# REPORT_MODE='Record'
# FUNC='backtest2'
# STRATEGY='Solomon'
# DAY_ID='January_2021_January_2023'
# PAIRS[1]='COCOS/USDT'
# PAIRS[2]='CTXC/USDT'
# PAIRS[3]='DOGE/USDT'
# PAIRS[4]='GTO/USDT'
# PAIRS[5]='MITH/USDT'

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

# SESSION_ID='?'
# REPORT_MODE='Record'
# FUNC='loop_backtest2'
# STRATEGY='Solomon'
# DAY_ID='January_2021_January_2023'

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

# FUNC='download_market_histories'
# REPORT_MODE='Record'
# nohup echo $(echo "No!$REPORT_MODE!$FUNC" | sed 's#!#\n#g' | sh "$DRAFT_FILE") &!
