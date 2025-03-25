import socket
import logging
import signal
from common.utils import decode_utf8, encode_string_utf8, load_bets, process_message, lotery


MAX_MSG_SIZE = 4
CONFIRMATION_MSG_LEN = 4
EXIT = "exit"
SUCCESS_MSG = "succ"
ERROR_MSG = "err"


class ClientHandler:
    def __init__(self, client_socket, file_lock, agency_lock, done_agencies, number_of_clients):
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())

        self.client_socket = client_socket
        self.file_lock = file_lock
        self.agency_lock = agency_lock
        self.done_agencies = done_agencies
        self.number_of_clients = number_of_clients
        self._is_running = True

    def handle_client_connection(self):
        try:
            addr = self.client_socket.getpeername()
            while self.client_socket:
                msg_length = self.__receive_message_length()
                if msg_length == 0:
                    break
                msg = self.__safe_receive(msg_length).strip()
                if not msg:
                    break

                try:
                    agencyID = process_message(
                        msg, addr, self.file_lock, self.agency_lock)
                    if agencyID:
                        logging.info(
                            f"action: done_received | result: success | ip: {addr[0]}")
                        with self.lock:
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

    def __receive_message_length(self):
        try:
            receive = self.client_socket.recv(MAX_MSG_SIZE)
            if not receive:
                return 0
            msg_len = int.from_bytes(receive, byteorder='little')

            logging.info(
                f"action: receive_message_length | result: success | msg_len: {msg_len}")
            self.__send_success_message()
            return msg_len

        except Exception as e:
            self.__send_error_message()
            logging.error(
                f"action: receive_message_length | result: fail | error: {e}")
            return 0

    def __close_client_connection(self):
        try:
            if self.client_socket:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except OSError as e:
                    if e.errno in [107, 9]:  # Not connected or bad fd
                        logging.warning(
                            f'action: close_client_connection | result: already closed | warning: {e}')
                    else:
                        raise e
        except OSError as e:
            logging.error(
                f'action: close_client_connection | result: fail | error: {e}')
        finally:
            if self.client_socket:
                logging.info('action: exit | result: success')
                self.client_socket = None
            return

    def __send_success_message(self):
        self.__safe_send("ok ")
        logging.info("action: send_success_message | result: success")

    def __send_error_message(self):
        self.__safe_send("err")
        logging.error("action: send_error_message | result: success")

    def __safe_send(self, message):
        total_sent = 0
        bytes_to_send = message.encode('utf-8')
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


def create_client_handler(client_socket, lock, done_agencies, number_of_clients):
    handler = ClientHandler(client_socket, lock,
                            done_agencies, number_of_clients)
    handler.handle_client_connection()
