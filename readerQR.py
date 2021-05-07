import os
import io
import numpy as np
import pyzbar.pyzbar
import pyzxing
from pyzbar.pyzbar import decode
from PIL import Image
import argparse
import cv2
from pyzxing import BarCodeReader
import urllib.request


# TOKEN = os.getenv("LOCAL_TOKEN")
def readimage(path):
    count = os.stat(path).st_size / 2
    with open(path, "rb") as f:
        return bytearray(f.read())


def readQR(uniq_id) -> (str, bool):
    # url = 'https://api.telegram.org/file/bot1539624754:AAFBaKfZylXlOuDRKbdLYcvIHj_hkWqaWkw/photos/file_7.jpg'  # Search the web for qrcode photos
    img = cv2.imread(uniq_id)
    decoded = decode(img)
    decoded = [code for code in decoded if code.type == 'QRCODE']
    if len(decoded) != 1:
        return '', False
    text = decoded[0].data.decode("utf-8")
    # text = text[2:-1]
    return text, True

def readQR2(byteimg: bytearray):
    reader = BarCodeReader()
    np_array = np.array(Image.open(io.BytesIO(byteimg)))
    results = reader.decode_array(np_array)
    try :
        results = [code for code in results if code['format'].decode("utf-8") == 'QR_CODE']
    except:
        return "", False
    print("it's 2")
    print(results)
    if len(results) == 0:
        return '', False
    text = results[0]['raw'].decode("utf-8")
    return text, True

def readQR3(uniq_id):
    reader = BarCodeReader()
    results = reader.decode(uniq_id)
    try :
        results = [code for code in results if code['format'].decode("utf-8") == 'QR_CODE']
    except:
        return "", False
    print("it's 3")
    print(results)
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

def twoQRreaders(url, uniq_id, byteimg: bytearray):
    download_photo(url, uniq_id)
    text1, got1 = readQR(uniq_id + ".jpg")
    text2, got2 = readQR2(byteimg)
    text3, got3 = readQR3(uniq_id + ".jpg")
    delete_photo(uniq_id)
    if got1:
        return text1, True
    if got2:
        return text2, True
    if got3:
        return text3, True
    return '', False

def main_test():
    img = cv2.imread('cut.jpg')
    decoded = decode(img)
    return
    # reader = BarCodeReader()
    # results = reader.decode('norm1.jpg')
    # Or file pattern for multiple files
    # results = reader.decode('/PATH/TO/FILES/*.png')
    # print(results)
    # Or a numpy array
    # Requires additional installation of opencv
    # pip install opencv-python
    # url = 'https://api.telegram.org/file/bot1539624754:AAFBaKfZylXlOuDRKbdLYcvIHj_hkWqaWkw/photos/file_7.jpg'  # Search the web for qrcode photos
    # img = Image.open(io.BytesIO(urllib.request.urlopen(url).read()))






if __name__ == "__main__":
    main_test()