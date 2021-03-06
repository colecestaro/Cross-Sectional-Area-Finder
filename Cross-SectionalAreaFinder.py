import cv2
import numpy as np
import tkinter
import tkinter.filedialog as tkfd
from PIL import Image
import matplotlib.pyplot as plt
import math


# create window named root to create file dialog
root = tkinter.Tk()
root.withdraw()
# show file dialog
imageFilePath = tkfd.askopenfilename()
path = imageFilePath


#############################################
# actual code implementation
#############################################

# sourcing the input image
# img wis the ORIGINAL image
img = cv2.imread(path)

# img.shape gives back height, width, color in this order
original_height, original_width, color = img.shape
print('Original Dimensions : ', original_width, original_height)

# resizing to see the entire image
scale_percent = 50
width = int(original_width * scale_percent / 100)
height = int(original_height * scale_percent / 100)
print('Resized Dimensions : ', width, height)

dim = (width, height)
# resize image as resized
resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
cv2.imshow("Starting image", resized)
cv2.waitKey()

# blurring; Applies a Gaussian filter onto the original image
imgBlur = cv2.GaussianBlur(resized, (7, 7), 1)
# save image for reference
cv2.imwrite('imgBlur.png', imgBlur)

# convert to grayscale
imgGray = cv2.cvtColor(imgBlur, cv2.COLOR_BGR2GRAY)

# initialing thresholds
threshold1 = 14
threshold2 = 17

# apply Canny algorithm
imgCanny = cv2.Canny(imgGray, threshold1, threshold2)
cv2.imwrite('imgCanny.png',imgCanny)
# showing the last produced result
cv2.imshow("imgCanny", imgCanny)
cv2.waitKey()

# kernel for convolution; keep as as small as possible
kernel = np.ones((2, 2))
imgDil = cv2.dilate(imgCanny, kernel, iterations=2)
# erodes away the background to contour lines; basically "thins" lines
imgThre = cv2.erode(imgDil, kernel, iterations=1)
#cv2.imshow('imgThre', imgThre) # show eroded image

# "closes" img; i.e. removes small pin dots
# closing kernel; want to be LARGER than other kernel to effectively mitigate holes
closingKernelSize = 2
closingKernel = np.ones((closingKernelSize, closingKernelSize))
closedImg = cv2.morphologyEx(imgThre, cv2.MORPH_CLOSE, closingKernel, iterations = 4) # numpy.ndarray
cv2.imshow('closedImg', closedImg)
cv2.imwrite('closedImg.png', closedImg)

# lets now use the contours of the image to find area:
# this is the black and white picture
closedImgCOPY = closedImg

# now lets show the contours of the shapes as identified using the closedImgCopy
# Note: RETR_CCOMP allows for child contours to be shown
contours, hierarchy = cv2.findContours(closedImgCOPY, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE
                                       )
##drawnOver = cv2.drawContours(image=resized, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
##cv2.imshow("Contoured Image", resized)

##############################################################################################
# Marker filter section

# now lets make sure that we REMOVE the outlines of any rulers, markers, etc:
# This will create a new list of contours with RECTANGLEs (and any other shapes that we want to specify) filtered out

# define a function that determines if a given contour is rectangular or not
# handy for removing certain objects from foreground
def contourIsARectangle(contour):
	# approximate the contour
    # finds perimeter
	peri = cv2.arcLength(contour, True)
	approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
	# the contour is 'bad' if it IS rectangle
    # returns true is approximate len == 4
	return len(approx) == 4

no_rec_contours = []
for eachContour in contours:
    if (contourIsARectangle(eachContour)):
        # if it is a rectangle do not add to list of contours
        pass
    else:
        # if not rectangle, add to list of contours
        no_rec_contours.append(eachContour)
no_rec_contours_tup = tuple(no_rec_contours)

# End marker filter section
##################################################################33333

# now we want to a) isolate ONLY the two enclosed contour loops (outer loop, inner loop)
#                b) determine area ==> cv2.contourArea is a handy function that calcualates it directly

# this will sort your contours by area
contoursSorted = sorted(no_rec_contours_tup, key=cv2.contourArea, reverse= True)
outerLoop = contoursSorted[0] # outer loop has largest area
areaOuterLoop = cv2.contourArea(outerLoop)
innerLoop = contoursSorted[1] # inner loop has 2nd largest area
areaInnerLoop = cv2.contourArea(innerLoop)
# creates a tuple of tuples which contains the outerLoop and innerLoop
tupleToDraw = (outerLoop, innerLoop)

finalContours = cv2.drawContours(image=resized, contours=outerLoop, contourIdx=-1, color=(0, 255, 0), thickness=3, lineType=cv2.LINE_AA)
finalContours = cv2.drawContours(image=resized, contours=innerLoop, contourIdx=-1, color=(0, 0, 255), thickness=3, lineType=cv2.LINE_AA)
# uncomment the below to show the two different contours
cv2.imshow('Final Contours', resized)
#cv2.imwrite("FinalContours.png", finalContours)

finalContoursfilled = cv2.fillPoly(resized, pts =[outerLoop, innerLoop], color=(0,0,255))


cv2.waitKey()
cv2.destroyAllWindows()

totalPixelArea = areaOuterLoop - areaInnerLoop
print("The pixel cross-sectional area is: ", totalPixelArea)


#####################################################################################################
"""
# This is the calibration section
# This will accept an image and allow one to select a line. It will then return the pixel length
"""
def referenceLineDrawer( imageFileInput ):
    """

    :param imageFileInput:
    :return: lengthPix [float, length of reference line in pixels]
    """

    # now establish the real world size with a reference measuremnt
    # initialize lists that contain the coordinates of the mouse click
    xli, yli = [], []

    # this class, drawn from this helpful code from Stack:
    # https://stackoverflow.com/questions/9136938/matplotlib-interactive-graphing-manually-drawing-lines-on-a-graph
    # allows one to draw directly onto the image
    # I added modification which capture the event position and records it
    class LineBuilder:
        def __init__(self, line):
            self.line = line
            self.xs = list(line.get_xdata())
            self.ys = list(line.get_ydata())
            line.set_color('red')
            self.cid = line.figure.canvas.mpl_connect('button_press_event', self)

        def __call__(self, event):
            print('click', event)
            if event.inaxes != self.line.axes: return
            xli.append(event.xdata)
            yli.append(event.ydata)
            self.xs.append(event.xdata)
            self.ys.append(event.ydata)
            self.line.set_data(self.xs, self.ys)
            self.line.figure.canvas.draw()

    # create a matplotlib subplot (a frame basically)
    fig, ax = plt.subplots()
    # now load this image into the subplot
    plt_image = plt.imshow(imageFileInput)
    # Now put in this text
    ax.set_title('Click endpoints of reference line')
    line, = ax.plot([0], [0])  # empty line
    # call the linebuilder function
    linebuilderInstance = LineBuilder(line)
    # display the image
    calibratedImage = plt.savefig('calibratedImage')
    plt.show()

    # need to extract coordinates of mouse clicks from event data (previously appended onto list):
    x1, y1, x2, y2 = xli[0], yli[0], xli[1], yli[1]

    # now calculate the length scale using event data (mouse click coordinates)
    lengthPix = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    ########################################################################################
    return lengthPix

referenceLineBuiltLength = referenceLineDrawer(resized)

####################################################################
# This is the area calculation section:
def areaCalculator(referenceLineBuiltLength, totalPixelArea):
    """

    :param referenceLineBuiltLength: float
    :param totalPixelArea:  float
    :return: actualArea [float], lengthscaleUnit [str, user input]
    """
    lengthPix = referenceLineBuiltLength
    lengthscale = input("Enter the length of the reference line: ")
    lengthscaleUnit = input("Enter the length units of the reference line: ")
    actualArea = (totalPixelArea) * ((float(lengthscale) ** 2) / (float(lengthPix) ** 2))
    return( actualArea, lengthscaleUnit )
####################################################################

calculatedArea = areaCalculator(referenceLineBuiltLength,totalPixelArea)
print("The actual cross-sectional area is: ", calculatedArea[0], ' ', calculatedArea[1], '^2')
