# -*- coding: utf-8 -*-

from graphics import *

class Font(list):
    pass

class DefaultFont(Font):

    def __getitem__(self, code):
        # Define a box with a cross, standard symbol for an unknown symbol.
        yield Path((0, 0), (20, 0), (20, 30), (0, 30),
                   (20, 0), (0, 0), (20, 30))

class Letter(list):

    def __init__(self, code, *args, font=DefaultFont(), **kargs):
        lines = font[code]

    def display(self, master=None):
        if master:
            for line in lines:
                line.display(master)
        else:
            raise TypeError('master must be of <Canvas> type.')

class TextLine(list):

    def __init__(self, line):
        pass

class Paragraph(list):
    pass

if __name__ == '__main__':
    text = '''This things is a paragraph, made of text, that has to be\
displayed.
There are several lines to show.
The program should display all of them within a box of a given size.'''
    width = 200
