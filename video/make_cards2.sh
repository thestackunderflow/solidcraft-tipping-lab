#!/usr/bin/env sh
# Card pictures at the split slide's picture box shape (1632 x 1200 = 2x the engine's 816 x 600), every label >= 70 px
# (>= 35 px on screen), at most 4 labels, no in-picture caption (the engine's imageCaption carries it). Script gate
# (teacher MUST 1, producer SHOULD). Needs ffmpeg + DejaVu (video-qa:2):
#   docker run --rm -v <lab>:/work -w /work video-qa:2 sh video/make_cards2.sh
set -eu
F=video/frames
B=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
RED=0xb71c1c; GREEN=0x1b5e20; INK=0x1f2937; BG=0xeceff4; BLUE=0x1d4ed8; AMBER=0xb45309
S=1632x1200
# A. hook card: the same stand, solid vs sliced
ffmpeg -v error -y -i $F/side-p210-solid.png -i $F/side-p210-sliced.png -filter_complex "\
[0:v]scale=-2:960[a];[1:v]scale=-2:960[b];color=c=$BG:s=$S[bg];[bg][a]overlay=70:200[t];[t][b]overlay=880:200,\
drawtext=fontfile=$B:text='✓ 156 g':fontcolor=$GREEN:fontsize=96:x=90:y=40,\
drawtext=fontfile=$B:text='✗ 43 g':fontcolor=$RED:fontsize=96:x=900:y=40,\
drawtext=fontfile=$B:text='stands':fontcolor=$GREEN:fontsize=72:x=430:y=560,\
drawtext=fontfile=$B:text='tips':fontcolor=$RED:fontsize=72:x=1240:y=560" -frames:v 1 $F/card-hook.png
# B. rule card: the ruler with a coin, then the plain stand with its line landing inside the footprint
ffmpeg -v error -y -i $F/ruler-coin.png -i $F/stand-only.png -filter_complex "\
[0:v]scale=1150:-2[a];[1:v]crop=900:330:0:960,scale=1150:-2[b];color=c=$BG:s=$S[bg];[bg][a]overlay=241:20[t];[t][b]overlay=241:680,\
drawtext=fontfile=$B:text='a coin pulls it':fontcolor=$INK:fontsize=76:x=(w-text_w)/2:y=575,\
drawtext=fontfile=$B:text='inside the footprint\: stands':fontcolor=$GREEN:fontsize=72:x=(w-text_w)/2:y=1110" -frames:v 1 $F/card-rule.png
# C. the phone leans out: its own point lands past the back edge
ffmpeg -v error -y -i $F/stand-and-phone-dots.png -filter_complex "\
[0:v]scale=-2:1160[a];color=c=$BG:s=$S[bg];[bg][a]overlay=40:20,\
drawtext=fontfile=$B:text='phone alone\:':fontcolor=$INK:fontsize=76:x=900:y=300,\
drawtext=fontfile=$B:text='11.5 mm past':fontcolor=$RED:fontsize=90:x=900:y=400,\
drawtext=fontfile=$B:text='the back edge':fontcolor=$RED:fontsize=90:x=900:y=510,\
drawtext=fontfile=$B:text='you →':fontcolor=$BLUE:fontsize=80:x=1320:y=1040" -frames:v 1 $F/card-phone.png
# D. the print is mostly air: one real layer of the slicer plan
ffmpeg -v error -y -i $F/honeycomb.png -filter_complex "\
[0:v]scale=1300:-2[a];color=c=0xffffff:s=$S[bg];[bg][a]overlay=166:150,\
drawtext=fontfile=$B:text='walls solid, 15% grid inside':expansion=none:fontcolor=$INK:fontsize=74:x=(w-text_w)/2:y=30,\
drawtext=fontfile=$B:text='43 g, not 156':fontcolor=$RED:fontsize=100:x=(w-text_w)/2:y=1070" -frames:v 1 $F/card-air.png
# E. SolidCraft render (no words: the card body names SolidCraft and Claude)
ffmpeg -v error -y -i $F/render-p210-iso.png -filter_complex "\
[0:v]crop=1000:900:460:0,scale=-2:1180[a];color=c=$BG:s=$S[bg];[bg][a]overlay=(W-w)/2:10" -frames:v 1 $F/card-claude.png
# F. Claude's flip: part 1 vs a flipped design
ffmpeg -v error -y -i $F/side-p210-sliced.png -i $F/run-outcome3-fits.png -filter_complex "\
[0:v]scale=-2:960[a];[1:v]scale=-2:960[b];color=c=$BG:s=$S[bg];[bg][a]overlay=70:200[t];[t][b]overlay=880:200,\
drawtext=fontfile=$B:text='part 1':fontcolor=$INK:fontsize=90:x=90:y=40,\
drawtext=fontfile=$B:text='Claude\: flipped':fontcolor=$BLUE:fontsize=90:x=880:y=40" -frames:v 1 $F/card-flip.png
# G. the 2 mm ledge: the slot opening of two flipped designs, zoomed
ffmpeg -v error -y -i $F/run-outcome1-mouth.png -i $F/run-outcome3-mouth.png -filter_complex "\
[0:v]scale=790:-2[a];[1:v]scale=790:-2[b];color=c=$BG:s=$S[bg];[bg][a]overlay=17:330[t];[t][b]overlay=825:330,\
drawtext=fontfile=$B:text='✗ opening 4.4 mm':fontcolor=$RED:fontsize=74:x=30:y=60,\
drawtext=fontfile=$B:text='✓ phone fits':fontcolor=$GREEN:fontsize=74:x=840:y=60,\
drawtext=fontfile=$B:text='2 mm ledge':fontcolor=$RED:fontsize=72:x=330:y=200" -frames:v 1 $F/card-ledge.png
# H. the fix: front lip 15 vs 40 (bracket under each base)
ffmpeg -v error -y -i $F/fix-before.png -i $F/fix-after.png -filter_complex "\
[0:v]scale=-2:960[a];[1:v]scale=-2:960[b];color=c=$BG:s=$S[bg];[bg][a]overlay=70:200[t];[t][b]overlay=880:200,\
drawtext=fontfile=$B:text='✗ front lip 15':fontcolor=$RED:fontsize=80:x=80:y=40,\
drawtext=fontfile=$B:text='✓ front lip 40':fontcolor=$GREEN:fontsize=80:x=880:y=40,\
drawtext=fontfile=$B:text='same 43 g':fontcolor=$INK:fontsize=72:x=700:y=160,\
drawtext=fontfile=$B:text='you →':fontcolor=$BLUE:fontsize=72:x=1380:y=560" -frames:v 1 $F/card-fix.png
echo "cards2 written"
