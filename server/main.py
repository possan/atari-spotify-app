import os
import sys
import fileinput
import json

from spot import *
from sio import *
from ui import *
from image import *



PORT = '/dev/tty.usbserial-AB0JJCSY'
DISKIMAGE = '../receiver/receiver.atr'



def handle_input(bytes):
    print ("SIO: Got input: %r" % (bytes))
    if bytes[0] == ord('K'):
        print ("Got keyboard press: %d" % bytes[1])
        if bytes[1] == 12 or bytes[1] == 33: # ENTER or SPACE
            ui_nav(UI_NAV_BUTTON)
        elif bytes[1] == 6 or bytes[1] == 63: # LEFT or A
            ui_nav(UI_NAV_LEFT)
        elif bytes[1] == 7 or bytes[1] == 58: # RIGHT or D
            ui_nav(UI_NAV_RIGHT)
        elif bytes[1] == 14 or bytes[1] == 46: # UP or W
            ui_nav(UI_NAV_UP)
        elif bytes[1] == 15 or bytes[1] == 62 or bytes[1] == 22: # DOWN, S or X
            ui_nav(UI_NAV_DOWN)
        elif bytes[1] == 28 or bytes[1] == 52: # ESC or DELETE
            ui_nav(UI_NAV_BACK)
    elif bytes[0] == ord('J'):
        print ("Got joystick move: %d" % bytes[1])
        if bytes[1] == ord('L'):
            ui_nav(UI_NAV_LEFT)
        elif bytes[1] == ord('R'):
            ui_nav(UI_NAV_RIGHT)
        elif bytes[1] == ord('U'):
            ui_nav(UI_NAV_UP)
        elif bytes[1] == ord('D'):
            ui_nav(UI_NAV_DOWN)
        elif bytes[1] == ord('B'):
            ui_nav(UI_NAV_BUTTON)
    else:
        print ("Got unhandled serial payload: %s" % hexbytes(bytes))



def ui_output(bytes):
    print ("UI: Write output: %r" % (bytes))
    sio_write(bytes)



def handle_state(state):
    print ("SPOT: Got state: %s" % (json.dumps(state)))
    ui_update_npv_fromstate(state)



def handle_restart():
    print ("SIO: Handle restart")
    ui_reset()



def handle_resume():
    print ("SIO: Handle resume")
    ui_resume()



image_init()

sio_setport(PORT)
sio_setdiskimage(DISKIMAGE)
sio_setinputhandler(handle_input)
sio_setrestarthandler(handle_restart)
sio_setresumehandler(handle_resume)
sio_start()

spot_setstatehandler(handle_state)
spot_init()

ui_setoutputhandler(ui_output)
ui_reset()

while True:
    s = None
    try:
        s = raw_input("Input: [ L(eft), R(ight), U(p), D(own), B(utton), Q(uit), CTRL-C ] ").upper().strip()
    except KeyboardInterrupt, e:
        break
    print("Got " + s)
    if s == 'L':
        handle_input([ord('J'), ord('L')])
    elif s == 'R':
        handle_input([ord('J'), ord('R')])
    elif s == 'U':
        handle_input([ord('J'), ord('U')])
    elif s == 'D':
        handle_input([ord('J'), ord('D')])
    elif s == 'B':
        handle_input([ord('J'), ord('B')])
    elif s == 'Q':
        break

sio_stop()
spot_kill()
