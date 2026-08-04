
---

## AND THEN IT WAS LOOKED AT

Rendered at 4K on the 5090 from `render/driver_look.blend` — the car, the
driver, `itemkit.contract_sun`'s sky and sun, at the film's own camera
positions and the film's grade (AgX / None / -3.628, read back and asserted).
Crops in `render/driver/`.

**Frame 2632, the peak (366 px sharp helmet, 2.42 m).** The helmet reads. Real
shell curvature, crown vents, a livery with a shape rather than a decal, and
paint with specular depth. It sits under the halo and proud of the cockpit rim,
in the headrest cradle, where it should.

**Frame 828, the launch, in profile.** This is the money shot and it is the one
that settles it: helmet in profile above the bodywork, the halo's front pillar
crossing it, the mirror beside it. Unmistakably a driver.

**Frame 700, head-on down the cockpit.** Visor, aperture trim, halo bar across
the face. Reads.

**The A/B, `crop_f2632.png` vs `crop_f2632_nodriver.png`, same camera, same
128 samples, driver hidden.** Without him: a visibly vacant seat — harness slot
openings, headrest, the tan seat shell, the extinguisher button, all plainly on
show. With him: that whole volume goes dark and occupied and a helmet sits in
the cradle. The hole is closed.

**`isolate_f2632.png`** is the driver alone with the car hidden, and it is the
proof the trim did not maim him: helmet, visor, HANS and tether hardware, race
suit with seams, panel lines and reflective bands, both gloves closed on the
wheel grips, arms tracking forward at a plausible angle.

### What does NOT read, stated plainly

**The driver sits about 0.20 m deeper in the tub than a real one, and the
cockpit reads emptier around the helmet because of it.** This is not a
placement error, it is round 1's cockpit:

    driver hip-to-shoulder            0.345 m   (correct anthropometry)
    hip-to-crown                      0.713 m   (measured on the mesh)
    round 1 seat-pan to cockpit rim   0.321 m
    round 1 seat-pan to halo apex     0.474 m

Put the hip on the seat pan where it belongs and the crown lands at 1.122 —
**0.24 m ABOVE the halo apex**, with the halo bar at the driver's chin. The
cockpit and halo are built to roughly 60 % of the hip-to-crown a 1.78 m man
needs. Fitting the crown under the halo is what forces the hip 0.229 m below
the pan, and that in turn is what puts the shoulders 0.20 m below the rim
instead of the 0.10-0.15 m a reference photograph shows.

There is 0.054 m of headroom left to `MB_chassis_cockpit`'s top (0.9307) and
raising the figure into it would recover part of the shoulder line — the wheel
is parametric so the hands would follow — but it puts the crown hard against
the engine cover. **Not taken. The numbers are recorded so the call can be made
with them rather than by eye.**

**THE REBUILD THAT IS OWED:** round 1's cockpit tub needs roughly 0.25 m more
hip-to-crown — a deeper floor or a raised halo — for a correctly proportioned
driver to sit at a real height. That is `/home/zany/opus5-car-render` geometry
and it is READ-ONLY, so it cannot be done here.

### What the look scene is not

No track surface, no grandstands, no showroom: the ground bounce and the built
environment do not appear, and the visor is a mirror, so it shows a cleaner sky
here than it will in the film. `--film-world` exists to swap
`contract_sun` for assembly9's own world and lights when that matters.

**`render/film14.blend` has NOT been rebuilt with the driver.** The command is

    blender -b render/world/assembly/r2/assembly9.blend --factory-startup \
        -P tools/build_film_scene.py -- --car world/car_anim_driver.blend \
           --out render/film15.blend

and `tools/driver_film_preflight.py` says it will be accepted, but a preflight
is not a film. That build is the outstanding item.
