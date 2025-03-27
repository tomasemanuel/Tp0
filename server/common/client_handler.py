import socket
import logging
from common.utils import process_message, load_bets, has_won, get_winner_bets_by_agency, encode_string_utf8, decode_utf8
from multiprocessing import Lock, Manager
MAX_MSG_SIZE = 4
CONFIRMATION_MSG_LEN = 4
SUCCESS_MSG = "succ"
EXIT_MSG = "exit"
WAITING_MSG = "wait"


class ClientHandler:
    def __init__(self, client_socket, file_lock: Lock, done_agencies, number_of_clients):
        self.client_socket = client_socket
        self.file_lock = file_lock
        self.done_agencies = done_agencies
        self.number_of_clients = number_of_clients

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
                    agencyID = process_message(msg, addr, self.file_lock)
                    if agencyID:
                        logging.info(
                            f"action: done_received | result: success | ip: {addr[0]}")

                        self.done_agencies[agencyID] = True
                        if len(self.done_agencies) == self.number_of_clients:
                            self.lottery(agencyID)
                        else:
                            self.__send_and_wait_confirmation(
                                encode_string_utf8(WAITING_MSG))
                    if self.client_socket:
                        self._send_success_message()

                except Exception as e:
                    logging.error(
                        f"action: handle_client_connection | result: fail | error: {e}")
                    self._send_error_message()
            logging.info(f"action: handle_client_connection | result: success")

        except socket.timeout:
            self.__send_error_message()
            logging.error(
                "action: handle_client_connection !!! | result: fail | error: timeout")
        except OSError as e:
            self.__send_error_message()
            logging.error(
                f"action: receive_message | result: fail | error: {e}")

    def __send_and_wait_confirmation(self, msg: bytes):

        self._safe_send(len(msg).to_bytes(MAX_MSG_SIZE, "little"))
        if decode_utf8(self._safe_receive(CONFIRMATION_MSG_LEN)) != SUCCESS_MSG:
            raise socket.error("Client did not confirm message reception")
        self._safe_send(msg)
        if decode_utf8(self._safe_receive(CONFIRMATION_MSG_LEN)) != SUCCESS_MSG:
            raise socket.error("Client did not confirm message reception")
        logging.info(
            f"action: send_and_wait_confirmation | result: success | msg: {msg}")

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

    def __close_client_connection(self):
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        self.client_socket = None
        logging.info('action: close_client_connection | result: success')

    def _send_success_message(self):
        self._safe_send("ok ")
        logging.info("action: send_success_message | result: success")

    def _send_error_message(self):
        self._safe_send("err")
        logging.error("action: send_error_message | result: success")

    def _safe_send(self, message):
        if isinstance(message, str):
            message = message.encode('utf-8')
        total_sent = 0
        while total_sent < len(message):
            n = self.client_socket.send(message[total_sent:])
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

    def lottery(self, agency_id):
        winners_by_agency = {}
        with self.file_lock:
            bets = load_bets()
            winner_bets = get_winner_bets_by_agency(bets, agency_id)
            docs = map(lambda bet: bet.document, winner_bets)
            response = ",".join(docs)
            logging.info(
                f"action: lottery | result: success | winners: {response}")
            self.__send_and_wait_confirmation(encode_string_utf8(response))
            self.__close_client_connection()

        logging.info("action: sorteo | result: success")


def create_client_handler(client_socket, file_lock, done_agencies, number_of_clients):
    client_handler = ClientHandler(
        client_socket, file_lock, done_agencies, number_of_clients)
    client_handler.handle()
    logging.info("action: create_client_handler | result: success")
