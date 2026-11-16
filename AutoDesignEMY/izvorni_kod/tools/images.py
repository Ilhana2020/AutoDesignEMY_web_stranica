"""Builds optimized, responsive images for the website from the original photos."""
from PIL import Image, ImageOps
import json, os
U = '/mnt/user-data/uploads/'
P = '/mnt/user-data/outputs/AutoDesignEMY_video/web_stranica/'
OUT = '/home/claude/emy/src/static/img/'
os.makedirs(OUT, exist_ok=True)
WIDTHS = [480, 960, 1440]

photos = {
    # name: (source, crop box or None)
    'volan-mercedes-amg-tirkiz': (U + '3b32b7a6-image.png', (0, 0, 596, 762)),  # crop removes Instagram UI
    'volan-vw-alcantara-koza': (U + '5f09b937-image.jpg', None),
    'volan-mercedes-koza': (U + 'f417dc2d-image.jpg', None),
    'volan-bmw-m-alcantara': (U + '84777cf4-image.jpg', None),
    'volan-audi-alcantara': (U + '64c0c494-image.jpg', None),
    'volan-bmw-plava-oznaka': (U + '1179a961-image.jpg', None),
    'volan-bmw-u-vozilu': (U + '1a99be7c-image.jpg', None),
    'sjediste-sace': (P + '16_enterijer_sjedista_vrata_poster.jpg', None),
    'tapacir-vrata-sace': (P + '17_tapacir_vrata_poster.jpg', None),
    'sjedista-romb': (P + '13_sjedista_romb_crveni_konac_poster.jpg', None),
}
swatches = {
    'mat-alcantara': (U + '84777cf4-image.jpg', (120, 380, 420, 680)),
    'mat-perforirana-koza': (U + '1179a961-image.jpg', (130, 1050, 530, 1450)),
    'mat-glatka-perforirana': (U + 'f417dc2d-image.jpg', (60, 560, 330, 830)),
    'mat-romb': (P + '13_sjedista_romb_crveni_konac_poster.jpg', (700, 250, 1100, 650)),
    'mat-sace': (P + '17_tapacir_vrata_poster.jpg', (300, 250, 800, 750)),
}
manifest = {}

def save_set(name, im, widths):
    im = ImageOps.exif_transpose(im).convert('RGB')
    out = {'w': im.width, 'h': im.height, 'webp': [], 'jpg': None}
    for w in sorted(set(min(w, im.width) for w in widths)):
        r = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        fn = f'{name}-{r.width}.webp'
        r.save(OUT + fn, 'WEBP', quality=78, method=6)
        out['webp'].append([fn, r.width])
    mid = min(960, im.width)
    r = im if im.width <= mid else im.resize((mid, round(im.height * mid / im.width)), Image.LANCZOS)
    out['jpg'] = f'{name}-{r.width}.jpg'
    r.save(OUT + out['jpg'], 'JPEG', quality=80, optimize=True, progressive=True)
    manifest[name] = out

for name, (src, box) in photos.items():
    im = Image.open(src)
    if box: im = im.crop(box)
    save_set(name, im, WIDTHS)
for name, (src, box) in swatches.items():
    im = Image.open(src).crop(box).resize((400, 400), Image.LANCZOS)
    save_set(name, im, [400])

# social sharing image (1200x630) and favicon
og = Image.open(P + '13_sjedista_romb_crveni_konac_poster.jpg').convert('RGB')
og = ImageOps.fit(og, (1200, 630), Image.LANCZOS); og.save(OUT + 'og-image.jpg', quality=82)
json.dump(manifest, open('/home/claude/emy/src/images.json', 'w'), indent=1)
print(len(manifest), 'image sets')
