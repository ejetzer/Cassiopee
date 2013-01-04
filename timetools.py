# -*- coding: utf-8 -*-

from time import time

class Timer:

    def __init__(self):
        self.starttime = 0.0
        self.endtime = 0.0
        self.duration = 0.0
        self.totaltime = 0.0

    def start(self):
        self.starttime = time()

    def stop(self):
        self.endtime = time()
        self.duration = self.endtime - self.starttime
        self.totaltime += self.duration

    def __str__(self):
        return '''The operation took {}sec, and the program took a total time \
of {}sec.'''.format(self.duration, self.totaltime)
