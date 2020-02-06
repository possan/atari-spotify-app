from spot import *
from image import *
import unidecode


UI_NAV_LEFT = 1
UI_NAV_RIGHT = 2
UI_NAV_UP = 3
UI_NAV_DOWN = 4
UI_NAV_BUTTON = 5
UI_NAV_BACK = 6
UI_NAV_ANY = 100

SCREEN_LOGO = 1
SCREEN_NPV = 2

SEL_BACK = 0
SEL_PREV = 1
SEL_PLAYPAUSE = 2
SEL_NEXT = 3
SEL_TOTAL = 4

ESC = 27


_output_paused = False
_output = None
_bg = 0
_fg = 0
_pin = ''
_screen = SCREEN_LOGO
_sel = 0
_playing = False
_trackuri = ''
_albumuri = ''



def ui_setoutputhandler(cb):
    global _output
    _output = cb

def ui_write(data):
    global _output
    global _output_paused
    if _output_paused:
        print("UI: Queueing output: %r" % (data))
        return
    print("UI: Sending output: %r" % (data))
    if _output:
        _output(data)



def ui_clear():
    print("UI: Send clear screen")
    ui_write([ ESC, ord('C') ])

def ui_fade_out():
    pass

def ui_fade_in(bg, fg):
    _bg = bg
    _fg = fg

def ui_fade(colortables):
    print("UI: Color tables: %r" % (colortables))



def ui_term_emptystring(l):
    arr = []
    for k in range(l):
        arr.append(0)
    return arr

def ascii_to_atascii(ch):
    # See: https://www.ascii-code.com/
    # See: https://www-alt.akk.org/~flo/ATASCII.pdf
    # See: https://en.wikipedia.org/wiki/ATASCII

    if ch >= 0x20 and ch < 0x60:
        ch = ch - 0x20

    return ch

def ui_cleanstring(s, maxlen=30):
    s = unidecode.unidecode(s)
    if len(s) > maxlen:
        s = s[0:maxlen]
    return s

def ui_centerstring(s, width=30):
    s = s.center(width, ' ')
    return s

def ui_term_convertascii(s):
    print('Converting input string "%s"' % s)
    try:
        arr = [ord(ch) for ch in s if ord(ch) < 128]
        print('Byte array %r' % arr)
        arr = map(lambda x: ascii_to_atascii(x), arr)
        print('Byte array %r' % arr)
    except Exception, e:
        print ("Exception", e)
        arr =  []
    return arr

def ui_term_gotoxy(x, y):
    return [ ESC, ord('G'), x, y ]

def ui_term_invert(inp):
    return [c + 128 for c in inp]

def ui_clear_npv():
    global _trackuri
    global _albumuri
    global _sel
    _trackuri = ''
    _albumuri = ''
    _sel = 1
    print("UI: Clear and draw npv screen")

def ui_update_npv_fromstate(state):
    global _screen
    global _playing
    global _albumuri
    global _trackuri
    if _screen != SCREEN_NPV:
        return
    _playing = state['is_playing']
    ctx = state['context']
    track = state['item']
    if track['uri'] != _trackuri:
        _trackuri = track['uri']
        trackname = track['name']
        artistname = ''
        if len(track['artists']) > 0:
            artistname = track['artists'][0]['name']
        ui_update_npv_trackinfo(trackname, artistname)
        ui_update_npv_buttons()
    album = track['album']
    if album['uri'] != _albumuri:
        _albumuri = album['uri']
        imageurl = album['images'][0]['url']
        img = image_get_and_convert(imageurl, album['uri'])
        col = spot_get_colors(imageurl)
        if img and col:
            ui_update_npv_cover(img, col)

def ui_update_npv_contextinfo(contextname):
    global _screen
    if _screen != SCREEN_NPV:
        return
    print("UI: Draw context: %r" % (contextname))
    # ui_write(ui_term_gotoxy(2, 2) + ui_term_emptystring(32))
    # ui_write(ui_term_gotoxy(2, 2) + ui_term_convertascii(artistname, 30))

def ui_update_npv_trackinfo(trackname, artistname):
    global _screen
    if _screen != SCREEN_NPV:
        return
    print("UI: Draw track: %s >> %s" % (trackname, artistname))
    ui_write(ui_term_gotoxy(1, 20) + ui_term_emptystring(38))
    ui_write(ui_term_gotoxy(1, 20) + ui_term_convertascii(ui_centerstring(ui_cleanstring(trackname, 38), 38)))

    ui_write(ui_term_gotoxy(1, 21) + ui_term_emptystring(38))
    ui_write(ui_term_gotoxy(1, 21) + ui_term_convertascii(ui_centerstring(ui_cleanstring(artistname, 38), 38)))

def ui_update_npv_cover(cover, dominantcolor):
    global _screen
    if _screen != SCREEN_NPV:
        return
    print("UI: Draw cover: %r %r" % (cover, colors))

    bghue = image_find_closest_bgcolor(dominantcolor)
    ui_write([ESC, ord('P'), bghue, bghue, 255, bghue, bghue])
    # // term_receive_chars("\x1b" "P" "\x30" "\x30" "\xFF" "\x30" "\x30", 7);

    for i in range(len(cover['rows'])):
        row = cover['rows'][i]
        ui_write(ui_term_gotoxy(11, i+1) + row)


def ui_term_button(label, selected):
    if selected:
        return [0x48] + ui_term_invert(ui_term_convertascii(label)) + [0xC8]
    return ui_term_convertascii(' ' + label + ' ')


def ui_update_npv_buttons():
    global _sel
    global _playing
    print("UI: Rendering buttons, nav=%d, playing=%d" % (_sel, _playing))

    ui_write(ui_term_gotoxy(0, 0) + ui_term_emptystring(20))
    # ui_write(ui_term_gotoxy(2, 22) + ui_term_emptystring(36))
    # ui_write(ui_term_gotoxy(5, 21) + ui_term_emptystring(6))
    # ui_write(ui_term_gotoxy(5, 22) + ui_term_emptystring(6))
    # ui_write(ui_term_gotoxy(15, 21) + ui_term_emptystring(6))
    # ui_write(ui_term_gotoxy(15, 22) + ui_term_emptystring(6))
    # ui_write(ui_term_gotoxy(25, 20) + ui_term_emptystring(6))
    # ui_write(ui_term_gotoxy(25, 21) + ui_term_emptystring(6))
    # ui_write(ui_term_gotoxy(25, 22) + ui_term_emptystring(6))

    ui_write(ui_term_gotoxy(0, 0) + ui_term_button(' < BACK ', _sel == SEL_BACK))
    ui_write(ui_term_gotoxy(6, 23) + ui_term_button(' PREV ', _sel == SEL_PREV))
    ui_write(ui_term_gotoxy(16, 23) + ui_term_button(' STOP ' if _playing else ' PLAY ', _sel == SEL_PLAYPAUSE))
    ui_write(ui_term_gotoxy(26, 23) + ui_term_button(' NEXT ', _sel == SEL_NEXT))


def ui_clear_logo():
    print("UI: Clear and draw logo screen")

    logo = image_get_from_disk('splashlogo.png', 0)
    # print(logo)

    # ui_write([ESC, ord('P'), 0x47, 0x0F])
    # ui_write([ESC, ord('P'), 0x47, 0xFF]) # brown logo, light bg

    # BBG, F1, UNUSED, FBG, UNUSED

    # ui_write([ESC, ord('P'), 0x2F, 0x6F, 0x0F, 0x4F, 0xF0])
    ui_write(ui_term_gotoxy(0, 0) + ui_term_emptystring(20))

    ui_write([ESC, ord('P'), 0xB0, 0xB0, 0xB8, 0xB0, 0xB0]) # Greenish

    ui_write(ui_term_gotoxy(0, 0) + ui_term_emptystring(20))

    for i in range(len(logo['rows'])):
        row = logo['rows'][i]
        ui_write(ui_term_gotoxy(2, i+4) + row)

    # ui_write(ui_term_gotoxy(3,  3) + ui_term_convertascii('ABC abc'))
    # ui_write(ui_term_gotoxy(3,  5) + ui_term_convertascii('012 ! - # *'))

    # ui_write(ui_term_gotoxy(6,  9) + ui_term_convertascii(' xxx                   '))
    # ui_write(ui_term_gotoxy(6, 10) + ui_term_convertascii('xx  x yxzy    z   yy   '))
    # ui_write(ui_term_gotoxy(6, 11) + ui_term_convertascii('xxx x yy yyzy yyyy yy y'))
    # ui_write(ui_term_gotoxy(6, 12) + ui_term_convertascii('xxxxx yz y zyyy yyy  yy'))
    # ui_write(ui_term_gotoxy(6, 13) + ui_term_convertascii(' xxx                   '))

    ui_write(ui_term_gotoxy(6, 20) + ui_term_convertascii('Press SPACE or FIRE to start'))





def ui_start():
    ui_clear()
    ui_clear_splash()
    ui_fade_in()



def ui_switch_to_npv():
    global _screen
    global _sel
    _screen = SCREEN_NPV
    _sel = SEL_PLAYPAUSE
    ui_clear()
    ui_clear_npv()
    ui_update_npv_buttons()
    ui_write(ui_term_gotoxy(31,  0) + [0x60] + ui_term_convertascii('Spotify'))
    ui_fade([ [], [], [], [] ])

def ui_switch_to_logo():
    global _screen
    _screen = SCREEN_LOGO
    ui_clear()
    ui_clear_logo()
    ui_fade([ [], [], [], [] ])



def ui_step():
    pass



def ui_nav_logo(d):
    print("UI: Navigate: %d" % (d))
    if d == UI_NAV_BUTTON or d >= UI_NAV_ANY:
        ui_switch_to_npv()
        spot_requeststate()



def ui_nav_npv(d):
    global _sel
    global _playing
    print("UI: Navigate: %d" % (d))
    if d == UI_NAV_LEFT or d == UI_NAV_UP:
        _sel -= 1
        _sel = (_sel + SEL_TOTAL) % SEL_TOTAL
        ui_update_npv_buttons()
    elif d == UI_NAV_RIGHT or d == UI_NAV_DOWN:
        _sel += 1
        _sel %= SEL_TOTAL
        ui_update_npv_buttons()
    elif d == UI_NAV_BUTTON:
        if _sel == SEL_PREV:
            spot_previous()
            ui_update_npv_buttons()
        elif _sel == SEL_PLAYPAUSE:
            if _playing:
                spot_pause()
            else:
                spot_play()
            ui_update_npv_buttons()
        elif _sel == SEL_NEXT:
            spot_next()
            ui_update_npv_buttons()
        elif _sel == SEL_BACK:
            ui_switch_to_logo()



def ui_nav(d):
    global _screen
    print("UI: Navigate: %d" % (d))
    if _screen == SCREEN_LOGO:
        ui_nav_logo(d)
    elif _screen == SCREEN_NPV:
        ui_nav_npv(d)


def ui_reset():
    global _ui_output_paused
    _ui_output_paused = True

def ui_resume():
    global _ui_output_paused
    _ui_output_paused = False
    ui_switch_to_logo()
    ui_write([])


