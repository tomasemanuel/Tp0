import socket
import logging
import signal
from common.utils import load_bets, process_message, store_bets, has_won


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
                msg_length = self.receive_message_length()
                if msg_length == 0:
                    break
                msg = self.safe_receive(msg_length).strip()
                if not msg:
                    break

                try:
                    agencyID = process_message(
                        msg, addr, self.file_lock, self.agency_lock)
                    if agencyID:
                        logging.info(
                            f"action: done_received | result: success | ip: {addr[0]} from agency: {agencyID}")
                        with self.agency_lock:
                            self.done_agencies[agencyID] = self.client_socket
                            logging.info(
                                f"action: done agencies | result: success | len: {len(self.done_agencies.keys())} and {self.number_of_clients} and {self.done_agencies.keys()}")
                            if len(self.done_agencies.keys()) == self.number_of_clients:
                                logging.info(
                                    "action: all_clients_done | result: success")
                                run_lottery(self.done_agencies)
                            break

                    self.__send_success_message()
                except Exception as e:
                    logging.error(
                        f"action: handle_client_connection | result: fail | error: {e}")
                    self.__send_error_message()
            logging.info(f"action: handle_client_connection | result: success")
        except OSError as e:
            self.__send_error_message()

    def receive_message_length(self):
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

    def close_client_connection(self):
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

    def safe_receive(self, buf_len):
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


def run_lottery(done_agencies):
    winners_by_agency = {}

    for bet in load_bets():
        if has_won(bet):
            if bet.agency not in winners_by_agency:
                winners_by_agency[bet.agency] = 0
            winners_by_agency[bet.agency] += 1
    logging.info(
        f"action: sorteo | result: success | winners_by_agency: {winners_by_agency}")
    for agency_id, client_socket in done_agencies.items():
        winners = winners_by_agency.get(agency_id, 0)
        response = f"OK:{winners}".ljust(8)
        try:
            client_socket.sendall(response.encode('utf-8'))
            logging.info(
                f"action: sorteo | result: success | agency: {agency_id} | winners: {winners}")
        except Exception as e:
            logging.error(
                f"action: sorteo | result: fail | agency: {agency_id} | error: {e}")
            return
        try:
            client_handler = ClientHandler(
                client_socket, None, None, None, None)
            msg_length = client_handler.receive_message_length()
            if msg_length == 0:
                return
            msg = client_handler.safe_receive(msg_length).strip()
            if msg == "exit":
                logging.info(
                    f"action: exit_received | result: success | agency: {agency_id}")
            else:
                logging.warning(
                    f"action: unexpected_msg_after_lottery | msg: {msg} | agency: {agency_id}")
        except Exception as e:
            logging.error(
                f"action: wait_exit_after_lottery | result: fail | agency: {agency_id} | error: {e}")

    logging.info("action: sorteo | result: success")


def create_client_handler(client_socket, file_lock, agency_lock, done_agencies, number_of_clients):
    handler = ClientHandler(client_socket, file_lock,
                            agency_lock, done_agencies, number_of_clients)
    handler.handle_client_connection()
