from math import floor, ceil
from typing import Union

import cv2
import numpy as np
import pyzxing
from PIL import Image
from cv2.cv2 import QRCodeDetector


def automatic_brightness_and_contrast(image: np.ndarray, clip_hist_percent: int = 25):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate grayscale histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_size = len(hist)

    # Calculate cumulative distribution from the histogram
    accumulator = [float(hist[0])]
    for index in range(1, hist_size):
        accumulator.append(accumulator[index - 1] + float(hist[index]))

    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= (maximum / 100.0)
    clip_hist_percent /= 2.0

    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1

    # Locate right cut
    maximum_gray = hist_size - 1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1

    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha

    '''
    # Calculate new histogram with desired range and show histogram 
    new_hist = cv2.calcHist([gray],[0],None,[256],[minimum_gray,maximum_gray])
    plt.plot(hist)
    plt.plot(new_hist)
    plt.xlim([0,256])
    plt.show()
    '''

    auto_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return auto_result, alpha, beta


def read_qr_complex_pyzxing(pil_image: Union[Image.Image, str]) -> (str, bool):
    # convert to PIL image if filename
    if isinstance(pil_image, str):
        pil_image = Image.open(pil_image)

    clip_hist_percents = [0, 10, 30, 60]
    denoise_levels = [0, 10, 30, 60]
    qr_extra_border = 10

    # convert into a numpy array
    image = np.array(pil_image)
    # get quadrants
    found, quadrants = QRCodeDetector().detect(image)

    for clip_hist_percent in clip_hist_percents:
        # correct brightness and contrast
        contrasted, _, _ = automatic_brightness_and_contrast(image, clip_hist_percent)

        if found:
            quadrant = quadrants[0]
            # get bounding box
            minx = floor(min([x for x, y in quadrant]))
            maxx = ceil(max([x for x, y in quadrant]))
            miny = floor(min([y for x, y in quadrant]))
            maxy = ceil(max([y for x, y in quadrant]))
            # crop image by bounding box
            contrasted = contrasted[miny - qr_extra_border:maxy + qr_extra_border,
                         minx - qr_extra_border:maxx + qr_extra_border]

        for denoise_level in denoise_levels:
            # denoise
            denoised = cv2.fastNlMeansDenoising(contrasted, None, h=denoise_level)
            # convert into hard black and white
            gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
            _, denoised = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # inverse image (black <-> white)
            denoised = cv2.bitwise_not(denoised)
            # convert back to PIL
            img = Image.fromarray(denoised)
            # find QR
            reader = pyzxing.BarCodeReader()
            output = reader.decode_array(np.array(img))
            # if found
            if len(output) and 'parsed' in output[0]:
                quadrant = output[0]['parsed'].decode('utf-8')
                return quadrant, True
    # nothing found
    return '', False
