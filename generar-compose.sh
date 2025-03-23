#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Error: Must enter 2 arguments"
    exit 1
fi

FILE_NAME=$1
CLIENTS=$2

# Verifico que el numero sea correcto (solo enteros)
if ! [[ "$CLIENTS" =~ ^[0-9]+$ ]]; then
    echo "Error: Client number must be an integer"
    exit 1
fi

# Invoco un subscript de python para modificar el archivo de docker-compose.yaml
python3 generador.py "$FILE_NAME" "$CLIENTS"

echo "Docker compose updated with $CLIENTS clients"