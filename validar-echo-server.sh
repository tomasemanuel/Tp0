#!/bin/bash

PORT=12345
MESSAGE="Hello world!"
TIMEOUT=5
SERVER_CONTAINER="server"
NETWORK="tp0_testing_net"

RESPONSE=$(docker run --rm --network "$NETWORK" alpine:latest sh -c "
  apk add --no-cache netcat-openbsd > /dev/null &&
  echo \"$MESSAGE\" | nc -w $TIMEOUT $SERVER_CONTAINER $PORT
")

# Mostrar respuesta obtenida para debug
echo "Response from container: '$RESPONSE'"

# Validación
if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
