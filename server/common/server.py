import socket
import logging
import signal
from common.utils import process_message, load_bets, has_won
import os

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

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._is_running:
            try:
                logging.info(
                    f"action: run | result: in_progress len: {len(self.done_agencies.keys())} y {self.number_of_clients}")
                if len(self.done_agencies.keys()) == self.number_of_clients:
                    logging.info("action: lottery | result: in_progress")
                    self.lotery()
                    break
                self.client_socket = self.__accept_new_connection()
                if self.client_socket is None or not self._is_running:
                    break
                self.__handle_client_connection()

            except OSError as e:
                if client_socket is None:
                    logging.error(f"action: run | result: client disconnected")
                    break
                else:
                    logging.error(f"action: run | result: fail | error: {e}")
                    self.__close_client_connection()
                    break
            except Exception as e:
                logging.error(f"action: run | result: fail | error: {e}")
                # self.__close_client_connection()
                break

    def lotery(self):
        logging.info("action: sorteo | result: in_progress")

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
                # self.client_socket = client_socket
                # self.__close_client_connection()

            except Exception as e:
                logging.error(...)
            except Exception as e:
                logging.error(
                    f"action: sorteo | result: fail | agency: {agency_id} | error: {e}")

        logging.info(
            f"action: sorteo | result: success")

    def __receive_message_length(self):
        try:
            receive = self.client_socket.recv(MAX_MSG_SIZE)
            if not receive:
                return 0
            msg_len = int.from_bytes(
                receive, byteorder='little')

            logging.info(
                f"action: receive_message_length | result: success | msg_len: {msg_len}")
            self.__send_success_message()
            return msg_len

        except Exception as e:
            self.__send_error_message()
            logging.error(
                "action: receive_message_length | result: fail | error: {e}")
            return 0

    def __handle_client_connection(self):
        try:
            addr = self.client_socket.getpeername()
            while self.client_socket:
                # logging.info(
                #     f"action: handle_client_connection | result: in_progress | ip: {addr[0]}")
                msg_length = self.__receive_message_length()
                # logging.info(
                #     f"action: handle_client_connection | result: in_progress | ip: {addr[0]} | msg_length: {msg_length}")
                if msg_length == 0:
                    break
                msg = self.__safe_receive(msg_length).strip()
                if not msg:
                    break

                try:
                    agencyID = process_message(msg, addr)
                    if agencyID:
                        logging.info(
                            f"action: done_received | result: success | ip: {addr[0]}")
                        self.done_agencies[agencyID] = self.client_socket
                        logging.info(
                            f"action: done agencies | result: success | ip: {self.done_agencies}")
                        return
                    self.__send_success_message()
                except Exception as e:
                    logging.error(
                        f"action: handle_client_connection | result: fail | error: {e}")
                    self.__send_error_message()
            logging.info(f"action: handle_client_connection | result: success")
        except OSError as e:
            self.__send_error_message()

    def __close_client_connection(self):
        # logging.info('action: close_client_connection | result: in_progress')
        try:
            if self.client_socket:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except OSError as e:
                    if e.errno == 107:  # Transport endpoint is not connected
                        logging.warning(
                            f'action: close_client_connection | result: already closed | warning: {e}')
                    elif e.errno == 9:  # Bad file descriptor
                        logging.warning(
                            f'action: close_client_connection | result: already closed | warning: {e}')
                    else:
                        raise e  # Re-raise if it's an unexpected error
        except OSError as e:
            logging.error(
                f'action: close_client_connection | result: fail | error: {e}')
        finally:
            if self.client_socket:
                logging.info(
                    'action: exit | result: success')
                self.client_socket = None
            return

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
        logging.info("action: exit | result: success")

    def __send_success_message(self):
        self.__safe_send("ok ")
        logging.info("action: send_success_message | result: success")

    def __send_error_message(self):
        self.__safe_send("err")
        logging.error("action: send_error_message | result: success")

    def __safe_send(self, message):
        total_sent = 0
        bytes_to_send = message.encode('utf-8')
        logging.info(
            f"action: safe_send | result: in_progress | message: {message}")
        while total_sent < len(message):
            n = self.client_socket.send(bytes_to_send[total_sent:])
            total_sent += n
        return

    def __safe_receive(self, buf_len):

        msg = 0
        buffer = bytes()
        while msg < buf_len:
            try:
                message = self.client_socket.recv(buf_len)
                buffer += message
                msg += len(message)
            except OSError as e:
                logging.error(
                    f"action: safe_receive | result: fail | error: {e}")
                return None

        return buffer
