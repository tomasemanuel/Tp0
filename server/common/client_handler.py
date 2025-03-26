import socket
import logging
from common.utils import process_message

MAX_MSG_SIZE = 4


class ClientHandler:
    def __init__(self, client_socket, done_agencies):
        self.client_socket = client_socket
        self.done_agencies = done_agencies

    def handle(self):
        try:
            addr = self.client_socket.getpeername()
            while self.client_socket:
                msg_length = self._receive_message_length()
                if msg_length == 0:
                    break
                msg = self._safe_receive(msg_length).strip()
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
                    self._send_success_message()
                except Exception as e:
                    logging.error(
                        f"action: handle_client_connection | result: fail | error: {e}")
                    self._send_error_message()
            logging.info(f"action: handle_client_connection | result: success")
        except OSError:
            self._send_error_message()

    def _receive_message_length(self):
        try:
            receive = self.client_socket.recv(MAX_MSG_SIZE)
            if not receive:
                return 0
            msg_len = int.from_bytes(receive, byteorder='little')
            logging.info(
                f"action: receive_message_length | result: success | msg_len: {msg_len}")
            self._send_success_message()
            return msg_len
        except Exception as e:
            self._send_error_message()
            logging.error(
                f"action: receive_message_length | result: fail | error: {e}")
            return 0

    def _send_success_message(self):
        self._safe_send("ok ")
        logging.info("action: send_success_message | result: success")

    def _send_error_message(self):
        self._safe_send("err")
        logging.error("action: send_error_message | result: success")

    def _safe_send(self, message):
        total_sent = 0
        bytes_to_send = message.encode('utf-8')
        while total_sent < len(message):
            n = self.client_socket.send(bytes_to_send[total_sent:])
            total_sent += n

    def _safe_receive(self, buf_len):
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
