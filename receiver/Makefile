SYS=atari
CFLAGS=
CC=cc65
CL=cl65
AS=ca65
LD=ld65
TARGET_PATH := $(shell $(CL) --print-target-path)

all: receiver.xex receiver.atr

clean:
	rm -r receiver* test.o test.s

# run: receiver.xex
	# ~/Applications/Atari800MacX/Atari800MacX.app/Contents/MacOS/Atari800MacX receiver.xex

run: receiver.atr
	~/Applications/Atari800MacX/Atari800MacX.app/Contents/MacOS/Atari800MacX receiver.atr

test.s: test.c
	# $(CC) $(CFLAGS) -Ors --codesize 500 -T -g -t $(SYS) test.c
	$(CC) $(CFLAGS) -Ors -T -g -t $(SYS) test.c

intr.o: intr.s
	$(AS) intr.s

test.o: test.s
	$(AS) test.s

receiver.xex: test.o intr.o
	$(LD) -o receiver.xex -t $(SYS) -m receiver.map test.o intr.o $(SYS).lib

receiver.atr: receiver.xex
	# atrcopy receiver.atr create dos2sd+2.0s.atr
	# atrcopy receiver.atr add -o SER receiver.xex
	../mkatr/mkatr -x receiver.atr -b receiver.xex
