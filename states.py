from enum import Enum


class States(Enum):
    WAITING_NEW_CHECK = 0
    WAITING_PHONE = 1
    WAITING_CODE = 2
    WAITING_NAMES = 3
    WAITING_TICKET = 4
    TICKET_PICKS = 5

