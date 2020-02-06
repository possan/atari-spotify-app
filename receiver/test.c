// See: https://www.atariarchives.org/mapping/memorymap.php
// See: https://www.atarimax.com/freenet/freenet_material/12.AtariLibrary/2.MiscellaneousTextFiles/showarticle.php?42
// See: https://atariage.com/forums/topic/279135-sio-from-basic/
// See: https://atariage.com/forums/topic/298324-atariwifi-an-atari-network-adapter/page/5/
// See: http://www.bighole.nl/pub/mirror/homepage.ntlworld.com/kryten_droid/Atari/800XL/atari_hw/atari_hw_02c.htm
// See: https://www.atarimax.com/freenet/freenet_material/5.8-BitComputersSupportArea/7.TechnicalResourceCenter/showarticle.php?60

#include <atari.h>
#include <stdio.h>
#include <stdlib.h>
#include <conio.h>
#include <6502.h>

// These are supposed to remap the characters, didn't get any of the m to work so the remapping is happening in the sender instead.
// #include <atari_atascii_charmap.h>
// #include <atari_screen_charmap.h>


#define SAVMSC *(unsigned int *) 88
#define NMIEN  *(unsigned char *) 0xD40E
#define SDMCTL *(unsigned char *) 559
#define SDLSTL *(unsigned int *) 560
#define VDSLST *(unsigned int *) 0x200
#define STICK0 ((unsigned char *) 0x0278)
#define STRIG0 ((unsigned char *) 0x0284)

#define CH ((unsigned char *) 0x02FC)
#define KBCODE ((unsigned char *) 0xD209)
#define KB_LEFT 134
#define KB_RIGHT 135
#define KB_UP 142
#define KB_DOWN 143
#define KB_A 63
#define KB_D 58
#define KB_S 62
#define KB_RETURN 12
#define KB_SPACE 33

#define SKSTAT ((unsigned char *) 0xD20F)
#define SKSTAT_KEYDOWN_MASK 4
#define SKREST ((unsigned char *) 0xD20A)
#define SERIN ((unsigned char *) 0xD20D)
#define SEROUT ((unsigned char *) 0xD20D)
#define SKCTL ((unsigned char *) 0xD20F)
#define SSKCTL ((unsigned char *) 0x0233)
#define DDEVIC ((unsigned char *) 0x0300)
#define DUNIT ((unsigned char *) 0x0301)
#define DCOMND ((unsigned char *) 0x0302)
#define DSTATS ((unsigned char *) 0x0303)
#define DBUFPTR ((unsigned short *) 0x0304)
#define DBUFLO ((unsigned char *) 0x0304)
#define DBUFHI ((unsigned char *) 0x0305)
#define DTIMPTR ((unsigned short *) 0x0306)
#define DTIMLO ((unsigned char *) 0x0306)
#define DTIMHI ((unsigned char *) 0x0307)
#define DBYTPTR ((unsigned short *) 0x0308)
#define DBYTLO ((unsigned char *) 0x0308)
#define DBYTHI ((unsigned char *) 0x0309)
#define DAUX1 ((unsigned char *) 0x030A)
#define DAUX2 ((unsigned char *) 0x030B)
#define SIOV ((void *) 0xE459)



char dl[] = {
    DL_DLI(0),
    DL_BLK8,
    DL_BLK8,
    DL_LMS(DL_CHR40x8x1), 0, 0,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_CHR40x8x1,
    DL_JVB,
    0,
    0
};



unsigned char *screenptr;
unsigned char kbmask, lastkbmask = 1;
unsigned char joy, lastjoy = 0;

unsigned char outbuf[5] = { 0, 0, 0, 0, 0 };
unsigned char inbuf[70] = { 0, };

unsigned char cursor_column = 0;
unsigned char cursor_row = 0;

extern unsigned char coltab1 = 0;
extern unsigned char coltab2 = 0;
extern unsigned char coltab3 = 0;
extern unsigned char coltab4 = 0;
extern unsigned char coltab5 = 0;

unsigned char term_escape_counter = 0;
unsigned char term_command_length = 1;
unsigned char term_escape_buffer[20] = { 0, };

// Externals from assembler code
void sio_wrapper(void);
void dli(void);



void send_payload(unsigned char b0, unsigned char b1) {
    outbuf[0] = b0;
    outbuf[1] = b1;

    *DDEVIC = 0x50; // R1
    *DUNIT = 0x1;
    *DCOMND = 0x50; // 'W';
    *DBUFPTR = &outbuf;
    *DTIMHI = 1;
    *DTIMLO = 0;
    *DBYTPTR = 2;
    *DAUX1 = 2;
    *DAUX2 = 0;
    *DSTATS = 0x80;
    sio_wrapper();

    // Trial and error, re-enabling the colors(?)
    NMIEN = 0xC0;
    SDMCTL = 34;
}



void joy_scan() {
    joy = (*STICK0 & 0x0F) | (*STRIG0 << 4);
    // if (joy == lastjoy) {
    // return;
    // }

    if ((joy & JOY_LEFT_MASK) == 0 && (lastjoy & JOY_LEFT_MASK) != 0) {
        send_payload('J', 'L');
    }

    if ((joy & JOY_RIGHT_MASK) == 0 && (lastjoy & JOY_RIGHT_MASK) != 0) {
        send_payload('J', 'R');
    }

    if ((joy & JOY_UP_MASK) == 0 && (lastjoy & JOY_UP_MASK) != 0) {
        send_payload('J', 'U');
    }

    if ((joy & JOY_DOWN_MASK) == 0 && (lastjoy & JOY_DOWN_MASK) != 0) {
        send_payload('J', 'D');
    }

    if ((joy & 16) == 0 && (lastjoy & 16) != 0) {
        send_payload('J', 'B');
    }

    lastjoy = joy;
}



void kb_scan() {
    unsigned char C;

    kbmask = (*SKSTAT & SKSTAT_KEYDOWN_MASK);
    if (kbmask == lastkbmask) {
        return;
    }

    lastkbmask = kbmask;
    if (kbmask != 0) {
        return;
    }

    C = *KBCODE;
    send_payload('K', *KBCODE);
}



void term_handle_escape(unsigned char *escapeseq, unsigned char _len) {
    unsigned short o;
    unsigned char i;
    // cprintf(" CMD=%c ", escapeseq[0] );
    // cprintf(" LEN=%d ", _len );
    // cprintf(" BUF=[%d %d %d ..] ", escapeseq[0], escapeseq[1], escapeseq[2] );
    if (escapeseq[0] == 'C' && _len == 1) {
        // clear screen + home cursor
        cursor_column = 0;
        cursor_row = 0;
        for(o = 0; o<40*25; o++) {
            screenptr[o] = 0;
        }
    } else if (escapeseq[0] == 'G' && _len == 3) {
        // move cursor
        cursor_column = escapeseq[1] % 40;
        cursor_row = escapeseq[2] % 25;
    } else if (escapeseq[0] == 'P' && _len == 6) {
        // color palette
        coltab1 = escapeseq[1];
        coltab2 = escapeseq[2];
        coltab3 = escapeseq[3];
        coltab4 = escapeseq[4];
        coltab5 = escapeseq[5];
    // } else {
        // cprintf(" [ERR] " );
    }
}



void term_receive_char(unsigned char ch) {
    unsigned char i;
    // cprintf(" ch=%d ", ch);
    if (term_escape_counter == 1) {
        // do nothing, just consume first character.
        term_escape_buffer[0] = ch;
        term_command_length = 0;
        if (ch == 'C') {
            term_command_length = 1;
        }
        else if (ch == 'G') {
            term_command_length = 3;
        }
        else if (ch == 'P') {
            term_command_length = 6;
        }
        // cprintf(" start c=%d len=%d ", ch, term_command_length);
        term_escape_counter = 2;
    } else if (term_escape_counter > 0) {
        // for the rest of the characters we check against a known length
        // cprintf(" e=%d ", term_command_length);
        term_escape_buffer[term_escape_counter - 1] = ch;
        ++term_escape_counter;

        if (term_escape_counter > term_command_length) {
            // cprintf(" ] ");
            term_handle_escape((unsigned char *)&term_escape_buffer, term_command_length);
            term_command_length = 0;
            term_escape_counter = 0;
        }
    } else if (ch == 0x1B) {
        term_escape_counter = 1;
        for(i=0; i<10; i++) {
            term_escape_buffer[i] = 0;
        }
        // cprintf(" ESC[ ");
    } else {
        screenptr[cursor_row * 40 + cursor_column] = ch;
        cursor_column ++;
        if (cursor_column >= 40) {
            cursor_column = 0;
            cursor_row ++;
            if (cursor_row >= 25) {
                cursor_row = 0;
            }
        }
    }
}



void term_receive_chars(unsigned char *chars, int len) {
    unsigned char *c = chars;
    unsigned char i;
    for(i=0; i<len; i++) {
        term_receive_char(*c ++);
    }
}



void ser_scan() {
    unsigned char len;

    *DDEVIC = 0x50; // R1
    *DUNIT = 0x1;
    *DCOMND = 'R';
    *DBUFPTR = &inbuf;
    *DTIMHI = 0;
    *DTIMLO = 1;
    *DBYTPTR = 65;
    *DAUX1 = 64;
    *DAUX2 = 0;
    *DSTATS = 0x40;

    sio_wrapper();

    // Trial and error, re-enabling the colors(?)
    NMIEN = 0xC0;
    SDMCTL = 34;

    // cprintf("R%d ", *DSTATS, *DBYTPTR, inbuf[0]);

    len = inbuf[0];
    if (len == 0 || len > 64) {
        return;
    }

    term_receive_chars((unsigned char *)&inbuf + 1, len);
}



void main(void) {
    unsigned char i, t, huecounter;
    unsigned short y, x, o, hue;
    unsigned char ret;

    // Set up the display
    dl[4] = (unsigned char) (SAVMSC % 256);
    dl[5] = (unsigned char) (SAVMSC / 256);
    dl[sizeof(dl)-2] = ((unsigned) &dl) % 256;
    dl[sizeof(dl)-1] = ((unsigned) &dl) / 256;
    SDLSTL = (unsigned int) &dl;
    VDSLST = (unsigned int) &dli;
    {
        unsigned char ptr0 = SAVMSC % 256;
        unsigned char ptr1 = SAVMSC / 256;
        unsigned short ptr2 = (ptr1 << 8) + ptr0;
        screenptr = (unsigned char *)ptr2;
    }
    NMIEN = 0xC0;
    SDMCTL = 0;
    SDMCTL = 34;

    // DEBUG ASCII TABLE
    // for(y=0; y<16; ++y) {
    //     o = y * 40;
    //     for(x=0; x<16; ++x) {
    //         screenptr[o] = y * 16 + x;
    //         o ++;
    //     }
    // }

    // Default colors
    coltab1 = 0;
    coltab2 = 0;
    coltab3 = 255;
    coltab4 = 0;
    coltab5 = 0;

    // Run some test code
    // term_receive_chars("\x1b" "C" "\x00", 3);
    term_receive_chars("\x1b" "G" "\x12" "\x0A", 4);
    term_receive_chars("l" "\x40" "ading", 7);
    // term_receive_chars("\x1b" "P" "\x10" "\x77" "\x10" "\x10" "\x10", 7);
    // term_receive_chars("hello world", 11);
    // term_receive_chars("\x1b" "G" "\x15" "\x09" "\x00", 6);
    // term_receive_chars("\x1b" "P" "\x30" "\x30" "\xFF" "\x30" "\x30", 7);

    send_payload('X', 'X'); // hello message

    t = 0;
    while(1) {
        // Display a small heartbeat
        if ((t & 255) < 4) {
            screenptr[23*40+39] = '\x40';
        } else {
            screenptr[23*40+39] = 0;
        }

        kb_scan();
        joy_scan();
        if ((t & 15) == 0) {
            ser_scan();
        }

        t ++;
    }
}
