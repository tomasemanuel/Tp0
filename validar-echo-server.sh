#!/bin/bash


PORT=12345
MESSAGE= "Hello world!"
TIMEOUT=5
SERVER_CONTAINER="server"

RESPONSE=$(docker run --rm --network tpo_testing_net alpine:latest sh -c "echo $MESSAGE | nC -W $TIMEOUT $SERVER_CONTAINER $PORT")

if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
