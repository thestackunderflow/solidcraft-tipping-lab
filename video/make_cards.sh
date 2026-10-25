#!/usr/bin/env sh
# Stills: words only on top of our drawings (video/draw.py) and SolidCraft's renders. Needs ffmpeg + DejaVu fonts:
#   docker run --rm -v <lab>:/work -w /work video-qa:2 sh video/make_cards.sh
#   hook-landscape.png   frame 0: the same stand + 210 g phone, solid (left) vs sliced (right), a magnifier on each
#                        back edge, the margin in mm; "slicer estimate, not a print"
#   ruler-card.png       the ruler on a finger, then with a coin taped near one end
#   honeycomb-card.png   one real layer of the slicer's plan: walls solid, inside a honeycomb; the two weights
#   claude-card.png      SolidCraft's render of the stand with the phone block: who's who
#   fix-card.png         front lip 15 (tips) vs 40 (stands), sliced, 210 g phone
#   hook-vertical.png    the Short's frame 0
set -eu
F=video/frames
B=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
R=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
RED=0xb71c1c; GREEN=0x1b5e20; INK=0x1f2937; GREY=0x475569; BG=0xeceff4; BLUE=0x1d4ed8
# side drawings are 900 x 1300 at 7.5 px/mm; the back edge (y = 3 mm, table) sits at px (322, 1240)
# magnifier: a 200 x 150 crop around it, scaled x1.8 (360 x 270), boxed
ffmpeg -v error -y -i $F/side-p210-solid.png -i $F/side-p210-sliced.png -filter_complex "\
[0:v]scale=-2:880[a];[1:v]scale=-2:880[b];\
[0:v]crop=200:150:222:1165,scale=360:270,pad=368:278:4:4:color=$GREEN[ma];\
[1:v]crop=200:150:222:1165,scale=360:270,pad=368:278:4:4:color=$RED[mb];\
color=c=$BG:s=1920x1080[bg];[bg][a]overlay=150:150[t1];[t1][b]overlay=1000:150[t2];[t2][ma]overlay=470:200[t3];[t3][mb]overlay=1320:200,\
drawtext=fontfile=$B:text='✓ ON THE COMPUTER\: 156 g':fontcolor=$GREEN:fontsize=50:x=120:y=40,\
drawtext=fontfile=$B:text='✗ SLICED\: 43 g':fontcolor=$RED:fontsize=50:x=1000:y=40,\
drawtext=fontfile=$R:text='slicer estimate, not a print':fontcolor=$RED:fontsize=30:x=1000:y=100,\
drawtext=fontfile=$B:text='5.7 mm to spare':fontcolor=$GREEN:fontsize=34:x=470:y=490,\
drawtext=fontfile=$B:text='5.0 mm past the edge':fontcolor=$RED:fontsize=34:x=1320:y=490,\
drawtext=fontfile=$R:text='the back edge, magnified':fontcolor=$GREY:fontsize=26:x=470:y=170,\
drawtext=fontfile=$R:text='the back edge, magnified':fontcolor=$GREY:fontsize=26:x=1320:y=170,\
drawtext=fontfile=$R:text='Part 1 stand + a 210 g phone block · seen from the side, you sit on the right · dot = balance point':fontcolor=$INK:fontsize=28:x=(w-text_w)/2:y=1040" \
  -frames:v 1 $F/hook-landscape.png
ffmpeg -v error -y -i $F/ruler-plain.png -i $F/ruler-coin.png -filter_complex "\
[0:v]scale=1000:-2[a];[1:v]scale=1000:-2[b];color=c=$BG:s=1920x1080[bg];[bg][a]overlay=820:40[t];[t][b]overlay=820:560,\
drawtext=fontfile=$B:text='One balance point':fontcolor=$INK:fontsize=50:x=80:y=180,\
drawtext=fontfile=$R:text='rest it there and it stays level':fontcolor=$GREY:fontsize=34:x=80:y=250,\
drawtext=fontfile=$B:text='A coin pulls it':fontcolor=$INK:fontsize=50:x=80:y=700,\
drawtext=fontfile=$R:text='the heavier side wins':fontcolor=$GREY:fontsize=34:x=80:y=770,\
drawtext=fontfile=$R:text='red dot = balance point':fontcolor=$RED:fontsize=30:x=80:y=1010" -frames:v 1 $F/ruler-card.png
ffmpeg -v error -y -i $F/honeycomb.png -filter_complex "\
[0:v]scale=1100:-2[a];color=c=0xffffff:s=1920x1080[bg];[bg][a]overlay=60:120,\
drawtext=fontfile=$B:text='walls\: solid':fontcolor=0x334155:fontsize=46:x=1240:y=220,\
drawtext=fontfile=$B:expansion=none:text='inside\: 15% grid':fontcolor=0x64748b:fontsize=46:x=1240:y=300,\
drawtext=fontfile=$B:text='slicer\: 43 g':fontcolor=$RED:fontsize=50:x=1240:y=470,\
drawtext=fontfile=$B:text='design file\: 156 g':fontcolor=$GREEN:fontsize=50:x=1240:y=550,\
drawtext=fontfile=$R:text='about a quarter':fontcolor=$INK:fontsize=38:x=1240:y=630,\
drawtext=fontfile=$R:text='One layer of the slicer plan 15 mm up · PrusaSlicer 2.9.2, 0.20mm SPEED preset · seen from above':fontcolor=$INK:fontsize=28:x=(w-text_w)/2:y=1020" \
  -frames:v 1 $F/honeycomb-card.png
ffmpeg -v error -y -i $F/render-p210-iso.png -filter_complex "\
[0:v]crop=900:820:510:20,scale=1030:-2[a];color=c=$BG:s=1920x1080[bg];[bg][a]overlay=560:70,\
drawtext=fontfile=$B:text='SolidCraft':fontcolor=$INK:fontsize=54:x=80:y=300,\
drawtext=fontfile=$R:text='a free design program':fontcolor=$GREY:fontsize=36:x=80:y=372,\
drawtext=fontfile=$B:text='Claude':fontcolor=$INK:fontsize=54:x=80:y=520,\
drawtext=fontfile=$R:text='an AI that can work it':fontcolor=$GREY:fontsize=36:x=80:y=592,\
drawtext=fontfile=$R:text='SolidCraft 0.22.0 render · the part 1 stand + the 210 g phone block':fontcolor=$INK:fontsize=28:x=(w-text_w)/2:y=1030" \
  -frames:v 1 $F/claude-card.png
ffmpeg -v error -y -i $F/side-p210-sliced.png -i $F/side-fix-p210-sliced.png -filter_complex "\
[0:v]scale=-2:880[a];[1:v]scale=-2:880[b];color=c=$BG:s=1920x1080[bg];[bg][a]overlay=150:150[t];[t][b]overlay=1000:150,\
drawtext=fontfile=$B:text='✗ FRONT LIP 15 mm':fontcolor=$RED:fontsize=48:x=120:y=40,\
drawtext=fontfile=$R:text='5.0 mm past the edge':fontcolor=$RED:fontsize=32:x=120:y=100,\
drawtext=fontfile=$B:text='✓ FRONT LIP 40 mm':fontcolor=$GREEN:fontsize=48:x=1000:y=40,\
drawtext=fontfile=$R:text='15.8 mm to spare, same 43 g':fontcolor=$GREEN:fontsize=32:x=1000:y=100,\
drawtext=fontfile=$R:text='Both sliced (slicer estimate) · 210 g phone · the slot moved 25 mm toward you':fontcolor=$INK:fontsize=28:x=(w-text_w)/2:y=1040" \
  -frames:v 1 $F/fix-card.png
ffmpeg -v error -y -i $F/side-p210-solid.png -i $F/side-p210-sliced.png -filter_complex "\
[0:v]scale=500:-2[a];[1:v]scale=500:-2[b];color=c=$BG:s=1080x1920[bg];[bg][a]overlay=30:520[t];[t][b]overlay=550:520,\
drawtext=fontfile=$B:text='Mostly air inside':fontcolor=$INK:fontsize=70:x=(w-text_w)/2:y=170,\
drawtext=fontfile=$B:text='+ a 210 g phone\:':fontcolor=$INK:fontsize=70:x=(w-text_w)/2:y=260,\
drawtext=fontfile=$B:text='does it tip?':fontcolor=$BLUE:fontsize=84:x=(w-text_w)/2:y=370,\
drawtext=fontfile=$B:text='✓ solid 156 g':fontcolor=$GREEN:fontsize=46:x=50:y=1290,\
drawtext=fontfile=$B:text='✗ sliced 43 g':fontcolor=$RED:fontsize=46:x=580:y=1290,\
drawtext=fontfile=$R:text='slicer estimate, not a print':fontcolor=$GREY:fontsize=34:x=(w-text_w)/2:y=1380" \
  -frames:v 1 $F/hook-vertical.png
echo "cards written"
ffmpeg -v error -y -i $F/run-outcome1-mouth.png -i $F/run-outcome3-mouth.png -filter_complex "\
[0:v]scale=880:-2[a];[1:v]scale=880:-2[b];color=c=$BG:s=1920x1080[bg];[bg][a]overlay=60:220[t];[t][b]overlay=980:220,\
drawtext=fontfile=$B:text='✗ FLOOR 8 mm':fontcolor=$RED:fontsize=48:x=60:y=60,\
drawtext=fontfile=$R:text='mouth 4.4 mm, phone 9 mm':fontcolor=$RED:fontsize=34:x=60:y=130,\
drawtext=fontfile=$B:text='✓ FLOOR 12 mm':fontcolor=$GREEN:fontsize=48:x=980:y=60,\
drawtext=fontfile=$R:text='the phone slides in':fontcolor=$GREEN:fontsize=34:x=980:y=130,\
drawtext=fontfile=$R:text='The slot mouth, zoomed in, side view · red = where the phone block would cut into the stand':fontcolor=$INK:fontsize=28:x=(w-text_w)/2:y=920,\
drawtext=fontfile=$R:text='Two designs Claude made, back angle 110 · our drawing from the saved designs':fontcolor=$GREY:fontsize=26:x=(w-text_w)/2:y=970" \
  -frames:v 1 $F/mouth-card.png
echo "mouth card written"
ffmpeg -v error -y -i $F/side-p210-sliced.png -i $F/run-outcome3-fits.png -filter_complex "\
[0:v]scale=-2:860[a];[1:v]scale=-2:860[b];color=c=$BG:s=1920x1080[bg];[bg][a]overlay=170:170[t];[t][b]overlay=1050:170,\
drawtext=fontfile=$B:text='PART 1':fontcolor=$INK:fontsize=48:x=120:y=40,\
drawtext=fontfile=$R:text='leans over the short end':fontcolor=$INK:fontsize=34:x=120:y=104,\
drawtext=fontfile=$B:text='CLAUDE\: FLIPPED':fontcolor=$BLUE:fontsize=48:x=1000:y=40,\
drawtext=fontfile=$R:text='leans over the long end':fontcolor=$BLUE:fontsize=34:x=1000:y=104,\
drawtext=fontfile=$R:text='Side view · back angle 70 (left) and 110 (right) · our drawing from the saved designs':fontcolor=$INK:fontsize=28:x=(w-text_w)/2:y=1045" \
  -frames:v 1 $F/flip-card.png
echo "flip card written"
