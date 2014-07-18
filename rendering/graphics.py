#!/usr/bin/python3.4

import tkinter as tk
from math import cos, sin, pi

class Color:

    def __init__(self, r=0, g=0, b=0, a=1):
        self.r = r
        self.g = g
        self.b = b
        # I need to find a way to implement transparency...
        self.a = a
        self.model = '#{:0>4X}{:0>4X}{:0>4X}'

    def __str__(self):
        return self.model.format(int(self.r*16**4),
                                 int(self.g*16**4),
                                 int(self.b*16**4))

    def __add__(self, other):
        r = (self.a*self.r + other.a*other.r) / (self.a + other.a)
        g = (self.a*self.g + other.a*other.g) / (self.a + other.a)
        b = (self.a*self.b + other.a*other.b) / (self.a + other.a)
        a = (self.a*self.a + other.a*other.a) / (self.a + other.a)
        return Color(r, g, b, a)

class Point(dict):

    def __init__(self, x, y, color=Color(), distance='c'):
        self['x'] = x
        self['y'] = y

    def __repr__(self):
        return '(x, y) => ({}, {})'.format(self['x'], self['y'])

    def __hash__(self):
        return id(self)

    def display(self, master=None):
        if master:
            point = master.create_line(self['x'], self['y'],
                                       self['x']+1, self['y']+1,
                                       tags=str(hash(self)),
                                       color=str(self.color))
        else:
            raise TypeError('master must be of <Canvas> type.')

    def __add__(self, other):
        # Should addition allow for color mixing? Probably not...
        if isinstance(other, (Point, dict)):
            return Point(self['x'] + other['x'], self['y'] + other['y'])
        elif isinstance(other, (list, tuple)):
            return Point(self['x'] + other[0], self['y'] + other[1])
        else:
            raise TypeError('Only <tuple>, <list>, <dict> & <Point> can be\
 added to <Point> objects.')

    def __div__(self, other):
        # Division could be understood as a stacking operator,
        # used to superimpose points...
        # This is how transparency could be implemented.
        if isinstance(other, Point):
            if self['x'] == other['x'] and\
               self['y'] == other['y']:
                return Point(self['x'], self['y'],
                             color=self.color+other.color)
            else:
                return self
        elif isinstance(other, list):
            return [self/i for i in other]
        else:
            raise TypeError('Only <Point> objects can \'divide\' other \
<Point> objects.')

class Line(list):

    def __init__(self, start, end, color=Color()):
        self.start = Point(*start)
        self.end = Point(*end)
        self.genpoints()

    def delta(self, axis):
        return self.end[axis] - self.start[axis]

    def genpoints(self):
        if self.delta('x'):
            slope = self.delta('y') / self.delta('x')
            offset = self.start['y'] - slope * self.start['x']
            func = lambda x: round(slope*x + offset)
            step = -1 if self.delta('x') < 0 else 1
            for index in range(self.start['x'], self.end['x']+step, step):
                self.append(Point(index, func(index)))
        elif self.delta('y'):
            step = -1 if self.delta('y') < 0 else 1
            for index in range(self.start['y'], self.end['y']+step, step):
                self.append(Point(self.start['x'], index))
        else:
            self.append(self.start)

    def display(self, master=None):
        for point in self:
            point.display(master)

    def __div__(self, other):
        if isinstance(other, Point):
            return [i/other for i in self]
        elif isinstance(other, list):
            output = Line(self[:])
            for i in range(len(self)):
                for pt in other:
                    output[i] = output[i] / pt
        else:
            raise TypeError('Sorry, this has to be some list of Point objects, \
or a Point object so that it can divide a Line.')

class Path(list):

    def __init__(self, *points, color=Color()):
        self.vertices = points
        self.genlines()
        self.genpoints()

    def genlines(self):
        self.lines = []
        for index in range(1, len(self.vertices)):
            self.lines.append(Line(self.vertices[index-1],
                                   self.vertices[index]))

    def genpoints(self):
        for line in self.lines:
            self.extend(line)

    def display(self, master=None):
        for point in self:
            point.display(master)

    def __div__(self, other):
        if isinstance(other, Point):
            return [i/other for i in self]
        elif isinstance(other, list):
            output = self[:]
            for i in range(len(self)):
                for pt in other:
                    output[i] = output[i] / pt
            return output

class Polygon(Path):

    def __init__(self, *points, color=Color()):
        self.vertices = points + points[0:1]
        self.genlines()
        self.genpoints()

class Rectangle(Polygon):

    def __init__(self, start, end, color=Color()):
        width = end[0] - start[0]
        height = end[1] - start[1]
        points = (start, (start[0], start[1]+height),
                  end, (start[0]+width, start[1]))
        super().__init__(*points)

class Curve(list):

    def __init__(self, func=lambda x: x, dom=[0, 100], res=1, color=Color()):
        self.func = func
        self.dom = [int(res*i) for i in dom]
        self.genpoints()

    def genpoints(self):
        for t in range(*self.dom):
            self.append(Point(*self.func(t)))

    def display(self, master=None):
        for point in self:
            point.display(master)

    def __div__(self, other):
        if isinstance(other, Point):
            return [i/other for i in self]
        elif isinstance(other, list):
            output = self[:]
            for i in range(len(self)):
                for pt in other:
                    output[i] = output[i] / pt
            return output

class Circle(Curve):

    def __init__(self, center=(0, 0), radius=100, res=2e4, color=Color()):
        super().__init__(lambda t: (round(radius * cos(2*t/res) + center[0]),
                                    round(radius * sin(2*t/res) + center[1])),
                         [0, pi],
                         res)

if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(master=root)
    a = Point(50, 50)
    a.display(canvas)
    b = Line((50, 60), (70, 80))
    b.display(canvas)
    c = Path((50, 90), (70, 90), (70, 100))
    c.display(canvas)
    d = Circle((100, 100), 75)
    d.display(canvas)
    e = Curve(lambda t: (t/10, 1e-4*t**2), [0, 10], 1e4)
    e.display(canvas)
    f = Rectangle((10, 10), (50, 100))
    f.display(canvas)
    canvas.pack()
    root.mainloop()
    root.destroy()
