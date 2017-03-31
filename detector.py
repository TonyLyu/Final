import cv2
from segment.rect import Rect
def find_plates(img, maxWidth, maxHeight):
    img = cv2.equalizeHist(img)
    plate_cascade = cv2.CascadeClassifier('us.xml')
    plate_image = plate_cascade.detectMultiScale(img,  scaleFactor=1.1, minNeighbors=3, flags=0, minSize=(70, 35),
                                                 maxSize=(maxWidth, maxHeight))
    return plate_image


def computeScaleFactor(width, height):
    scale_factor = float(1.0)
    if(width > 1280):
        scale_factor = float(1280)/width
    if(height > 728):
        scale_factor = float(768)/height
    return scale_factor


def expandRect(img, expandXPixels, expandYPixels, maxX, maxY):
    expandRegion = img
    halfX = round(float(expandXPixels) / 2.0)
    halfY = round(float(expandYPixels) / 2.0)
    expandRegion[0] = img[0] - halfX
    expandRegion[1] = img[1] - halfY
    expandRegion[2] = expandRegion[2] + expandXPixels
    expandRegion[3] = expandRegion[3] + expandYPixels
    expandRegion[0] = min(max(expandRegion[0], 0), maxX)
    expandRegion[1] = min(max(expandRegion[1], 0), maxY)
    if(expandRegion[0] + expandRegion[2] > maxX):
        expandRegion[2] = maxX - expandRegion[0]
    if(expandRegion[1] + expandRegion[3] > maxY):
        expandRegion[3] = maxY - expandRegion[1]

    return expandRegion


# def produceThreshold(img):
#     threshhold = bin.otsu(img)
#     return threshhold


def analysis(thresh):
    img2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    height, width = thresh.shape
    if(len(contours) > 0):
        return contours, hierarchy
    else:
        return False, False


def detect(img):
    if (img.shape[2] > 2):
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    rows, columns = grayimg.shape
    w = columns
    h = rows
    maxWidth = columns
    maxHeight = rows
    scale_factor = computeScaleFactor(w, h)
    if scale_factor != 1:
        grayimg = cv2.resize(grayimg, dsize=(w*scale_factor, h*scale_factor))

    regions = find_plates(grayimg, maxWidth, maxHeight)
    allregions = []
    imglist = []
    if(len(regions) != 0):
        new_regions = []
        for i in range(0, len(regions)):
            regions[i][0] = regions[i][0] / scale_factor
            regions[i][1] = regions[i][1] / scale_factor
            regions[i][2] = regions[i][2] / scale_factor
            regions[i][3] = regions[i][3] / scale_factor


            o_region = expandRect(regions[i], 0, 0, w, h)
            new_regions.append(o_region)
        for (x, y, w, h) in new_regions:
            one_region = Rect(x, y, w, h)
            allregions.append(one_region)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.imshow('img', img)
            text_img = grayimg[y:y + h, x:x + w]
            text_img = cv2.resize(text_img, dsize=(120, 60))
            imglist.append(text_img)
    return imglist, allregions

# def resize(img, grayimg, regions):
#     rows, columns = grayimg.shape
#     w = columns
#     h = rows
#     new_regions = []
#     for region in regions:
#         o_region = expandRect(region, 0, 0, w, h)
#         new_regions.append(o_region)
#     for (x, y, w, h) in new_regions:
#         cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
#         text_img = grayimg[y:y + h, x:x + w]
#         res = cv2.resize(text_img, dsize=(120, 60))
#     return res



# img = cv2.imread('2.png')
# if(img.shape[2] > 2):
#     grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#
# rows, columns = grayimg.shape
# w = columns
# h = rows
# maxWidth = columns
# maxHeight = rows
# scale_factor = computeScaleFactor(columns, rows)
# regions = find_plates(grayimg, maxWidth, maxHeight)
#
#
# new_regions = []
# for region in regions:
#     o_region = expandRect(region, 0, 0, w, h)
#     new_regions.append(o_region)
# for (x,y,w,h) in new_regions:
#     cv2.rectangle(img, (x,y),(x+w,y+h), (255,0,0), 2)
#     text_img = grayimg[y:y+h, x:x+w]
#
#
# res = cv2.resize(text_img, dsize=(100, 100))
# threshold = produceThresholds(res)
# contours, hierarchy = analysis(threshold)


#
# cv2.imshow('te', res)
# cv2.imshow('img',img)
# cv2.imshow('1', grayimg)
# cv2.waitKey(0)
# cv2.destroyAllWindows()