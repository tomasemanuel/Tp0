import socket
import logging
import signal
from common.utils import process_message


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

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._is_running:
            try:
                client_socket = self.__accept_new_connection()
                if client_socket:
                    self.client_socket = client_socket
                    self.__handle_client_connection()
            except OSError as e:
                if client_socket is None:
                    logging.error(f"action: run | result: client disconnected")
                    break
                else:
                    logging.error(f"action: run | result: fail | error: {e}")
                    self.__close_client_connection()
                    break

    def __receive_message_length(self):
        try:
            msg_len = int.from_bytes(
                self.__safe_receive(MAX_MSG_SIZE), byteorder='little')

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
                msg_length = self.__receive_message_length()
                if msg_length == 0:
                    return
                msg = self.__safe_receive(msg_length).strip()

                try:
                    process_message(msg, addr)
                    self.__send_success_message()
                except Exception:
                    self.__send_error_message()

        except OSError as e:
            self.__send_error_message()
            # logging.error(
            #     f"action: receive_message | result: fail | error: {e}")
        finally:
            self.__close_client_connection()

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
                    'action: close client connection | result: success')

                self.client_socket = None  # <- Esto es importante
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

        while total_sent < len(message):
            n = self.client_socket.send(bytes_to_send[total_sent:])
            total_sent += n
        return

    def __safe_receive(self, buf_len):

        msg = 0
        buffer = bytes()
        while msg < buf_len:
            message = self.client_socket.recv(buf_len)
            buffer += message
            msg += len(message)

        return buffer
