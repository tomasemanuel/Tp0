import sys
import yaml


def create_clients(file, clients):
    with open(file, 'r') as docker_compose:
        data = yaml.safe_load(docker_compose)

    for i in range(1, clients + 1):
        client = {
            f'client{i}': {
                'container_name': f'client{i}',
                'image': 'client:latest',
                'entrypoint': '/client',
                'environment': [
                    f'CLI_ID={i}',
                ],
                'networks': [
                    'testing_net'
                ],
                'depends_on': [
                    'server'
                ],
                'volumes': [
                    './client/config.yaml:/config.yaml'
                ]

            }
        }
        data['services'].update(client)

    with open(file, 'w') as docker_compose:
        yaml.safe_dump(data, docker_compose, default_flow_style=False)


if __name__ == '__main__':
    file = sys.argv[1]
    clients = int(sys.argv[2])

    if clients <= 0:
        print("Clients cannot be 0")
        sys.exit(1)

    create_clients(file, clients)
