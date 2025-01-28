# Template Matching Example - Normalized Cross Correlation (NCC)
#
# This example shows off how to use the NCC feature of your OpenMV Cam to match
# image patches to parts of an image... expect for extremely controlled environments
# NCC is not all to useful.
#
# WARNING: NCC supports needs to be reworked! As of right now this feature needs
# a lot of work to be made into somethin useful. This script will remain to show
# that the functionality exists, but, in its current state is inadequate.

import time
import sensor
import image
from image import SEARCH_EX
import display
# from image import SEARCH_DS

# Reset sensor
sensor.reset()

# Set sensor settings
sensor.set_contrast(1)
sensor.set_gainceiling(16)
# Max resolution for template matching with SEARCH_EX is QQVGA
sensor.set_framesize(sensor.QQVGA)
# You can set windowing to reduce the search image.
# sensor.set_windowing(((640-80)//2, (480-60)//2, 80, 60))
sensor.set_pixformat(sensor.GRAYSCALE)
lcd = display.SPIDisplay()
# Load template.
# Template should be a small (eg. 32x32 pixels) grayscale image.
template1 = image.Image("/1.pgm")
template2 = image.Image("/2.pgm")
template3 = image.Image("/3.pgm")

clock = time.clock()

# Run template matching
while True:
    clock.tick()
    img = sensor.snapshot()

    # find_template(template, threshold, [roi, step, search])
    # ROI: The region of interest tuple (x, y, w, h).
    # Step: The loop step used (y+=step, x+=step) use a bigger step to make it faster.
    # Search is either image.SEARCH_EX for exhaustive search or image.SEARCH_DS for diamond search
    #
    # Note1: ROI has to be smaller than the image and bigger than the template.
    # Note2: In diamond search, step and ROI are both ignored.
    r1 = img.find_template(
        template1, 0.70, step=4, search=SEARCH_EX
    )  # , roi=(10, 0, 60, 60))
    if r1:
        img.draw_rectangle(r1,color=(0,0,0))

    r2 = img.find_template(
        template2, 0.70, step=4, search=SEARCH_EX
    )  # , roi=(10, 0, 60, 60))
    if r2:
        img.draw_rectangle(r2,color=(255,0,0))

    r3 = img.find_template(
        template3, 0.70, step=4, search=SEARCH_EX
    )  # , roi=(10, 0, 60, 60))
    if r3:
        img.draw_rectangle(r3)
    lcd.write(img)
    print(clock.fps())
