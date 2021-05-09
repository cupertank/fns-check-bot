class InvalidPhoneException(Exception):
    pass


class InvalidSmsCodeException(Exception):
    pass


class InvalidQrCodeException(Exception):
    pass


class InvalidTicketIdException(Exception):
    pass


class InvalidSessionIdException(Exception):
    pass


class FNSConnectionError(Exception):
    pass

class TooManyRequests(Exception):
    pass
