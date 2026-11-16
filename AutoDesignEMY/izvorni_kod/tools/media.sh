#!/bin/sh
# Encodes website video versions from the graded masters.
SRC=/mnt/user-data/outputs/AutoDesignEMY_video/web_stranica
OUT=/home/claude/emy/src/static/media
mkdir -p $OUT/gallery $OUT/hero
for f in $SRC/*.mp4; do
  n=$(basename $f .mp4)
  w=$(ffprobe -v error -select_streams v -show_entries stream=width -of csv=p=0 $f)
  if [ "$w" -gt 1100 ]; then S="scale=1280:-2"; else S="scale=720:-2"; fi
  ffmpeg -v error -y -i $f -vf "$S" -an -c:v libx264 -preset medium -crf 27 -profile:v high -pix_fmt yuv420p -movflags +faststart $OUT/gallery/$n.mp4
  ffmpeg -v error -y -i $SRC/${n}_poster.jpg -vf "$S" -q:v 80 $OUT/gallery/${n}.webp
  echo enc $n
done
# hero loop: 4 portrait segments, 6.5 s each, crossfaded
A=$SRC/01_volan_vw_alcantara_koza.mp4; B=$SRC/16_enterijer_sjedista_vrata.mp4; C=$SRC/17_tapacir_vrata.mp4; D=$SRC/05_volan_mercedes_amg.mp4
ffmpeg -v error -y -ss 0.5 -t 7 -i $A -ss 3 -t 7 -i $B -ss 2 -t 7 -i $C -ss 12 -t 7 -i $D -filter_complex "
[0:v]scale=720:1280,setsar=1,fps=30[a];[1:v]scale=720:1280,setsar=1,fps=30[b];[2:v]scale=720:1280,setsar=1,fps=30[c];[3:v]scale=720:1280,setsar=1,fps=30[d];
[a][b]xfade=transition=fade:duration=0.6:offset=6.4[ab];[ab][c]xfade=transition=fade:duration=0.6:offset=12.8[abc];[abc][d]xfade=transition=fade:duration=0.6:offset=19.2[v]" -map "[v]" -an -c:v libx264 -preset slow -crf 28 -pix_fmt yuv420p -movflags +faststart $OUT/hero/hero.mp4
ffmpeg -v error -y -ss 4 -i $OUT/hero/hero.mp4 -frames:v 1 -q:v 80 $OUT/hero/hero.webp
ffmpeg -v error -y -ss 4 -i $OUT/hero/hero.mp4 -frames:v 1 -q:v 4 $OUT/hero/hero.jpg
echo HERO DONE
