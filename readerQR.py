import os
import io
import numpy as np
from PIL import Image
from pyzxing import BarCodeReader
import urllib.request
from typing import Union


def read_image(path):
    with open(path, "rb") as f:
        return bytearray(f.read())


def read_qr_by_pyzxing(img: Union[bytearray, str]):
    reader = BarCodeReader()
    if img is bytearray:
        np_array = np.array(Image.open(io.BytesIO(img)))
        results = reader.decode_array(np_array)
    elif img is str:
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
    text1, got1 = read_qr_by_pyzxing(byteimg)
    text2, got2 = read_qr_by_pyzxing(uniq_id + ".jpg")
    delete_photo(uniq_id)
    if got1:
        return text1, True
    if got2:
        return text2, True
    return '', False
