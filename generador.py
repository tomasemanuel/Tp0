import sys
import yaml


import yaml


def create_clients(file_path, clients):
    # Estructura base del compose
    data = {
        'name': 'tp0',
        'services': {},
        'networks': {
            'testing_net': {
                'ipam': {
                    'driver': 'default',
                    'config': [
                        {'subnet': '172.25.125.0/24'}
                    ]
                }
            }
        }
    }
    cli_length = f'CLIENTS_LENGTH={clients}'

    # Agregar servidor
    data['services']['server'] = {
        'container_name': 'server',
        'image': 'server:latest',
        'entrypoint': 'python3 /main.py',
        'environment': [
            'PYTHONUNBUFFERED=1',
            'LOGGING_LEVEL=DEBUG',
            cli_length
        ],
        'networks': ['testing_net'],
        'volumes': ['./server/config.ini:/config.ini']
    }

    # Agregar clientes
    for i in range(1, clients + 1):
        data['services'][f'client{i}'] = {
            'container_name': f'client{i}',
            'image': 'client:latest',
            'entrypoint': '/client',
            'environment': [
                f'CLI_ID={i}',
            ],
            'networks': ['testing_net'],
            'depends_on': ['server'],
            'volumes': [
                './client/config.yaml:/config.yaml',
                './.data:/.data'
            ]

        }

    # Escribir archivo compose sobrescribiendo lo que había
    with open(file_path, 'w') as docker_compose:
        yaml.dump(data, docker_compose, default_flow_style=False)


if __name__ == '__main__':
    file = sys.argv[1]
    clients = int(sys.argv[2])

    create_clients(file, clients)
