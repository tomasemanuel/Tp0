import csv
import datetime
import time
import logging

from common.bet import Bet

""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574

""" Checks whether a bet won the prize or not. """


def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER


"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""


def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])


"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""


def load_bets() -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])


def process_message(msg: bytes, addr):
    """
    Process a batch message from a client.
    Each line represents one bet.
    """

    logging.info("action: process_message | result: in_progress")

    decoded = msg.decode("utf-8").strip()
    if decoded.startswith("done:"):
        logging.info(
            f"action: done_received | result: success | ip: {addr[0]}")
        agency_id = int(decoded.split(":")[1])
        return agency_id

    else:
        lines = decoded.split("\n")
        bets = []
        for line in lines:
            bet = Bet.deserialize(line.encode("utf-8"))
            bets.append(bet)
        store_bets(bets)
        logging.info(
            f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")
