import math
import sys
from dcServo import *
from myGraphics import *
from inputs import get_gamepad
from threading import Thread


def calc_joint_angles(coords): # bez uwzglednienia zalamania na drugim stawie
    a = 170
    b = 120
    c = 50
    d = 100
    e = 60
    f = 30
    x = coords[0]
    y = coords[1]
    c2= x^2 + y^2
    alfa1 = math.atan(y / x)
    gamma = math.acos((a^2 + b^2 - c2) / (2 * a * b))
    alfa2 = math.asin(b / math.sqrt(c2) * math.sin(gamma))
    alfa = alfa1 + alfa2  # first joint angle
    p1 = math.sqrt(a^2 + e^2 - 2*a*e*math.cos(3.1415-gamma))
    alfa3 = 180-alfa - math.asin(e / p1 * math.sin(3.1415 - gamma))
    p2 = math.sqrt(p1^2 + f^2 - 2*p1*f*math.cos(alfa3))
    beta1 = math.asin(p1 / p2 * math.sin(alfa3))
    beta2 = math.acos((c^2 + p2^2 - d^2) / (2*c*p2))
    beta = beta1 + beta2
    return alfa, beta


def send_to_manipulator(alfa, beta, s1, s2):
    s1.write(b"sett{}RQ".format(alfa*1000))
    s2.write(b"sett{}RQ".format(beta*1000))


class CheckThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.mainFlag = True
        self.pressed_up = False
        self.pressed_down = False
        self.quit_button = False
        self.x = 0
        self.y = 0
        self.z = 0

    @staticmethod
    def cut(temp):    # eliminating non_zero values from released pad
        if abs(temp) > 2000:
            c = temp / 400
        else:
            c = 0
        return c

    def run(self):
        while self.mainFlag:
            events = get_gamepad()
            for event in events:
                #  print(event.ev_type, event.code, event.state)
                if event.ev_type == "Key":
                    if event.code == "BTN_TR" and event.state == 1:
                        self.pressed_up = True
                    if event.code == "BTN_TL" and event.state == 1:
                        self.pressed_down = True
                    if event.code == "BTN_EAST" and event.state == 1:
                        self.quit_button = True
                if event.ev_type == "Absolute":
                    if event.code == "ABS_X":
                        self.x = self.cut(event.state)
                    if event.code == "ABS_Y":
                        self.y = self.cut(event.state)
                    if event.code == "ABS_RX":
                        self.z = self.cut(event.state)

    def stop(self):
        self.mainFlag = False


def read_from_serial(ser, name):
    msg = ser.readline()
    msg = msg.decode('utf-8')

    if not msg == "":
        tp = msg[0]
        data = msg.split()
        sys.stdout.write('{}  '.format(name))
        if tp == 'u':
            print("servo reported unsuported msg")
        else:
            # print(data[0][1: -1])  # for debuging purposes
            num = float(data[0][1: -1])

        if tp == "K":
            position = float(data[1][0: -1])
            print("position = {}   power = {}".format(num, position))
        elif tp == "P" or tp == "I" or tp == "D":
            print("{} set to {}".format(tp, num))
        elif tp == "S":
            print("setpoint = {}".format(num))
        else:
            print("BAD DATA: {}".format(msg))


def set_pids(s, ser):
    for obj in [s.P, s.I, s.D]:
        msg = u'pid{}{}RQ'.format(obj.name, float(obj.get_val()))
        ser.write(msg.encode('utf-8'))


class Gasper:
    def __init__(self):
        self.s = []  # servo settings objects
        self.srs = []   # serial port objects
        self.w1 = MyGraphWin("dcServo", 400, 600)
        self.pad = CheckThread()  # starting gamepad listener thread
        self.pad.start()

        self.s.append(ServoSettings(100, 80, 4, 1.5, 0.5))
        self.s.append(ServoSettings(200, 80, 3.7, 1.8, 0.5))
        self.srs.append(connect('COM3', self.w1))
        self.srs.append(connect('COM5', self.w1))

    def run(self):
        last_time = 0
        coords = [0, 0]  # manipulator coordinates
        send = Button(150, 160, 70, 40, "green", "send")
        debug = Button(150, 220, 70, 40, "blue", "debug")
        quit = Button(150, 280, 70, 40, "red", "quit")
        b = [send, debug, quit]

        l_c_point = None  # last clicked point

        self.w1.display(self.s, b)

        while True:
            c_point = self.w1.win.checkMouse()
            if (c_point != l_c_point) and (c_point is not None):
                if inside(c_point, send):
                    print("sending PID settings\n\n")
                    set_pids(self.s[0], self.srs[0])
                    set_pids(self.s[1], self.srs[1])
                elif inside(c_point, quit):
                    self.end()
                    break
                elif inside(c_point, debug):
                    for i in self.srs:
                        i.write(b'sndtogRQ')
                l_c_point = c_point

            if self.pad.pressed_up:
                print("up")
                self.srs[0].write(b"setuRQ")
                self.pad.pressed_up = False

            if self.pad.pressed_down:
                print("down")
                self.srs[0].write(b"setdRQ")
                self.pad.pressed_down = False

            now = time.time()
            # ten times per second send new cords
            if now - last_time > 0.1 and (self.pad.x != 0 or self.pad.y != 0 or self.pad.z != 0):
                coords[0] += self.pad.x
                coords[1] += self.pad.y

                self.srs[0].write(b"sete{}RQ".format(self.pad.x))  # driving joint by adding a number to its position
                self.srs[1].write(b"sete{}RQ".format(self.pad.y))
                self.srs[1].write(b"setz{}RQ".format(self.pad.z * 0.385))  # limiting to <-255 ; 255>
                last_time = now

            if self.pad.quit_button:
                self.end()
                break

            key = self.w1.win.checkKey()
            if key is not None:
                if key == "Up":
                    self.srs[0].write(b"setuRQ")
                if key == "Down":
                    self.srs[0].write(b"setdRQ")

            read_from_serial(self.srs[0], "servo1")
            read_from_serial(self.srs[1], "servo2")

    def end(self):
        for i in self.srs:
            i.close()
        self.pad.stop()
        self.pad.join()
        self.w1.win.close()


gasper = Gasper()
gasper.run()

# TODO:
