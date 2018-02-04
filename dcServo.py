import serial
from time import sleep


def connect(port, w):
    conn = None
    er_draw = False
    while not conn:
        try:
            conn = serial.Serial(port, 9600, timeout=0.1)
            if er_draw:
                w.no_conn.undraw()
                er_draw = False
                break
        except serial.SerialException:
            if not er_draw:
                w.no_conn.draw(w.win)
                er_draw = True
        sleep(1)
    return conn
