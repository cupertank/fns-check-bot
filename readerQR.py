import os
import io
import numpy as np
from PIL import Image
from pyzxing import BarCodeReader
import urllib.request
from typing import Union
import cv2
from pyzbar.pyzbar import decode


def read_image(path):
    with open(path, "rb") as f:
        return bytearray(f.read())


def read_qr_by_pyzbar(uniq_id) -> (str, bool):
    img = cv2.imread(uniq_id)
    decoded = decode(img)
    decoded = [code for code in decoded if code.type == 'QRCODE']
    if len(decoded) != 1:
        return '', False
    text = decoded[0].data.decode("utf-8")
    return text, True


def read_qr_by_pyzxing(img: Union[bytearray, str]):
    reader = BarCodeReader()
    if type(img) is bytearray:
        np_array = np.array(Image.open(io.BytesIO(img)))
        results = reader.decode_array(np_array)
    elif type(img) is str:
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


def download_photo(url, uniq_id):
    img = urllib.request.urlopen(url).read()
    out = open(uniq_id + ".jpg", "wb")
    out.write(img)
    out.close()


def delete_photo(uniq_id):
    os.remove(uniq_id + ".jpg")


def main_qr_reader(url, uniq_id, byteimg: bytearray):
    download_photo(url, uniq_id)

    text, got = read_qr_by_pyzbar(uniq_id + ".jpg")
    if got:
        delete_photo(uniq_id)
        return text, True

    text, got = read_qr_by_pyzxing(byteimg)
    if got:
        delete_photo(uniq_id)
        return text, True

    text, got = read_qr_by_pyzxing(uniq_id + ".jpg")
    if got:
        delete_photo(uniq_id)
        return text, True

    return '', False
