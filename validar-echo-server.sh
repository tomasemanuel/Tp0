#!/bin/bash

docker build -f Dockerfile.netcat -t netcat-test .

RESPONSE=$(docker run --rm --network tp0_testing_net netcat-test)

echo "Response from container: '$RESPONSE'"

if [ "$RESPONSE" = "hello world" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
