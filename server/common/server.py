import socket
import logging
import signal
import os
from common.utils import load_bets, has_won
from common.client_handler import ClientHandler


class Server:
    def __init__(self, port, listen_backlog):
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.client_socket = None
        self._is_running = True
        self.done_agencies = {}
        self.number_of_clients = int(os.getenv('CLIENTS_LENGTH', 0))

    def run(self):
        while self._is_running:
            try:
                if len(self.done_agencies.keys()) == self.number_of_clients:
                    self.lotery()
                    break

                self.client_socket = self.__accept_new_connection()
                if self.client_socket is None or not self._is_running:
                    break

                handler = ClientHandler(self.client_socket, self.done_agencies)
                handler.handle()

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

    def lotery(self):
        winners_by_agency = {}

        for bet in load_bets():
            if has_won(bet):
                if bet.agency not in winners_by_agency:
                    winners_by_agency[bet.agency] = 0
                winners_by_agency[bet.agency] += 1

        for agency_id, client_socket in self.done_agencies.items():
            winners = winners_by_agency.get(agency_id, 0)
            response = f"OK:{winners}".ljust(8)

            try:
                bytes_to_send = response.encode('utf-8')
                client_socket.sendall(bytes_to_send)
                logging.info(
                    f"action: sorteo | result: success | agency: {agency_id} | winners: {winners}")
            except Exception as e:
                logging.error(
                    f"action: sorteo | result: fail | agency: {agency_id} | error: {e}")

        logging.info("action: sorteo | result: success")

    def __accept_new_connection(self):
        if not self._is_running or self._server_socket.fileno() == -1:
            return None
        try:
            client_socket, addr = self._server_socket.accept()
            return client_socket
        except OSError as e:
            return None

    def __close_client_connection(self):
        try:
            if self.client_socket:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except OSError as e:
                    if e.errno in (107, 9):  # Already closed or bad fd
                        logging.warning(
                            f"action: close_client_connection | result: already closed | warning: {e}")
                    else:
                        raise e
        except OSError as e:
            logging.error(
                f"action: close_client_connection | result: fail | error: {e}")
        finally:
            if self.client_socket:
                logging.info("action: exit | result: success")
                self.client_socket = None

    def stop(self):
        if self.client_socket is not None:
            self.__close_client_connection()
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None
        logging.info("action: exit | result: success")
