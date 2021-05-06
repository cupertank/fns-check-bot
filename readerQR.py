import os
import io
from pyzbar.pyzbar import decode
from PIL import Image


def readimage(path):
    count = os.stat(path).st_size / 2
    with open(path, "rb") as f:
        return bytearray(f.read())


def readQR(img: bytearray) -> (str, bool):
    decoded = decode(Image.open(io.BytesIO(img)))
    decoded = [code for code in decoded if code.type == 'QRCODE']
    if len(decoded) != 1:
        return '', False
    text = decoded[0].data.decode("utf-8")
    # text = text[2:-1]
    return text, True