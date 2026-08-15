#!/usr/bin/env bash
# R2-4152 -- LAND THE MASTER INTO BOTH FILMS, PROVING THE PICTURE DID NOT MOVE.
#
#   bash tools/r2_4152_land.sh
#
# Both films are re-muxed `-c:v copy`. The video stream's md5 is taken BEFORE and
# AFTER and the script REFUSES if either changes -- the picture is 2,978 frames
# rendered on three rented 5090s over five days and an audio landing may not
# touch it. Declared, from `watch/INDEX.md`:
#     ProRes  c346a7a322a4a2a403727c1e85f17511
#     H.265   235ef36e844a62b0e303e4138907b9fa
set -euo pipefail
cd "$(dirname "$0")/.."
WAV=audio/out/r2_4152/master_R2-4152.wav
DST=watch/PART2_AUDIO_MASTER_R2-4152.wav
PRORES=watch/PART2_THE_FILM_4K_ProRes422HQ.mov
H265=watch/PART2_THE_FILM_4K_h265.mp4
WANT_PRORES=c346a7a322a4a2a403727c1e85f17511
WANT_H265=235ef36e844a62b0e303e4138907b9fa
PRORES_TMP=watch/.r2_4152_tmp_ProRes.mov
H265_TMP=watch/.r2_4152_tmp_h265.mp4

vmd5() { ffmpeg -v error -i "$1" -map 0:v:0 -c copy -f md5 - | sed 's/^MD5=//'; }

echo "== video md5 BEFORE =="
A0=$(vmd5 "$PRORES"); B0=$(vmd5 "$H265")
echo "  ProRes $A0"; echo "  H.265  $B0"
[ "$A0" = "$WANT_PRORES" ] || { echo "REFUSING: ProRes video md5 is not the declared one"; exit 1; }
[ "$B0" = "$WANT_H265" ]   || { echo "REFUSING: H.265 video md5 is not the declared one"; exit 1; }

cp -f "$WAV" "$DST"

ffmpeg -v error -y -i "$PRORES" -i "$WAV" -map 0:v:0 -map 1:a:0 \
    -c:v copy -c:a pcm_s24le -movflags +write_colr "$PRORES_TMP"
ffmpeg -v error -y -i "$H265" -i "$WAV" -map 0:v:0 -map 1:a:0 \
    -c:v copy -c:a aac -b:a 192k -movflags +faststart "$H265_TMP"

echo "== video md5 AFTER =="
A1=$(vmd5 "$PRORES_TMP"); B1=$(vmd5 "$H265_TMP")
echo "  ProRes $A1"; echo "  H.265  $B1"
if [ "$A1" != "$A0" ] || [ "$B1" != "$B0" ]; then
    echo "REFUSING: a video stream md5 MOVED. Nothing replaced."
    rm -f "$PRORES_TMP" "$H265_TMP"; exit 1
fi
mv -f "$PRORES_TMP" "$PRORES"
mv -f "$H265_TMP" "$H265"
echo ">> STAGE RESULT: LANDED, both video md5s byte-identical"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$PRORES"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$H265"
