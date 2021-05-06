import requests

from .exceptions import *
from .receipt import Receipt

__HOST = 'irkkt-mobile.nalog.ru:8888'
__DEVICE_OS = 'iOS'
__CLIENT_VERSION = '2.9.0'
__DEVICE_ID = '7C82010F-16CC-446B-8F66-FC4080C66521'
__ACCEPT = '*/*'
__USER_AGENT = 'billchecker/2.9.0 (iPhone; iOS 13.6; Scale/2.00)'
__ACCEPT_LANGUAGE = 'ru-RU;q=1, en-US;q=0.9'
__CLIENT_SECRET = "IyvrAbKt9h/8p6a7QPh8gpkXYQ4="

__HEADERS = {
    'Host': __HOST,
    'Accept': __ACCEPT,
    'Device-OS': __DEVICE_OS,
    'Device-Id': __DEVICE_ID,
    'clientVersion': __CLIENT_VERSION,
    'Accept-Language': __ACCEPT_LANGUAGE,
    'User-Agent': __USER_AGENT,
}


def send_login_sms(number: str):
    url = f'https://{__HOST}/v2/auth/phone/request'
    payload = {
        'client_secret': __CLIENT_SECRET,
        'phone': number
    }
    resp = requests.post(url, headers=__HEADERS, json=payload)
    if resp.status_code != 200:
        raise InvalidPhoneException()


def send_login_code(number: str, code: str):
    url = f'https://{__HOST}/v2/auth/phone/verify'
    payload = {
        'client_secret': __CLIENT_SECRET,
        'phone': number,
        'code': code
    }
    resp = requests.post(url, headers=__HEADERS, json=payload)
    if resp.status_code != 200:
        raise InvalidSmsCodeException()
    resp_json = resp.json()
    return resp_json["sessionId"], resp_json["refresh_token"]


def __get_ticket_id(qr: str, session_id: str) -> str:
    url = f'https://{__HOST}/v2/ticket'
    headers = __HEADERS.copy()
    headers["sessionId"] = session_id
    payload = {'qr': qr}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        raise InvalidTicketIdException()
    resp_json = resp.json()
    return resp_json["id"]


def __get_ticket(qr: str, session_id: str) -> dict:
    headers = __HEADERS.copy()
    headers["sessionId"] = session_id
    ticket_id = __get_ticket_id(qr, session_id)
    url = f'https://{__HOST}/v2/tickets/{ticket_id}'
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise InvalidTicketIdException()
    ticket_dict = resp.json()
    if "status" not in ticket_dict or ticket_dict["status"] != 2:
        raise InvalidTicketIdException()
    return ticket_dict


def get_receipt(qr: str, session_id: str) -> Receipt:
    ticket_dict = __get_ticket(qr, session_id)
    try:
        receipt_dict = ticket_dict["ticket"]["document"]["receipt"]
        ticket: Receipt = Receipt.from_dict(receipt_dict)
        return ticket
    except KeyError:  # TODO check if nothing else can be thrown
        raise InvalidTicketIdException


def refresh_session(refresh_token: str) -> str:
    url = f'https://{__HOST}/v2/mobile/users/refresh'
    headers = __HEADERS.copy()
    payload = {
        "client_secret": __CLIENT_SECRET,
        "refresh_token": refresh_token
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        raise InvalidSessionIdException()
    resp_json = resp.json()
    return resp_json["sessionId"]
