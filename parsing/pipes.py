import sys, pathlib, time, os

DELAY = 1

class Stream:
    'Writable & readable file, with builtin locks and list-like access.'
    
    def __init__(self, name, tty=False, buffer=1000):
        self.name = pathlib.Path(name)
        self.pos = 0
        self.lock = Lock(name)
        self.tty = tty
        self.buffsize, self.buffer, self.buffpos = buffer, '', 0
        self.mode = 'a+'
        self.acquire()
        with self.name.open() as file:
            self.buffer = file.read(self.buffsize)
            self.encoding = file.encoding
        self.release()

    def __iter__(self):
        return self

    def __next__(self):
        char = self.read(1)
        if char:
            return char
        else:
            raise StopIteration

    def __getitem__(self, index):
        if isinstance(index, int):
            self.seek(index)
            return self.read(1)
        elif isinstance(index, slice):
            self.seek(index.start)
            res = ''
            for i in range(0, index.stop-index.start,
                           index.step if index.step else 1):
                res += self.read(1)
            return res
        else:
            raise TypeError('index should be an int or slice.')

    def __setitem__(self, index, val):
        if not isinstance(val, str):
            raise TypeError('val should be a string.')
        if isinstance(index, int):
            self.seek(index)
            self.write(val)
        elif isinstance(index, slice):
            if index.step not in (1, None):
                raise ValueError('step must be 1.')
            self.seek(index.stop)
            backup = self.read()
            self.seek(index.start)
            self.truncate(index.start)
            self.write(val + backup)
        else:
            raise TypeError('index should be an int or slice.')

    def __delitem__(self, index):
        if isinstance(index, int):
            self[index] = ''
        elif isinstance(index, slice):
            for i in range(index.start, index.stop, index.step):
                self[i] = ''
        else:
            raise TypeError('index should be an int or slice.')

    def insert(self, index, val):
        index = self.tell() + index
        self.seek(index)
        backup = self.read()
        self.truncate(index)
        self.seek(index)
        self.write(val+backup)

    def isatty(self):
        return self.tty

    def acquire(self, *args, **kargs):
        return self.lock.acquire(*args, **kargs)

    def release(self, *args, **kargs):
        return self.lock.release(*args, **kargs)
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, trace):
        return not bool(exc_type)
    
    def fileno(self):
        with self.lock:
            with self.name.open() as file:
                return file.fileno()
    
    def close(self):
        pass
    
    def flush(self):
        pass
    
    def tell(self):
        return self.pos

    def seekable(self):
        return True
    
    def seek(self, pos, whence=0):
        if whence == 0:
            self.pos = pos
        elif whence == 1:
            self.pos += pos
        elif whence == 2:
            length = 0
            self.pos = len(self) - 1 + pos

    def __len__(self):
        with self.lock:
            with self.name.open() as file:
                return len(file.read())
        return 0

    def writable(self):
        return True
    
    def write(self, data):
        with self.lock:
            with self.name.open('a') as file:
                file.seek(self.pos)
                file.write(str(data))
                self.seek(file.tell())
    
    def writelines(self, data, sep=''):
        with self.lock:
            with self.name.open('a') as file:
                file.seek(self.pos)
                file.write(sep.join(str(i) for i in data))
                self.seek(file.tell())

    def readable(self):
        return True
    
    def read(self, size=-1):
        output = ''
        if self.pos < self.buffpos or\
           self.pos > self.buffpos + self.buffsize or\
           (self.pos + size > self.buffpos + self.buffsize and size != -1) or\
           size == -1:
            # The cursor was placed before or after the buffer,
            # or the selection ends after the buffer.
            with self.lock:
                with self.name.open() as file:
                    file.seek(self.pos)
                    output = file.read(size)
                    self.seek(file.tell())
                    self.buffpos = file.tell()
                    self.buffer = file.read(self.buffsize)
        else:
            start = self.pos - self.buffpos
            output = self.buffer[start:start+size]
            self.seek(size, 1)
        return output
    
    def readline(self, size=-1):
        output = ''
        with self.lock:
            with self.name.open() as file:
                file.seek(self.pos)
                output = file.readline(size)
                self.seek(file.tell())
        return output
    
    def readlines(self, sizehint=-1):
        output = ['']
        with self.lock:
            with self.name.open() as file:
                file.seek(self.pos)
                output = file.readlines(sizehint)
                self.seek(file.tell())
        return output

    def truncate(self, size=None):
        with self.lock:
            with self.name.open('a+') as file:
                file.seek(self.pos)
                newsize = file.truncate(size)
        return newsize

class Lock:

    def __init__(self, name=''):
        self.name = pathlib.Path(name)
        self.name = self.name.with_suffix('.lock')

    def acquire(self, blocking=True, timeout=-1, delay=DELAY):
        timeleft = timeout // delay
        while self.name.exists():
            with self.name.open() as file:
                if file.read().startswith(str(id(self))):
                    file.close()
                    break
            if blocking and timeleft:
                time.sleep(delay)
                timeleft -= 1
            else: return False
        with self.name.open('w') as file:
            print(id(self), file=file)
            print(time.time(), file=file)
            file.close()
            return True

    def release(self):
        if self.name.exists():
            with self.name.open() as file:
                if file.read().startswith(str(id(self))):
                    os.remove(str(self.name))
                else:
                    return False
        return True

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_value, trace):
        self.release()
        return not bool(exc_type)

if __name__ == '__main__':
    print('########################')
    print('# Trying out a stream! #')
    print('########################')
    name = input('Enter a file name: ')
    stream = Stream(name)
    data = True
    while data:
        data = input('What do you want to write?')
        stream.write(data)
        stream.seek(0)
        print('This is what was added:', repr(stream.read()))
    print('All done!')
