import tkinter as tk
from graphics import *

class Box(list):

    def __init__(self, content,
                 width, height,
                 top=0, left=0,
                 padding=0, margin=0):
        super().__init__(content)
        start = (left, top)
        end = (left+width, top+height)
        self.container = Rectangle(tuple(i+padding for i in start),
                                   tuple(i-padding for i in end))
        self.padding = Rectangle(start, end)
        self.margin = Rectangle(tuple(i-margin for i in start),
                                tuple(i+margin for i in end))

    def display(self, master=None):
        self.margin.display(master)
        self.padding.display(master)
        self.container.display(master)
        for el in self:
            el.display(master)

    def __div__(self, other):
        if isinstance(other, Point):
            return [i/other for i in self]
        elif isinstance(other, list):
            output = Line(self[:])
            for i in range(len(self)):
                for pt in other:
                    output[i] = output[i] / pt

    def bind(self, sequence, func, add=''):
        pass

if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(master=root)
    canvas.master.title('My Box Model Tests')
    a = Box([], 100, 100, 10, 10, 5, 5)
    a.display(canvas)
    canvas.pack()
    root.mainloop()
