import io
import os
import urllib.request
from typing import Union

import cv2
import numpy as np
from PIL import Image
from pyzxing import BarCodeReader

from complexQrReader import read_qr_complex_pyzxing
from pyzbar.pyzbar import decode

from main import cache_dir


def read_image(path):
    with open(path, "rb") as f:
        return bytearray(f.read())


def read_qr_by_pyzbar(path) -> (str, bool):
    img = cv2.imread(path)
    decoded = decode(img)
    decoded = [code for code in decoded if code.type == 'QRCODE']
    if len(decoded) != 1:
        return '', False
    text = decoded[0].data.decode("utf-8")
    return text, True


def read_qr_by_pyzxing(img: Union[bytearray, str]):
    reader = BarCodeReader()
    if isinstance(img, bytearray):
        np_array = np.array(Image.open(io.BytesIO(img)))
        results = reader.decode_array(np_array)
    elif isinstance(img, str):
        results = reader.decode(img)
    else:
        return "", False

    try:
        results = [code for code in results if code['format'].decode("utf-8") == 'QR_CODE']
    except:
        return "", False
    if len(results) == 0:
        return '', False
    text = results[0]['raw'].decode("utf-8")
    return text, True


def download_photo(url, uniq_id) -> str:
    img = urllib.request.urlopen(url).read()
    path = f"{cache_dir}/{uniq_id}.jpg"
    with open(path, "wb") as file:
        file.write(img)

    return path


def delete_photo(uniq_id):
    os.remove(f"{cache_dir}/{uniq_id}.jpg")


def main_qr_reader(url, uniq_id):
    path = download_photo(url, uniq_id)

    text, got = read_qr_by_pyzbar(path)
    if got:
        delete_photo(uniq_id)
        return text, True

    text, got = read_qr_by_pyzxing(path)
    if got:
        delete_photo(uniq_id)
        return text, True

    text, got = read_qr_complex_pyzxing(path)
    if got:
        delete_photo(uniq_id)
        return text, True

    return '', False
