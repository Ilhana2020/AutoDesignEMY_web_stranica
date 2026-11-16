"""Pick the sharpest, well-exposed frame of each gallery video as its poster (crops letterbox bars)."""
import subprocess, glob, os, numpy as np
from PIL import Image, ImageFilter
D = 'src/static/media/gallery/'
for mp4 in sorted(glob.glob(D + '*.mp4')):
    name = os.path.basename(mp4)[:-4]
    dur = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',mp4]))
    tmp = '/tmp/pf'; os.makedirs(tmp, exist_ok=True)
    for f in glob.glob(tmp + '/*'): os.remove(f)
    subprocess.run(['ffmpeg','-v','error','-i',mp4,'-vf',f'fps={24/dur}', tmp + '/f%03d.png'], check=True)
    best, score = None, -1
    for f in sorted(glob.glob(tmp + '/*.png'))[1:-2]:
        im = Image.open(f).convert('L'); a = np.asarray(im, dtype=float)
        rows = a.mean(1); keep = rows > 18
        if keep.sum() < a.shape[0] * 0.5: continue
        a2 = a[keep]
        bright = a2.mean()
        if bright < 55 or bright > 225: continue
        lap = np.asarray(Image.fromarray(a2.astype('uint8')).filter(ImageFilter.FIND_EDGES), dtype=float).var()
        if lap > score: score, best = lap, f
    if not best: print('skip', name); continue
    im = Image.open(best).convert('RGB'); a = np.asarray(im.convert('L'), dtype=float)
    rows = np.where(a.mean(1) > 18)[0]; im = im.crop((0, rows[0], im.width, rows[-1] + 1))
    im.save(D + name + '.webp', 'WEBP', quality=80, method=6)
    print(name, os.path.basename(best), round(score))
