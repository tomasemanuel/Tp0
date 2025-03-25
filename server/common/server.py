import socket
import logging
import signal
import os
from multiprocessing import Process, Lock
from common.client_handler import create_client_handler

MAX_MSG_SIZE = 4


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.client_socket = None
        self._is_running = True
        self.done_agencies = {}
        self.number_of_clients = int(os.getenv('CLIENTS_LENGTH', 0))
        self.file_lock = Lock()
        self.agency_lock = Lock()
        self.processes = []

    def run(self):
        while self._is_running:
            try:
                if len(self.done_agencies.keys()) == self.number_of_clients:
                    logging.info("action: all_clients_done | result: success")

                    break

                client_socket = self.__accept_new_connection()
                if client_socket is None or not self._is_running:
                    break

                process = Process(
                    target=create_client_handler,
                    args=(client_socket, self.file_lock, self.agency_lock, self.done_agencies,
                          self.number_of_clients)
                )
                self.processes.append(process)
                process.start()

            except OSError as e:
                logging.error(f"action: run | result: fail | error: {e}")
                break
            except Exception as e:
                logging.error(f"action: run | result: fail | error: {e}")
                break

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        # logging.info('action: accept_connections | result: in_progress')
        if not self._is_running or self._server_socket.fileno() == -1:
            return None
        try:
            c, addr = self._server_socket.accept()
            # logging.info(
            # f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError as e:
            # logging.info(
            # f'action: accept_connections | result: fail | error: {e}')
            return None

    def stop(self):
        if self.client_socket is not None:
            self.__close_client_connection()
        if self.socket:
            self.socket.close()
            self.socket = None
        for process in self.processes:
            if process.is_alive():
                process.join()
                # process.terminate()
        logging.info("action: exit | result: success")
