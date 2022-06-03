#!/bin/bash


export FLASK_APP=blade.py
export FLASK_ENV=development

mkdir -p labrys_test_net_temp

echo 'Setting up blade 1'
python3 setup.py labrys_test_net_temp/blade1 localhost:1337 'acid_burn' "the baddest hacker in nyc. will kick your ass at wipeout. she/her" password
cp burn_avatar.jpg labrys_test_net_temp/blade1/identity/avatar.jpg
DATA_DIR=labrys_test_net_temp/blade1 flask run --port 1337 &
PID1=$!

echo 'Setting up blade 2'
python3 setup.py labrys_test_net_temp/blade2 localhost:1338 'crash_override' "used to be zero_cool. mess the best, die like the rest. he/him" password
cp crash_avatar.jpg labrys_test_net_temp/blade2/identity/avatar.jpg
DATA_DIR=labrys_test_net_temp/blade2 flask run --port 1338 &
PID2=$!

echo 'Setting up blade 3'
python3 setup.py labrys_test_net_temp/blade3 localhost:1339 'lord_nikon' "hacker, dj, gender is a colonialist construct. they/them" password
cp nikon_avatar.jpg labrys_test_net_temp/blade3/identity/avatar.jpg
DATA_DIR=labrys_test_net_temp/blade3 flask run --port 1339&
PID3=$!

trapit() {
  kill $PID1 $PID2 $PID3
  rm -r labrys_test_net_temp
}

trap trapit EXIT

sleep 3600h
