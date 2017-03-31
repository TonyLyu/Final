import cv2
import numpy as np
import math
import copy
def produceThresholds(crop_img):
    crop = copy.deepcopy(crop_img)
    thresholds = []
    threshold0 = Wolf(crop, 3, 18, 18, 0.05 + (0 * 0.35), 128)
    threshold0 = cv2.bitwise_not(threshold0)
    thresholds.append(threshold0)
    threshold1 = Wolf(crop, 3, 22, 22, 0.05 + (1 * 0.35), 128)
    threshold1 = cv2.bitwise_not(threshold1)
    thresholds.append(threshold1)
    threshold2 = Wolf(crop, 2, 12, 12, 0.18, 128)
    threshold2 = cv2.bitwise_not(threshold2)
    thresholds.append(threshold2)

    return thresholds


def calcLocalStats(im, map_m, map_s, winx, winy):
    rows, cols = im.shape
    im_sum, im_sum_sq = cv2.integral2(im, sqdepth=cv2.CV_64F)
    wxh = winx/2
    wyh = winy/2
    x_firstth = wxh
    y_lastth = rows - wyh - 1
    y_firstth = wyh
    winarea = float(winx * winy)

    max_s = 0
    j = y_firstth
    for j in range(y_firstth, y_lastth+1):
        sum = 0.0
        sum_sq = 0.0
        sum = im_sum.item(j-wyh+winy, winx) - im_sum.item(j-wyh, winx) - im_sum.item(j-wyh+winy, 0) + im_sum.item(j-wyh, 0)
        sum_sq = im_sum_sq.item(j-wyh+winy, winx) - im_sum_sq.item(j-wyh, winx) - im_sum_sq.item(j-wyh+winy, 0) + im_sum_sq.item(j-wyh, 0)
        m = sum / winarea
        s = math.sqrt((sum_sq - m * sum) / winarea)
        if s > max_s:
            max_s = s
        map_m.itemset((j, x_firstth), m)
        map_s.itemset((j, x_firstth), s)
        maxrange = cols - winx + 1
        for i in range(1, maxrange):
            sum -= im_sum.item(j-wyh+winy, i) - im_sum.item(j-wyh, i) - im_sum.item(j-wyh+winy, i-1) \
                   + im_sum.item(j-wyh, i-1)
            sum += im_sum.item(j - wyh + winy, i + winx) - im_sum.item(j - wyh, i + winx) - im_sum.item(j - wyh + winy, i + winx - 1) + im_sum.item(j - wyh, i + winx - 1)

            sum_sq -= im_sum_sq.item(j - wyh + winy, i) - im_sum_sq.item(j - wyh, i) - im_sum_sq.item(j - wyh + winy, i - 1) + im_sum_sq.item(j-wyh, i-1)
            sum_sq += im_sum_sq.item(j - wyh + winy, i + winx) - im_sum_sq.item(j - wyh, i + winx) - im_sum_sq.item(j - wyh + winy, i + winx - 1) + im_sum_sq.item(j - wyh, i + winx - 1)
            m = sum / winarea
            s = math.sqrt(abs(sum_sq - m*sum) / winarea)
            if s > max_s:
                max_s = s
            map_m.itemset((j, i+wxh), m)
            map_s.itemset((j, i+wxh), s)
    return max_s, map_m, map_s, im

def Wolf(image, version, winx, winy, k, dR):
    img = copy.deepcopy(image)
    m = 0.0
    max_s = 0.0
    th = 0
    wxh = winx / 2
    wyh = winy / 2
    x_firstth = wxh
    x_lastth = img.shape[1] - wxh - 1
    y_lastth = img.shape[0] - wyh - 1
    y_firstth = wyh

    rows, cols = img.shape[:2]
    #output = np.zeros((rows, cols), np.uint8)
    output = np.uint8(img)
    # print img.dtype
    # print rows, cols
    map_m = np.zeros((rows, cols), dtype=float)
    map_s = np.zeros((rows, cols), dtype=float)
    max_s, map_m, map_s, img = calcLocalStats(img, map_m, map_s, winx, winy)
    #Finds the global minimum and maximum in an array
    min_I, max_I, _, _ = cv2.minMaxLoc(img)
    #
    # for i in range(0, map_s.shape[0]):
    #     for j in range(0, map_s.shape[1]):
    #         print map_s.item(i, j)
    # map_s = np.uint8(map_s)
    # cv2.imshow('12', map_s)
    thsurf = np.zeros((rows, cols), dtype=float)
    for j in range(y_firstth, y_lastth+1):
        for i in range(0, cols - winx + 1):
            m = float(map_m.item(j, i+wxh))
            s = float(map_s.item(j, i+wxh))
            if version == 1:
                th = m + k*s
            elif version == 2:
                th = m * (1 + k*(s / dR - 1))
            else:
                th = m + k * (s / max_s - 1) * (m-min_I)
            thsurf.itemset((j, i+wxh), th)
            if i == 0:
                for l in range(0, x_firstth+1):
                    thsurf.itemset((j, l), th)
                if j == y_firstth:
                    for u in range(0, y_firstth):
                        for t in range(0, x_firstth+1):
                            thsurf.itemset((u, t), th)
                if j == y_lastth:
                    for u in range(y_lastth+1, rows):
                        for l in range(0, x_firstth+1):
                            thsurf.itemset((u, l), th)


            if j == y_firstth:
                for u in range(0, y_firstth):
                    thsurf.itemset((u, i+wxh), th)
            if j == y_lastth:
                for u in range(y_lastth+1, rows):
                    thsurf.itemset((u, i+wxh), th)
        #right border
        for i in range(x_lastth, cols):
            thsurf.itemset((j, i), th)
        #right-upper corner
        if j == y_firstth:
            for u in range(0, y_firstth):
                for l in range(x_lastth, cols):
                    thsurf.itemset((u, l), th)
        #right-lower corner
        if j == y_lastth:
            for u in range(y_lastth+1, rows):
                for l in range(x_lastth, cols):
                    thsurf.itemset((u, l), th)
    for y in range(0, rows):
        for x in range(0, cols):
            if img.item(y, x) >= thsurf.item(y, x):
                output.itemset((y, x), 255)
            else:
                output.itemset((y, x), 0)
    return output

def otsu(img):
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return th3