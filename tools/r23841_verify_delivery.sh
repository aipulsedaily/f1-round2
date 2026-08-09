#!/usr/bin/env bash
# VERIFY A FINISHED DELIVERABLE -- the checks that must pass before anything ships.
#
#   tools/r23841_verify_delivery.sh MEDIA FFCONCAT WAV EXPECTED_FRAMES FPS
#
# e.g.
#   tools/r23841_verify_delivery.sh \
#       deliver/R2_master_4K_ProRes422HQ.mov \
#       tmp/r23841_master4k.ffconcat \
#       audio/out/master.wav 2978 24
#
# Frame counts here are COUNTED off the bitstream (-count_frames), never read
# from the container's nb_frames field -- a truncated file will happily claim
# 2978 in its header. Head/tail frames are compared against the actual first
# and last source PNGs, because a sync error or an off-by-one in the frame list
# shows up at the ends and nowhere else.
#
# Never judges $? after a pipe: every stage that matters writes to a file and
# its own status is read directly.
set -u

MEDIA=${1:?media file}
LIST=${2:?ffconcat frame list}
WAV=${3:?source wav}
NFRAMES=${4:?expected frame count}
FPS=${5:-24}

TMPD=$(mktemp -d); trap 'rm -rf "$TMPD"' EXIT
FAIL=0
ok()   { printf '  PASS  %s\n' "$*"; }
bad()  { printf '  FAIL  %s\n' "$*"; FAIL=1; }
want() { [ "$2" = "$3" ] && ok "$1 = $2" || bad "$1 = $2 (expected $3)"; }

EXP_DUR=$(python3 -c "print(f'{$NFRAMES/$FPS:.6f}')")
printf '== %s\n' "$MEDIA"
printf '   expecting %s frames @ %s fps = %s s\n' "$NFRAMES" "$FPS" "$EXP_DUR"

# ---- 1. counted frames, geometry, rate, colour -------------------------------
ffprobe -v error -count_frames -select_streams v:0 \
  -show_entries stream=nb_read_frames,width,height,pix_fmt,r_frame_rate,color_range,color_space,color_transfer,color_primaries,start_time \
  -of default=nw=1 "$MEDIA" > "$TMPD/v" || { echo "  FAIL  ffprobe video failed"; exit 1; }
g() { sed -n "s/^$1=//p" "$TMPD/$2"; }

want "nb_read_frames (COUNTED)" "$(g nb_read_frames v)" "$NFRAMES"
want "width"            "$(g width v)"            "3840"
want "height"           "$(g height v)"           "2160"
want "r_frame_rate"     "$(g r_frame_rate v)"     "$FPS/1"
want "color_primaries"  "$(g color_primaries v)"  "bt709"
want "color_transfer"   "$(g color_transfer v)"   "bt709"
want "color_space"      "$(g color_space v)"      "bt709"
want "color_range"      "$(g color_range v)"      "tv"
want "video start_time" "$(g start_time v)"       "0.000000"

# ---- 2. duration -------------------------------------------------------------
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$MEDIA" > "$TMPD/f" || exit 1
DUR=$(g duration f)
python3 -c "import sys; sys.exit(0 if abs($DUR-$EXP_DUR)<=0.001 else 1)" \
  && ok "duration = ${DUR} s (target ${EXP_DUR} s)" \
  || bad "duration = ${DUR} s (target ${EXP_DUR} s)"
printf '  ....  size = %s bytes\n' "$(g size f)"

# ---- 3. audio present, and lined up at the head ------------------------------
ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,sample_rate,channels,start_time,duration \
  -of default=nw=1 "$MEDIA" > "$TMPD/a" || exit 1
[ -s "$TMPD/a" ] && ok "audio stream present ($(g codec_name a), $(g sample_rate a) Hz, $(g channels a) ch)" \
                || bad "NO AUDIO STREAM"
want "audio start_time" "$(g start_time a)" "0.000000"
ADUR=$(g duration a)
python3 -c "import sys; sys.exit(0 if abs($ADUR-$EXP_DUR)<=0.001 else 1)" \
  && ok "audio duration = ${ADUR} s (matches video, so it is in sync at the tail too)" \
  || bad "audio duration = ${ADUR} s != ${EXP_DUR} s -- audio and picture end at different times"

# ---- 4. audio content: identical to the source (lossless wraps only) ---------
if [ "$(g codec_name a)" != "aac" ]; then
  ffmpeg -v error -i "$MEDIA" -map 0:a:0 -f s24le "$TMPD/in.pcm"  && r1=0 || r1=1
  ffmpeg -v error -i "$WAV"   -map 0:a:0 -f s24le "$TMPD/src.pcm" && r2=0 || r2=1
  if [ $r1 -eq 0 ] && [ $r2 -eq 0 ] && cmp -s "$TMPD/in.pcm" "$TMPD/src.pcm"; then
    ok "audio samples BIT-IDENTICAL to $WAV (nothing re-encoded, nothing resampled)"
  else
    bad "audio samples differ from $WAV"
  fi
else
  ok "audio is AAC (lossy by design on the viewing copy) -- identity check skipped"
fi

# ---- 5. head and tail frames are the right frames ----------------------------
FIRST=$(grep -m1 "^file '" "$LIST" | sed "s/^file '//;s/'$//")
LAST=$(grep "^file '"  "$LIST" | tail -1 | sed "s/^file '//;s/'$//")
LASTIDX=$((NFRAMES-1))
for pair in "0:$FIRST" "$LASTIDX:$LAST"; do
  idx=${pair%%:*}; src=${pair#*:}
  ffmpeg -v error -i "$MEDIA" -i "$src" -filter_complex \
    "[0:v]select=eq(n\,$idx),setpts=0,scale=in_range=tv:out_range=full:in_color_matrix=bt709,format=rgb24[a];[1:v]format=rgb24[b];[a][b]psnr=stats_file=$TMPD/p$idx" \
    -f null - 2>/dev/null && r=0 || r=1
  if [ $r -ne 0 ] || [ ! -s "$TMPD/p$idx" ]; then bad "could not compare frame $idx"; continue; fi
  P=$(sed -n 's/.*psnr_avg:\([0-9.]*\).*/\1/p' "$TMPD/p$idx" | head -1)
  python3 -c "import sys; sys.exit(0 if float('$P')>35 else 1)" \
    && ok "frame $idx matches $(basename "$src")  (PSNR ${P} dB)" \
    || bad "frame $idx does NOT match $(basename "$src")  (PSNR ${P} dB) -- wrong frame at this end"
done

# ---- 6. faststart, mp4 only --------------------------------------------------
case "$MEDIA" in *.mp4)
  python3 - "$MEDIA" > "$TMPD/atoms" <<'PY'
import struct,sys
f=open(sys.argv[1],'rb'); o=[]
while True:
    h=f.read(8)
    if len(h)<8: break
    sz,t=struct.unpack('>I4s',h); t=t.decode('latin1'); o.append(t)
    if sz==1: sz=struct.unpack('>Q',f.read(8))[0]; f.seek(sz-16,1)
    elif sz==0: break
    else: f.seek(sz-8,1)
print('OK' if 'moov' in o and 'mdat' in o and o.index('moov')<o.index('mdat') else 'NO')
PY
  [ "$(cat "$TMPD/atoms")" = OK ] && ok "faststart (moov before mdat)" || bad "faststart missing"
;; esac

echo
[ $FAIL -eq 0 ] && echo "ALL CHECKS PASSED: $MEDIA" || echo "CHECKS FAILED: $MEDIA"
exit $FAIL
