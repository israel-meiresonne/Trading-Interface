#!/bin/bash

DRAFT_FILE='sh/start_draft.sh'
FUNC='backtest2'
STRATEGY='Solomon'
DAY_ID='January_2021_January_2023'

REPORT_MODE='Record'
# REPORT_MODE='Print'

# COCOS_USDT
# CTXC_USDT
# DOGE_USDT
# GTO_USDT
# MITH_USDT

# PAIR='COCOS/USDT'
# PAIRS[1]='COCOS/USDT'
# PAIRS[2]='CTXC/USDT'
# PAIRS[3]='DOGE/USDT'
# PAIRS[4]='GTO/USDT'
# PAIRS[5]='MITH/USDT'
# SESSION_ID=$(date -u '+%Y-%m-%d_%H.%M.%S_Solomon-v1.1.3')
# SESSION_ID='2023-01-07_23.41.49_Solomon-v1.1.3'

SLEEP_TIME=7

# echo 'No!Record!backtest2!Solomon!13_14_February_2021!BTC/USDT' | sed 's#!#\n#g' | sh "$DRAFT_FILE"

# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!13_14_February_2021!$PAIR" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# # sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!21_May_2021!$PAIR" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!February_2021!$PAIR" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!June_2021!$PAIR" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!January_2021_January_2022!$PAIR" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!


# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!January_2021_January_2022!$PAIR_0" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!January_2021_January_2022!$PAIR_1" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!January_2021_January_2022!$PAIR_2" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!January_2021_January_2022!$PAIR_3" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!
# sleep "$SLEEP_TIME"
# nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!January_2021_January_2022!$PAIR_4" | sed 's#!#\n#g' | sh "$DRAFT_FILE" 2>&1) &!

# for i in {1..5} ; do
#     echo "$(date -u '+%Y-%m-%d_%H.%M.%S') >> $i"
#     nohup echo $(echo "No!$REPORT_MODE!$FUNC!$STRATEGY!$DAY_ID!${PAIRS[i]}" | sed "s#!#\n#g" | sh "$DRAFT_FILE" 2>&1) &!
#     if [ "$i" != 5 ]; then
#         sleep "$SLEEP_TIME"
#     fi
# done

# for i in {1..5} ; do
#     echo "$(date -u '+%Y-%m-%d_%H.%M.%S') >> $i"
#     # nohup echo $(echo "Yes!$SESSION_ID!$REPORT_MODE!$FUNC!$STRATEGY!$DAY_ID" | sed "s#!#\n#g" | sh "$DRAFT_FILE" 2>&1) &!
#     if [ "$i" != 5 ]; then
#         sleep "$SLEEP_TIME"
#     fi
# done

FUNC='download_market_histories'
REPORT_MODE='Record'
nohup echo $(echo "No!$REPORT_MODE!$FUNC" | sed 's#!#\n#g' | sh "$DRAFT_FILE") &!
