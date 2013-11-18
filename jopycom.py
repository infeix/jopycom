#!/usr/bin/python

import time
import sys
import serial
import termios
import contextlib
import threading
import os


@contextlib.contextmanager
def raw_mode(file):
    old_attrs = termios.tcgetattr(file.fileno())
    new_attrs = old_attrs[:]
    new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
    try:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
        yield
    finally:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)


class ReadthreadStdIn(threading.Thread):
    
    Ereignis = ''
    EreignisLock = threading.Lock()
        
    def __init__(self, serarg):
        threading.Thread.__init__(self)
        self.ser = serarg
        self.to_send = ''

    def run(self):
        ReadthreadStdIn.EreignisLock.acquire()
        while self.ser.isOpen():
            ReadthreadStdIn.EreignisLock.release()
            ch = sys.stdin.read(1)
            if not ch or ch == chr(4):
                ReadthreadStdIn.EreignisLock.acquire()
                ReadthreadStdIn.Ereignis = 'exit'
                self.ser.close()
                ReadthreadStdIn.EreignisLock.release()
                break
            self.to_send = self.to_send + ch
            
            if ord(ch) == 10:
                ReadthreadStdIn.EreignisLock.acquire()
                if self.ser.isOpen():
                    self.ser.write(self.to_send)
                ReadthreadStdIn.EreignisLock.release()
                self.to_send = ''
            print ch,
            sys.stdout.softspace=False
            time.sleep(0.07)
            ReadthreadStdIn.EreignisLock.acquire()
        print '\n EXIT \n',
        sys.stdout.softspace=False

def main(argv):
    
    print 'Number of arguments:', len(sys.argv)
    print 'Argument List:', str(sys.argv)


    ser = serial.Serial()

    ser.port = argv[0]

    ser.baudrate = argv[1]

    ser.bytesize = serial.EIGHTBITS #number of bits per bytes

    ser.parity = serial.PARITY_NONE #set parity check: no parity

    ser.stopbits = serial.STOPBITS_ONE #number of stop bits

    ser.timeout = 0             #non-block read

    ser.xonxoff = False     #disable software flow control

    ser.rtscts = False     #disable hardware (RTS/CTS) flow control

    ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control

    ser.writeTimeout = 2     #timeout for write

    ser.open()
    
    mythread = ReadthreadStdIn(ser)
    mythread.start()

    print 'exit with ^C or ^D'
    with raw_mode(sys.stdin):
        try:
            ReadthreadStdIn.EreignisLock.acquire()
            while ser.isOpen():
                ser_input = ser.read()
                ReadthreadStdIn.EreignisLock.release()
                while ser_input is not '':
                    print ser_input,
                    sys.stdout.softspace=False
                    ReadthreadStdIn.EreignisLock.acquire()
                    if ser.isOpen():
                        ser_input = ser.read()
                    ReadthreadStdIn.EreignisLock.release()
                time.sleep(0.05)
                ReadthreadStdIn.EreignisLock.acquire()
                ereignis = ReadthreadStdIn.Ereignis
                ReadthreadStdIn.EreignisLock.release()
                if ereignis is 'exit':
                    break
                ReadthreadStdIn.EreignisLock.acquire()
        except (KeyboardInterrupt, EOFError):
            pass


    ser.close()
    

if __name__ == "__main__":
    main(sys.argv[1:])

