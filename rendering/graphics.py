#!/usr/bin/python3.2
# -*- coding: utf-8 -*-

import tkinter as tk
from math import cos, sin, pi

class Point(dict):

    def __init__(self, x, y):
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
                                       tags=str(hash(self)))
        else:
            raise TypeError('master must be of <Canvas> type.')

    def __add__(self, other):
        if isinstance(other, (Point, dict)):
            return Point(self['x'] + other['x'], self['y'] + other['y'])
        elif isinstance(other, (list, tuple)):
            return Point(self['x'] + other[0], self['y'] + other[1])
        else:
            raise TypeError('Only <tuple>, <list>, <dict> & <Point> can be\
 added to <Point> objects.')

class Line(list):

    def __init__(self, start, end):
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

class Path(list):

    def __init__(self, *points):
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

class Polygon(Path):

    def __init__(self, *points):
        self.vertices = points + points[0:1]
        self.genlines()
        self.genpoints()

class Rectangle(Polygon):

    def __init__(self, start, end):
        points = (start, (start[0], end[1]), end, (start[1], end[0]))
        super().__init__(*points)

class Curve(list):

    def __init__(self, func=lambda x: x, dom=[0, 100], res=1):
        self.func = func
        self.dom = [int(res*i) for i in dom]
        self.genpoints()

    def genpoints(self):
        for t in range(*self.dom):
            self.append(Point(*self.func(t)))

    def display(self, master=None):
        for point in self:
            point.display(master)

class Circle(Curve):

    def __init__(self, center=(0, 0), radius=100, res=2e4):
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
    canvas.pack()
    root.mainloop()
    root.destroy()
