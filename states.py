from enum import Enum, auto


class States(Enum):
    WAITING_NEW_CHECK = auto()
    WAITING_PHONE = auto()
    WAITING_CODE = auto()
    WAITING_NAMES = auto()
    WAITING_TICKET = auto()
    TICKET_PICKS = auto()

