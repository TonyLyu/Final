import cv2
import numpy as np

# Load the image
img = cv2.imread('3.png')

# convert to grayscale
gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
# smooth the image to avoid noises
#gray = cv2.medianBlur(gray,5)

# Apply adaptive threshold
#thresh = cv2.adaptiveThreshold(gray,255,1,1,11,2)
#thresh_color = cv2.cvtColor(thresh,cv2.COLOR_GRAY2BGR)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
ret2, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY+ cv2.THRESH_OTSU)
thresh_color = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
# apply some dilation and erosion to join the gaps
#thresh = cv2.dilate(thresh,None,iterations = 1)
#thresh = cv2.erode(thresh,None,iterations = 1)

# Find the contours
#img2,contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
listofimage = []
img2,contours,hierarchy = cv2.findContours(thresh, 1, cv2.CHAIN_APPROX_NONE)
# For each contour, find the bounding rectangle and draw it
for cnt in contours:
    x,y,w,h = cv2.boundingRect(cnt)
    if(h > 20 and w > 10 and w < 80):
    	cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
    	cv2.rectangle(thresh_color,(x,y),(x+w,y+h),(0,255,0),2)
    	#img3 = cv2.getRectSubPix(thresh, (w,h), (x+w,y+h))
    	img3 = thresh[y:y+h, x:x+w]
    	img4 = cv2.contourArea(cnt)
    	print(x)
    	print(y)
    	print(w)
    	print(h)
    	listofimage.append(img3)

# Finally show the image
cv2.imshow('img',img)
cv2.imshow('res',thresh_color)
i = 0
for img in listofimage:
	l = str(i)
	print(l)
	h,w = img.shape
	print(img.shape)
	if(h>0 and w>0):
		cv2.imshow(l, img)
	i = i + 1
cv2.waitKey(0)
cv2.destroyAllWindows()
