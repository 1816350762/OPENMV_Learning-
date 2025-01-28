import sensor, image, time, math, omv
from machine import UART#串口通信的依赖
import time

sensor.reset()
sensor.set_pixformat(sensor.RGB565) # use RGB565.
sensor.set_framesize(sensor.QQVGA) # use QQVGA for speed.
if omv.board_type() == "H7": sensor.set_windowing((240, 240))
elif omv.board_type() == "M7": sensor.set_windowing((200, 200))
else: raise Exception("You need a more powerful OpenMV Cam to run this script")
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()

uart = UART(3, 9600)#串口通信的基础设置


while(True):
    clock.tick() # Track elapsed milliseconds between snapshots().
    img = sensor.snapshot().lens_corr(1.8)

    for c in img.find_circles(
        threshold=4000,
        x_margin=10,
        y_margin=10,
        r_margin=10,
        r_min=2,
        r_max=100,
        r_step=2,
    ):
        img.draw_circle(c.x(), c.y(), c.r(), color=(255, 0, 0))


        # Draw a rect around the blob.
        uart.write("@%d \r\n" % int(c.x()*100+c.y()))#串口通信（里面为内容）
        print(c)


