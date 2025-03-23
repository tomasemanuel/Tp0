import datetime
BET_MSG_SEPARATOR = "|"


class Bet:
    def __init__(self, bet_agency: str, name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        bet agency must be passed as int
        birthdate fmt: YYYY-MM-DD
        number must be passed ad int
        """
        self.agency = int(bet_agency)
        self.first_name = name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)

    @staticmethod
    def deserialize(msg: bytes):
        """
        Deserialize a message into a Bet object
        """
        message = msg.decode('utf-8')
        bet_agency, name, last_name, document, birthdate, number = message.split(
            BET_MSG_SEPARATOR)

        return Bet(bet_agency, name, last_name, document, birthdate, number)
