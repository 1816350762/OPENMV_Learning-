import json
import sensor, image, time, math, pyb, ustruct
from pyb import LED, UART
import pyb, time


# 初始化UART
uart = UART(3, 115200, timeout_char=3000)

# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(10)
sensor.set_auto_whitebal(False)

# 定义全局变量
rx_buff = []
state = 1
tx_flag = 0

# 接收数据的状态机
def receive_prepare(data):
    global state, tx_flag, rx_buff
    if state == 0:
        if data == 0x0d:  # 帧头
            state = 1
        else:
            state = 0
            rx_buff.clear()
    elif state == 1:
        rx_buff.append(data)
        state = 2
    elif state == 2:
        rx_buff.append(data)
        state = 3
    elif state == 3:
        if data == 0x5b:
            tx_flag = int(rx_buff[0])
            state = 4
        else:
            state = 0
            rx_buff.clear()
    else:
        state = 0
        rx_buff.clear()

# 处理接收到的命令
def handle_command():
    global state
    if tx_flag == 0x01:
        state = 1  # 切换到光斑检测模式
    elif tx_flag == 0x02:
        state = 2  # 切换到矩形框检测模式
    else:
        state = 0  # 无效指令，保持当前模式

# 找到最大的blob
def find_max(blobs):
    max_size = 0
    max_blob = None
    for blob in blobs:
        if blob[2] * blob[3] > max_size:
            max_size = blob[2] * blob[3]
            max_blob = blob
    return max_blob

# 光斑检测模式
def blob_detection():
    #threshold = (95, 100, -64, -8, -32, 32)#绿色
    threshold =(92, 100, -4, 15, -9, 3)   #红色
    img = sensor.snapshot()
    blobs = img.find_blobs([threshold])
    if blobs:
        largest_blob = find_max(blobs)
        x_coord = int(largest_blob.cx())
        y_coord = int(largest_blob.cy())
        print("Center at:", x_coord, y_coord)
        img.draw_rectangle(largest_blob.rect(), color=(255, 0, 0), thickness=2)
        img.draw_cross(x_coord, y_coord, color=(0, 255, 0), thickness=2)
        img_data = bytearray([0x2C, 7, x_coord, y_coord, 3, 4, 0X5B])
        uart.write(img_data)
    else:
        img_data = bytearray([0x2C, 7, 160, 120, 3, 4, 0X5B])
        uart.write(img_data)

# 矩形框检测模式
def rectangle_detection():
    thresholds = [(1, 20, -20, 19, -13, 17)]
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QQVGA)
    sensor.skip_frames(time=2000)
    clock = time.clock()
    sensor.set_vflip(True)
    sensor.set_hmirror(True)
    led = pyb.LED(3).on()
    uart.init(115200, bits=8, parity=None, stop=1)
    flag = 1
    check = 0
    x_range = 0
    y_range = 0
    x_last_range = 0
    y_last_range = 0
    high = 0
    high_range = 0
    wight = 0
    wight_range = 0
    inix = 0
    iniy = 0
    wight_xiangsu = 0
    high_xiangsu = 0
    li_list = []
    x_list = []
    y_list = []
    while True:
        clock.tick()
        img = sensor.snapshot()
        for r in img.find_rects(threshold=33000):
            img.draw_rectangle(r.rect(), color=(255, 0, 0))
            led = pyb.LED(3).off()
            led = pyb.LED(2).on()
            for li in r.corners():
                img.draw_circle(li[0], li[1], 5, color=(0, 255, 0))
                if check >= 10 and flag < 4:
                    flag += 1
                    li_list.append(li)
                else:
                    li_list.append(li)
                    if len(li_list) >= 4 and len(li_list) < 5:
                        x_list = [x[0] for x in li_list]
                        y_list = [y[1] for y in li_list]
                        if flag == 4:
                            wight = (wight_xiangsu - inix) / 21
                            high = (high_xiangsu - iniy) / 30
                            wucha = wight - high
                            print("误差为 :", wucha)
                        else:
                            if abs(x_list[3] - x_last_range) < 10 and check >= 1 and abs(y_list[3] - y_last_range) < 10:
                                x_range += x_list[3]
                                y_range += y_list[3]
                                wight_range = wight_range + (x_list[1] + x_list[2]) / 2
                                high_range = high_range + (y_list[0] + y_list[1]) / 2
                                check += 1
                                x_last_range = x_range / check
                                y_last_range = y_range / check
                            elif check == 0:
                                x_range += x_list[3]
                                y_range += y_list[3]
                                wight_range = wight_range + (x_list[1] + x_list[2]) / 2
                                high_range = high_range + (y_list[0] + y_list[1]) / 2
                                check += 1
                                x_last_range = x_range / check
                                y_last_range = y_range / check
                            else:
                                x_last_range = x_range / check
                                y_last_range = y_range / check
                        data = bytearray([0xb3, 0xb3, x_list[0], x_list[1], x_list[2], x_list[3], y_list[0], y_list[1], y_list[2], y_list[3], 0x5b])
                        uart.write(data)
                        x_list.clear()
                        y_list.clear()
                        li_list.clear()
                    else:
                        x_list.clear()
                        y_list.clear()
                        li_list.clear()

p = pyb.Pin("P0", pyb.Pin.IN)
clock = time.clock() # 追踪帧率，影响不大
while True:
    key_value = p.value() # Returns 0 or 1.
    if key_value == 1:
        key_time_first  = clock.tick() #开始计时
        Task1 = 1
        while key_value == 1: #一直等待松手
            pass
    if key_value == 0:  #确认松手
        key_time_last = clock.avg()
        if(key_time_last-key_time_first> 2000) :  #如果按键按下时间超过2s
            blob_detection()
        elif Task1 == 1 : #如果按键按下时间小于1s
            # 进入任务1
            rectangle_detection()
            pass
        else:
             handle_command()
