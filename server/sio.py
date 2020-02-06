import os
import serial
import threading
import time
import random


SIO_ACK = 0x41 # A
SIO_NACK = 0x4E # N
SIO_COMPLETE = 0x43 # C
SIO_ERROR = 0x45 # E
US_PER_S = 1000000.0

# Constants from sio2bsd
BASIC_DELAY = 2000
POKEY_PAL_HZ = 1773447.0
POKEY_NTSC_HZ = 1789790.0
POKEY_AVG_HZ = (POKEY_NTSC_HZ + POKEY_PAL_HZ) / 2.0
POKEY_CONST = 7.1861
# From https://github.com/jzatarski/RespeQt/blob/2e50a405e5ee65c15bb36177351e7185ddac259c/serialport-unix.cpp 
SLEEP_FACTOR = 10000
FRAME_DELAY = 50.0 / 1000000.0
WRITE_DELAY = (1.0 * SLEEP_FACTOR) / 1000000.0
HANDSHAKE_DELAY = 500.0 / 1000000.0
COMP_DELAY = 800.0 / 1000000.0



diskimagedata = []
_sio_port = None
_sio_inputhandler = None
_sio_diskimage = None
_sio_restarthandler = None
_sio_resumehandler = None
_sio_outqueue = []
_sio_thread_alive = False
_sio_thread = None
port = None



def sio_setport(port):
    global _sio_port
    _sio_port = port



def sio_setdiskimage(path):
    global _sio_diskimage
    _sio_diskimage = path



def sio_setinputhandler(cb):
    global _sio_inputhandler
    _sio_inputhandler = cb



def sio_setrestarthandler(cb):
    global _sio_restarthandler
    _sio_restarthandler = cb



def sio_setresumehandler(cb):
    global _sio_resumehandler
    _sio_resumehandler = cb



def sio_write(data):
    global _sio_outqueue
    print ("Sio: Appending to output queue: %r" % (hexbytes(data)))
    _sio_outqueue += data



def sioChecksum(bytearrayinput):
    sum = 0
    for k in bytearrayinput:
        sum += k
        if sum > 255:
            sum -= 255
    return sum



def hexbytes(bytearrayinput):
    return ' '.join('%02x' % i for i in bytearrayinput)



def writeResponseBytes(bytearrayinput):
    checksum = sioChecksum(bytearrayinput)
    # print ("Writing bytes: %s (checksum %02x)" % (hexbytes(bytearrayinput), checksum))
    bytearrayinput.append(checksum)
    bytes = map(lambda x: chr(x), bytearrayinput)
    x = port.write(bytes)
    # print ("Wrote %d bytes" % (x))



def sendRaw(bytearrayinput):
    # print ("Sending raw: %s" % hexbytes(bytearrayinput))
    bytes = map(lambda x: chr(x), bytearrayinput)
    x = port.write(bytes)
    # print ("Wrote %d bytes" % (x))



def sendACK():
    d = (BASIC_DELAY*1000) / (POKEY_AVG_HZ/1000) / US_PER_S;
    # print ("delaying", d)
    time.sleep(d);
    sendRaw([SIO_ACK])



def sendNACK():
    sendRaw([SIO_NACK])



def sendComplete():
    time.sleep(WRITE_DELAY)
    sendRaw([SIO_COMPLETE])



def sendError():
    time.sleep(WRITE_DELAY)
    sendRaw([SIO_ERROR])



def sendResponse(bytearrayinput):
    checksum = sioChecksum(bytearrayinput)
    bytearrayinput.append(checksum)
    time.sleep(FRAME_DELAY)
    time.sleep(WRITE_DELAY)
    sendRaw(bytearrayinput)



def handleGetStatus(bytearrayinput):
    print ("Get status")
    status = [0, 0, 0, 0]
    status[0] = 8 # | 64 | 128
    status[1] = 0
    status[2] = 0
    status[3] = 1
    sendResponse(status)



def handleReadSector(bytearrayinput):
    global diskimagedata
    global _sio_diskimage
    global _sio_restarthandler
    global _sio_outqueue
    with open(_sio_diskimage, 'rb') as f:
        diskimagedata = bytearray(f.read())
        print ("Read %d bytes disk image" % (len(diskimagedata)))
    si = bytearrayinput[2] + (bytearrayinput[3] * 256)
    o = 16 + ((si - 1) * 128)
    print ("Read sector #%d (offset %d)" % (si, o))
    resp = diskimagedata[o:o+128]
    sendResponse(resp)
    if si == 1:
        # we requested the last sector, maybe
        print ("Requested first sector (restart handler)")
        _sio_outqueue = []
        if _sio_restarthandler:
            _sio_restarthandler()



def handleWritePercomBlock(bytearrayinput):
    print ("Write percom")



def readFromSerial(l):
    global port
    bytes = port.read(l)
    mapped = map(lambda x: ord(x), bytes)
    return mapped



def handleFloppyCommand(device):
    rest = readFromSerial(4)
    command = [device] + rest
    # print("Handling disk command: %s" % hexbytes(command))
    if len(command) <> 5:
        print("Invalid disk command: %s" % hexbytes(command))
        sendNACK()
        return
    if command[1] == 0x53:
        print("Get disk status command: %s" % hexbytes(command))
        sendACK()
        sendComplete()
        handleGetStatus(command)
    elif command[1] == 0x52:
        print("Read disk sector command: %s" % hexbytes(command))
        sendACK()
        sendComplete()
        handleReadSector(command)
    else:
        print("Invalid disk command: %s" % hexbytes(command))
        sendNACK()



def handleSerialPayload(bytes):
    if len(bytes) < 2:
        print ("Got invalid serial payload")
        return
    if bytes[0] == ord('K'):
        print ("Got keyboard press: %d" % bytes[1])
        _sio_inputhandler(bytes)
    elif bytes[0] == ord('J'):
        print ("Got joystick move: %d" % bytes[1])
        _sio_inputhandler(bytes)
    elif bytes[0] == ord('X'):
        if _sio_resumehandler:
           _sio_resumehandler()
    else:
        print ("Got unhandled serial payload: %s" % hexbytes(bytes))



# See (ack/complete): http://abbuc.de/~montezuma/Sio2BT%20Networking.pdf
def handleSerialCommand(device):
    global _sio_outqueue
    rest = readFromSerial(4)
    command = [device] + rest
    if len(command) <> 5:
        print("Invalid serial command (length): %s" % hexbytes(command))
        sendNACK()
        return
    if command[1] == 0x50:
        # print("Serial data write: %s" % hexbytes(command))
        sendACK()
        sendComplete()
        l = command[2]
        data = readFromSerial(l)
        handleSerialPayload(data)
        # print ("Got serial data: %s" % hexbytes(data))
        sendACK()
        # gotkey = True
    elif command[1] == 0x52:
        # print("Serial data read: %s" % hexbytes(command))
        sendACK()
        sendComplete()
        response = []
        l = len(_sio_outqueue)
        if l > 60:
            l = 60
        for k in range(l):
            popped = _sio_outqueue.pop(0)
            response.append(popped)
        for k in range(64):
            if (len(response) < 64):
                response.append(0)
        response = [l] + response

        # response.append(random.randint(1, 60))
        # for k in range(64):
        #     # if response
        #     response.append(k)
        # response = []
        if l > 0:
            print ("Sending serial data: %s" % hexbytes(response))
        sendResponse(response)
    else:
        print("Invalid serial command (command): %s" % hexbytes(command))
        sendNACK()



def handleFirstByte(firstbyte):
    if firstbyte[0] == 0x31:
        handleFloppyCommand(firstbyte[0])
    elif firstbyte[0] == 0x50:
        handleSerialCommand(firstbyte[0])
    else:
        # print("Invalid first byte: %s" % hexbytes(firstbyte))
        sendNACK()



def sio_thread():
    global _sio_thread_alive
    global _sio_port
    global port
    print("Opening serial port: %s" % _sio_port)
    try:
        port = serial.Serial(_sio_port, 19200, timeout=0.01, rtscts=0)
    except serial.SerialException, e:
        print("Failed to open port!", e)
        return
    print("Opened serial port.")
    while _sio_thread_alive:
        firstbyte = readFromSerial(1)
        if firstbyte:
            handleFirstByte(firstbyte)
    if port:
        print("Closing serial port...")
        port.close()



def sio_start():
    global _sio_thread
    global _sio_thread_alive
    _sio_thread_alive = True
    _sio_thread = threading.Thread(target = sio_thread)
    _sio_thread.start()



def sio_stop():
    global _sio_thread
    global _sio_thread_alive
    _sio_thread_alive = False
    _sio_thread.join()
