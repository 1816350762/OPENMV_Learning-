# Blob Detection and uart transport
import json
import sensor, image, time , math, pyb, ustruct
from pyb import LED, UART


rx_buff=[]
state = 1
tx_flag = 0

uart = UART(3, 115200, timeout_char=3000)

sensor.reset() # Initialize the camera sensor.
sensor.set_pixformat(sensor.RGB565) # use RGB565.
sensor.set_framesize(sensor.QVGA) # use QQVGA for speed.
sensor.skip_frames(10) # Let new settings take affect.
sensor.set_auto_whitebal(False) # turn this off.
#串口接收函数
def Receive_Prepare(data):
    global state
    global tx_flag
    if state==0:
        if data == 0x0d:#帧头
            state = 1
        else:
            state = 0
            rx_buff.clear()
    elif state==1:
        rx_buff.append(data)
        state = 2
    elif state==2:
        rx_buff.append(data)
        state = 3
    elif state == 3:
        if data == 0x5b:
            tx_flag = int(rx_buff[0])
            state = 4
    else:
        state = 0
        rx_buff.clear()

def find_max(blobs):
    max_size=0
    for blob in blobs:
        if blob[2]*blob[3] > max_size:
            max_blob=blob
            max_size = blob[2]*blob[3]
    return max_blob

while(True):
    if state == 1:  #识别光斑
        #clock.tick()
            threshold = (30, 100, -64, -8, -32, 32)
            img = sensor.snapshot() # Take a picture and return the image.
            blobs = img.find_blobs([threshold])
            if blobs:
                    largest_blob = find_max(blobs)
                    # 将质心坐标转换为 uint16 类型
                    x_coord = int(largest_blob.cx())
                    y_coord = int(largest_blob.cy())
                    # 打印坐标
                    print("Center at:", x_coord, y_coord)
                    # 在图像上绘制轮廓和质心
                    img.draw_rectangle(largest_blob.rect(), color=(255, 0, 0), thickness=2)
                    img.draw_cross(x_coord,y_coord, color=(0, 255, 0), thickness=2)
                    img_data=bytearray([0x2C,7,x_coord,y_coord,3,4,0X5B])
                    uart.write(img_data)
                # 显示处理后的图像
                #img.show()
            else:
                img_data=bytearray([0x2C,7,160,120,3,4,0X5B])
                uart.write(img_data)


    elif   state == 2:  #识别矩形框
        thresholds = [(1, 20, -20, 19, -13, 17)]
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565) # 灰度更快(160x120 max on OpenMV-M7)
        sensor.set_framesize(sensor.QQVGA)
        sensor.skip_frames(time = 2000)
        clock = time.clock()
        sensor.set_vflip (True)
        sensor.set_hmirror (True)
        led = pyb.LED(3).on()
        uart = UART(3,115200)   #定义串口3变量
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

        while(True):
            clock.tick()
            img = sensor.snapshot()
            for r in img.find_rects(threshold = 33000):
                img.draw_rectangle(r.rect(), color = (255, 0, 0))
                led = pyb.LED(3).off()
                led = pyb.LED(2).on()
                for li in r.corners():
                    img.draw_circle(li[0], li[1], 5, color = (0, 255, 0))
                    #print(li,xielu)
                    #print(check)
                    if check >= 10 and flag < 4: # 上电10次求出平均值和标志点坐标
                        flag += 1               # 实验发现10次求平均值后得到的原始数据会乱序（总体向前3个单位）
                        li_list.append(li)      # 加注flag < 4既等待3个单位以顺序正确
                        led = pyb.LED(2).off()
                        led = pyb.LED(1).on()
                        inix = (x_range/10)
                        iniy = (y_range/10)
                        wight_xiangsu = (wight_range / 10)
                        high_xiangsu = (high_range / 10)


                    else:
                        li_list.append(li)
                        if len(li_list) >= 4: # 当li_list里数据超过4个但不超过5个时（正常情况）绘制辅助边框
                            if len(li_list) < 5: # 实验发现当等待3个单位后，数据长度异常为5位 以此过滤
                                print(li_list,check,flag)
                                x_list = [x[0] for x in li_list]# 读取元组
                                y_list = [y[1] for y in li_list]
                                if flag == 4:  #  平均值得出后执行绘制辅助区域程序
                                    wight = (wight_xiangsu-inix)/21
                                    high = (high_xiangsu-iniy)/30
                                    wucha = wight-high
                                    print("误差为 :",wucha)
                                else:
                                    if abs(x_list[3]-x_last_range) < 10 and check >= 1 and abs(y_list[3]-y_last_range) < 10: # 10次检测中过滤误差大于10的数据
                                        x_range += x_list[3]
                                        y_range += y_list[3]
                                        wight_range = wight_range + (x_list[1] + x_list[2])/2
                                        high_range = high_range + (y_list[0] + y_list[1])/2
                                        check+=1
                                        x_last_range = x_range / check
                                        y_last_range = y_range / check
                                        #print('next')
                                    elif  check == 0:
                                        x_range += x_list[3]
                                        y_range += y_list[3]
                                        wight_range = wight_range + (x_list[1] + x_list[2])/2
                                        high_range = high_range + (y_list[0] + y_list[1])/2
                                        check+=1
                                        x_last_range = x_range / check
                                        y_last_range = y_range / check
                                        #print('first')
                                    else:
                                        x_last_range = x_range / check
                                        y_last_range = y_range / check
                                        #print('error')
                                #data = bytearray([0xb3,0xb3,inix,iniy,x_list[0]-inix,x_list[1]-inix,x_list[2]-inix,x_list[3]-inix,y_list[0]-iniy,y_list[1]-iniy,y_list[2]-iniy,y_list[3]-iniy,0x5b])# 重新构建的坐标系发送32处理/？在openmv内部处理
                                data = bytearray([0xb3,0xb3,x_list[0],x_list[1],x_list[2],x_list[3],y_list[0],y_list[1],y_list[2],y_list[3],0x5b])
                                uart.write(data)
                                x_list.clear()
                                y_list.clear()
                                li_list.clear()
                            else:
                                x_list.clear()
                                y_list.clear()
                                li_list.clear()

