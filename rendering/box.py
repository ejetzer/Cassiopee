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
        print(tuple(i+padding for i in start), tuple(i-padding for i in end))
        self.padding = Rectangle(start, end)
        self.margin = Rectangle(tuple(i-margin for i in start),
                                tuple(i+margin for i in end))
        print(tuple(i-margin for i in start), tuple(i+margin for i in end))

    def display(self, master=None):
        self.margin.display(master)
        self.padding.display(master)
        self.container.display(master)
        for el in self:
            el.display(master)

if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(master=root)
    a = Box([], 100, 100, 10, 10, 0, 0)
    a.display(canvas)
    canvas.pack()
    root.mainloop()
