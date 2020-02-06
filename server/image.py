import os
import random
import requests
import json
import math
from PIL import Image, ImageEnhance, ImageOps, ImageDraw

_cache = {}
chars = []
colors = []



def getpixelarray(im):
    arr = []
    o = 0
    for j in range(8):
        for i in range(8):
            arr.append(1 if im.getpixel((i, j)) > 100 else 0)
            o += 1
    # print ('getpixelarray %r' % (arr))
    return arr



def comparepixels(a, b):
    diff = 0
    for k in range(len(a)):
        if a[k] != b[k]:
            diff += 1
    return diff



def inittemplates():
    print("loading font and creating template")
    templateimage = Image.open('atascii_actual.png')
    # templateimage = Image.open('atascii.png')
    templateimage = templateimage.convert(mode='1', dither=Image.FLOYDSTEINBERG, palette=Image.ADAPTIVE, colors=3)
    o = 0
    for j in range(16):
        for i in range(16):
            x = i * 8
            y = j * 8
            ch = Image.new(mode='1', size=(8, 8), color=0)
            ch.paste(templateimage, (-x, -y))
            # ch.save('temp/ch-' + str(o) + '.png', 'PNG')
            chars.append({
                'index': o,
                'image': ch,
                'pixels': getpixelarray(ch)
            })
            o += 1
    paletteimage = Image.open('atari_palette.png')
    palettepx = paletteimage.load()
    for j in range(16):
        for i in range(5): # Not all of them
            c = palettepx[j, i][0:3]
            print ("palette #%d = %r" % (o, c))
            colors.append({'i': j * 16 + i, 'c': c})



def rankCompare(a, b):
    return a['d'] - b['d']



def rankChars(inputslice, randomness):
    pixels = getpixelarray(inputslice)
    # print ('rank input pixels %r' % (pixels))
    ranked = []
    for ch in chars:
        diff = comparepixels(pixels, ch['pixels'])
        ranked.append({'i': ch['index'], 'd': diff, 'm': ch['image']})
    ranked.sort(rankCompare)
    i = random.randint(0, randomness)
    i -= 4
    if i < 0:
        i = 0
    return ranked[i]



def image_init():
    inittemplates()



def image_get_from_disk(path, randomness=6):
    tempfn3 = 'temp/' + os.path.basename(path) + '-converted.json'
    if os.path.exists(tempfn3):
        print ("Image: Loading cached image: " + tempfn3)
        with open(tempfn3, 'r') as f:
            ret = json.loads(f.read())
            return ret

    print ("Image: Loading image: " + path)
    im = Image.open(path)

    cols = im.width >> 3
    rows = im.height >> 3
    print ("Image: Size, %d x %d cells" % (cols, rows))

    tempoutput = Image.new(mode='1', size=(8*cols, 8*rows), color=0)

    outputrows = []
    for j in range(rows):
        outputrow = []
        for i in range(cols):
            x = i * 8
            y = j * 8
            tempimage = Image.new(mode='1', size=(8, 8), color=0)
            tempimage.paste(im, (-x, -y))
            ranked = rankChars(tempimage, randomness)
            tempoutput.paste(ranked['m'], (x, y))
            xx = ranked['i']
            # in ATASCII table
            if xx != 27:
                outputrow.append(xx)
            else:
                outputrow.append(0)
        outputrows.append(outputrow)
    tempfn2 = 'temp/' + os.path.basename(path) + '-converted.png'

    print ('Image: Writing temporary output to ' + tempfn2)
    tempoutput.save(tempfn2, 'PNG')
    print ('')

    ret = {
        'rows': outputrows
    }

    with open(tempfn3, 'w') as f:
        f.write(json.dumps(ret))

    return ret



def image_get_and_convert(url, id, randomness=6):
    global _cache
    if url in _cache:
        return _cache[url]

    # Download from CDN
    imagepath = 'temp/' + id + '-orig.jpg'
    print("Image: Downloading image from: %s" % (url))
    r2 = requests.get(url, allow_redirects=True)

    print("Image: Saving original to: %s" % (imagepath))
    open(imagepath, 'wb').write(r2.content)

    imagepath2 = 'temp/' + id + '-prep.png'
    # Preprocess a bit, normalize colors etc.
    im = Image.open(imagepath)
    enhancer = ImageEnhance.Color(im); im = enhancer.enhance(0.2)
    im.thumbnail((18 * 8, 18 * 8), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=5);
    im = im.convert(mode='1', dither=Image.FLOYDSTEINBERG, palette=Image.ADAPTIVE, colors=2)
    print ('Image: Writing preprocessed image to: ' + imagepath2)
    im.save(imagepath2, 'PNG')

    ret = image_get_from_disk(imagepath2, randomness)
    _cache[url] = ret
    return ret



def image_find_closest_bgcolor(rgb):
    global colors
    ranked = []
    for i in range(len(colors)):
        c = colors[i]
        crgb = c['c']
        dr = crgb[0] - rgb[0]
        dg = crgb[1] - rgb[1]
        db = crgb[2] - rgb[2]
        ds = dr*dr + dg*dg + db*db
        ds += random.randint(0, 10)
        d = math.sqrt(ds)
        ranked.append({
            'i': c['i'],
            'c': crgb,
            'ds': ds,
            'd': ds
        })

    ranked.sort(rankCompare)

    print("ranked colors: %r" % ranked)

    i = random.randint(0, 4)
    i -= 4
    if i < 0:
        i = 0

    print("picked color: %r" % ranked[i])
    return ranked[i]['i']
