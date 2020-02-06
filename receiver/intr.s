  .include "atari.inc"

  .export _sio_wrapper
  .export _dli

  .import _coltab1
  .import _coltab2
  .import _coltab3
  .import _coltab4
  .import _coltab5

  .code

_dli:
  pha

  LDA _coltab1
  STA COLBK

  LDA _coltab2
  STA COLPF0

  LDA _coltab3
  STA COLPF1

  LDA _coltab4
  STA COLPF2

  LDA _coltab5
  STA COLPF3

  pla
  rti

_sio_wrapper:
  jsr SIOV
  rts
