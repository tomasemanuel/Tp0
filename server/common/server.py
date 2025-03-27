import socket
import logging
import signal
import os
from common.utils import load_bets, has_won
from common.client_handler import create_client_handler
from multiprocessing import Lock, Process, Manager, Barrier
import time


class Server:
    def __init__(self, port, listen_backlog):
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.client_socket = None
        self._is_running = True
        self.file_lock = Lock()
        self.number_of_clients = int(os.getenv('CLIENTS_LENGTH', 0))
        self.manager = Manager()
        self.done_agencies = self.manager.dict()
        self.processes = []

    def run(self):
        while self._is_running:
            try:

                client_socket = self.__accept_new_connection()
                if client_socket is None or not self._is_running:
                    break
                process = Process(target=create_client_handler, args=(
                    client_socket, self.file_lock, self.done_agencies, self.number_of_clients))
                process.start()
                self.processes.append(process)
                time.sleep(0.1)
                logging.info("action: run | result: success")

            except OSError as e:
                if self.client_socket is None:
                    logging.error("action: run | result: client disconnected")
                    break
                else:
                    logging.error(f"action: run | result: fail | error: {e}")
                    self.__close_client_connection()
                    break
            except Exception as e:
                logging.error(f"action: run | result: fail | error: {e}")
                break

    def __accept_new_connection(self):
        if not self._is_running or self._server_socket.fileno() == -1:
            return None
        try:
            client_socket, addr = self._server_socket.accept()
            return client_socket
        except OSError as e:
            return None

    def stop(self):

        if self.client_socket is not None:
            self.__close_client_connection()
        for process in self.processes:
            process.join()
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
        logging.info("action: exit | result: success")
