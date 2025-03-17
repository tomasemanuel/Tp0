#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <archivo_salida> <cantidad_clientes>"
    exit 1
fi

OUTPUT_FILE=$1
NUM_CLIENTS=$2

cat > "$OUTPUT_FILE" <<EOL
version: "3.8"

services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
EOL

for i in $(seq 1 "$NUM_CLIENTS"); do
    cat >> "$OUTPUT_FILE" <<EOL

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server
EOL
done

cat >> "$OUTPUT_FILE" <<EOL

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOL

echo "Archivo $OUTPUT_FILE generado correctamente con $NUM_CLIENTS clientes."
