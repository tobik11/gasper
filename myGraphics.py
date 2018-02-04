from graphics import *


class MyGraphWin:
    def __init__(self, name, width, height):
        self.win = GraphWin(name, width, height)
        self.win.setBackground("white")
        self.title = Text(Point(self.win.width / 2, self.win.height / 16), "PID settings")
        self.no_conn = Text(Point(self.win.width / 2, self.win.height / 2), "GASPER not connected")

    def display(self, s, butt):  # takes a list of settings and buttoms
        self.title.draw(self.win)
        r = Setting('tmp', self.win.width / 2, self.win.width * 7 / 8, "")
        r.draw(self)
        for i in s:
            i.draw(self)
        for i in butt:
            i.draw(self)


class ServoSettings:
    def __init__(self, x=0, y=0, p=1, i=1, d=1):
        self.P = Setting('P', x, y, p)
        self.I = Setting('I', x, y+30, i)
        self.D = Setting('D', x, y+60, d)

    def draw(self, w):
        self.P.draw(w)
        self.I.draw(w)
        self.D.draw(w)


class Setting:  # textbox
    def __init__(self, name,  x, y, val):
        self.name = name
        # self.servoNum = num
        self.obj = Entry(Point(x, y), 5)
        self.obj.setText(val)
        self.title = Text(Point(x-40, y), name)

    def draw(self, w):
        self.title.draw(w.win)
        self.obj.draw(w.win)

    def un_draw(self):
        self.title.undraw()
        self.obj.undraw()

    def get_val(self):
        try:
            num = float(self.obj.getText())

        except ValueError:
            print("accepting only numbers!!!, setting to 0")
            self.obj.setText("0")
            num = 0

        return num


class Button:
    def __init__(self, x, y, length, heigth, color, title):
        self.r = Rectangle(Point(x, y), Point(x + length, y + heigth))
        self.t = Text(Point(x + length/2, y + heigth/2), title)
        self.r.setFill(color)

    def draw(self, w):
        self.r.draw(w.win)
        self.t.draw(w.win)


def inside(point, butt):  # takes buttom object
    ll = butt.r.getP1()  # assume p1 is ll (lower left)
    ur = butt.r.getP2()  # assume p2 is ur (upper right)
    return ll.getX() < point.getX() < ur.getX() and ll.getY() < point.getY() < ur.getY()


