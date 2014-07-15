from parsing import Parser
from timetools import Timer
from zipfile import ZipFile
import os, shutil

import xml.etree.ElementTree as ET
from xml.dom.minidom import parse as domparse

if __name__ == '__main__':
    N = 100
    ## Active testing for the parser.
    file = 'source/source.xml'
    print('## == Now, a parser show off == ##')
    parser = Parser()
    timer1 = Timer()
    print('Let\'s go, New Parser!')
    for i in range(N):
        if not i % (N//10): print('Going around for the {}th time...'.format(i))
        folder = ZipFile('source.zip')
        folder.extractall()
        timer1.start()
        parser(file)
        timer1.stop()
        shutil.rmtree('source')
    print(timer1)
    print('The average is of', timer1.totaltime/N)

    ## ElementTree
    timer2 = Timer()
    print('How are you doing, etree?')
    for i in range(N):
        if not i % (N//10): print('{}th time...'.format(i))
        folder = ZipFile('source.zip')
        folder.extractall()
        timer2.start()
        tree = ET.parse(file)
        timer2.stop()
        shutil.rmtree('source')
    print(timer2)
    print('The average is of', timer2.totaltime/N)

    ## DOM
    timer3 = Timer()
    print('How are you doing, etree?')
    for i in range(N):
        if not i % (N//10): print('{}th time...'.format(i))
        folder = ZipFile('source.zip')
        folder.extractall()
        timer3.start()
        tree = domparse(file)
        timer3.stop()
        shutil.rmtree('source')
    print(timer3)
    print('The average is of', timer3.totaltime/N)
    
