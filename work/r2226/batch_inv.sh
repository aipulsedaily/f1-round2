#!/bin/bash
cd $HOME/f1-round2
run () { # item coll prefix
  /opt/blender-5.2.0-linux-x64/blender -b world/items/$1_test.blend --factory-startup -noaudio \
    -P work/r2226/inventory_item.py -- --collection "$2" --prefix "$3" --out work/r2226/inv_$1.json \
    > work/r2226/inv_$1.log 2>&1
  echo "$1: $(grep 'STAGE RESULT' work/r2226/inv_$1.log)  $(grep 'collection ' work/r2226/inv_$1.log | head -1)"
}
run crew_figure          W_Item_CrewFigure          CRF_
run timing_stand         W_Item_TimingStand         TS_
run armco_post           W_Item_ArmcoPost           AP_
run catch_fence_post     W_Item_CatchFencePost      CFP_
run tyre_wall_tyre       W_Item_TyreWallTyre        TWT_
run heras_fence_panel    W_Item_HerasFencePanel     HFP_
run spectator_crowd      ITEM_spectator_crowd       SPECX_
run pit_wall_unit        W_Item_PitWallUnit         PWU_
echo BATCHINVDONE
