from parsing import Parser
from timetools import Timer
from zipfile import ZipFile
import os, shutil

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
    
