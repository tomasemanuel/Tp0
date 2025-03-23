import socket
import logging
import signal
import json
from common.utils import store_bets, Bet


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        # Para saber el estado del servidor
        self._is_running = True

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        signal.signal(signal.SIGTERM, self.__signal_handler)

        while self._is_running:
            client_sock = self.__accept_new_connection()
            if client_sock:
                self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            if not client_sock:
                return

            # Short-read: leer hasta que el cliente cierre o llegue EOF
            data = b""
            while True:
                chunk = client_sock.recv(1024)
                if not chunk:
                    break
                data += chunk

            # Decodificar mensaje y parsear JSON
            msg = data.decode("utf-8").strip()
            addr = client_sock.getpeername()

            logging.info(
                f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')

            bet_data = json.loads(msg)
            bet = Bet(
                agency=bet_data["agencia"],
                first_name=bet_data["nombre"],
                last_name=bet_data["apellido"],
                document=bet_data["dni"],
                birthdate=bet_data["nacimiento"],
                number=bet_data["numero"]
            )

            # Guardar la apuesta
            store_bets([bet])

            # Log de éxito
            logging.info(
                f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')

            # Enviar respuesta al cliente
            client_sock.send(b"OK\n")

        except Exception as e:
            logging.error(
                f"action: handle_client_connection | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        if not self._is_running or self._server_socket.fileno() == -1:
            return None
        try:
            c, addr = self._server_socket.accept()
            logging.info(
                f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError as e:
            logging.info(
                f'action: accept_connections | result: fail | error: {e}')
            return None

    def __signal_handler(self, signal, frame):
        """
        Signal handler for SIGTERM signal

        When SIGTERM signal is received, the server stops accepting new
        connections and finishes the current ones
        """
        # logging.info("action: signal_handler SIGTERM| result: in_progress")
        self._is_running = False
        try:
            if self._server_socket:
                self._server_socket.close()
                logging.info(
                    f"action: exit | result: success | detail: server socket closed")
        except OSError as e:
            logging.error(f"action: exit | result: fail | error: {e}")
        logging.info(f"action: exit | result: success")
