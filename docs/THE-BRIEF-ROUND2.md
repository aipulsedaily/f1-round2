# ROUND 2 — F1 CINEMATIC: ONE UNBROKEN SHOT. ASSEMBLY → WALL BREACH → FLYING LAP



Round 1 is finished. Do NOT assume what it produced — inventory it. STEP ZERO, before any planning: open the final .blend(s) and the project folder, enumerate every mesh/collection/part module that actually exists (names, counts, hierarchy, transforms), read the round-1 defect log and task history, and write a `round2_inventory.md` that becomes the single source of truth for what the car is made of. However many parts there are — 12, 14, 40 — the plan adapts to the inventory, never the other way around. If the inventory reveals surprises (merged parts, extra detail meshes, renamed collections, leftover WIP objects), resolve them explicitly in the inventory doc before proceeding.



Round 2 produces ONE final video with ONE absolute law above all others:



## THE LAW: ONE CONTINUOUS SHOT



The entire video — assembly, wall breach, drive to the track, the full lap, the ending — is a SINGLE unbroken camera take. Zero cuts. Zero crossfades. Zero hidden whip-pan cheats. One camera, one continuous path through space and time, first frame to last frame. Everything below bends to this law:



- **One world.** The showroom, its exterior, the connecting road, and the full circuit exist in ONE scene, spatially continuous and to consistent scale. The showroom sits trackside (design it into the circuit's paddock area, glass wall facing the pit straight or an access road). The camera physically travels from inside the showroom, through the breached wall, and onto the circuit. Build the world so this route is real geometry the whole way — no teleports, no fog-wall scene swaps.

- **One camera path.** A single animated camera with a fully choreographed trajectory and focal/exposure/DOF animation over the entire duration. Plan it like a drone-cinematography flight plan: write a beat sheet (timestamp → camera position/move → what it's framing → speed of time) into the project docs BEFORE animating, and refine it with fast preview renders (low samples, low res are permitted ONLY for camera-path previews — final frames are always full quality).

- **Time is allowed to bend; the shot is not.** Slow-motion happens as in-camera SPEED RAMPS (time remapping of the world's animation while the camera keeps flying), not as separate slow-mo shots. Ramps must be smooth (eased time curves, no stepped time), and the audio must ramp with them.

- **No AI-generated images, video, or audio. No downloaded stock anything.** Every frame is rendered in Blender from our geometry; every sound is physically synthesized in code. Render time is explicitly NOT a constraint — quality is the only axis. If a frame takes 20 minutes, it takes 20 minutes.



## DELIVERABLE



A single mastered video: `f1_oneshot_final.mp4` — 3840×2160 (4K), 24 fps, ~100–130 seconds, H.265 CRF 14 (plus a lossless FFV1/ProRes master), 48 kHz stereo audio, -14 LUFS integrated. Plus: `round2_inventory.md`, the camera beat sheet, the unified world .blend, the telemetry CSV, the full defect log, all audio synthesis scripts, and a contact sheet of one still per beat.



## THE SHOT — BEAT BY BEAT (timings approximate; the beat sheet is the source of truth)



**Beat 1 — Assembly, the parts showcase (≈0:00–0:35).** This beat is a PARTS SHOWCASE as much as an assembly: every part must be clearly visible, close, and readable at the highest detail the geometry and materials can deliver. Camera drifts through the darkened showroom as parts hang exploded in space around the empty turntable. EVERY part from the inventory — however many there are — arranged with deliberate engineered spacing (compute exploded offsets from each part's bounding box and final transform along mechanically sensible axes: fore/aft elements along Y, lateral outboard, underbody drops, top structures rise). If there are many small parts, group them into assembly clusters (e.g. per-corner suspension clusters) so it reads as engineering, not confetti — grouping derived from the inventory, not a preset list.



The showcase rules:

- **Every part/cluster gets a readable moment.** Choreograph the camera path AND the part flight paths together so that each part (or cluster) is, at some point, large in frame — either the camera flying a close pass over it while it hangs in the exploded field, or the part's flight path carrying it close past the lens on its way to seat. With many parts, sequence these moments densely: the camera weaves THROUGH the exploded field like a drone through a hangar, parts sliding past near-camera continuously. Log the choreography in the beat sheet: every inventory line item maps to a timestamp where it is clearly visible. No part seats without having been seen.

- **Close-up worthiness is a defect gate.** At these near-camera distances at 4K, materials and geometry will be under a microscope: carbon weave must resolve as actual weave (no blur, no obvious tiling at macro distance), decals crisp at pixel level, metallic and rubber shaders holding up at grazing angles, edge bevels present (no razor-sharp CG edges filling the frame). Render test close-ups of EVERY hero part at the actual camera distance from the beat sheet and pixel-peep them BEFORE animating the full beat. Any part that fails macro inspection gets its materials/geometry upgraded first — subdivision, texture resolution, bevel, imperfection layers (subtle dust, fingerprint-level surface variation on paint) — then re-tested. If a texture is too low-res for its close-up, rebuild it at the needed resolution; never solve it by keeping the camera away.

- **DOF as the presenter.** Shallow depth of field with animated focus pulling from part to part as the camera weaves — the in-focus part is the one being presented; near-misses sweep past soft in the foreground. Focus pulls are eased, never snapped.

- **Light for legibility.** Parts in the exploded field must be lit to be READ: use the showroom rig plus, if needed, subtle added practicals/rim lighting motivated by the ceiling coves so each presented part gets edge separation from the dark background. No part's readable moment happens in mud.



Parts fly to final transforms in an order derived by one rule: structural core first (identify the central chassis/tub by geometry and hierarchy, not by name), inboard-to-outboard, underbody before topside, aero late, wheels LAST with a simultaneous seat. Eased F-curves, 2–4 frame settle on arrival, staggered landings. Write the chosen order + justification into the inventory doc. The beat ends with the camera pushing toward the completed car as the spot rigs ramp up ~1 stop over 12 frames. All subsequent beat timestamps shift accordingly — the beat sheet, not the numbers in this doc, is the source of truth; total runtime may grow toward ~2 minutes and that is fine.



**Beat 2 — Ignition and launch (≈0:20–0:26).** Camera settles low behind/beside the car. One second of stillness, engine dropping to idle rumble. Launch: wheelspin for ~10 frames (wheels spin faster than travel — the ONLY sanctioned violation of the rolling-contact rule), then hook-up, hard acceleration straight at the glass wall. Camera accelerates WITH the car, tucked alongside or just behind.



**Beat 3 — The breach (≈0:26–0:34).** The car hits the glass wall and the world goes into a speed ramp: time eases down to ~15–25% as the nose meets the glass, the camera swings around the erupting shard field in a smooth arc (camera keeps real-time flight while world-time is slowed — this contrast is the money moment of the entire video), then time eases back to 100% as the car clears the debris. The wall is a REAL destruction sim: pre-fracture the glass (cell fracture, small shards at impact point, larger at edges) plus wall framing; rigid body sim with the car as an animated passive of effectively infinite mass; shards inherit contact velocity, tumble with spin, catch the incoming daylight. Cache, inspect, iterate — glass falls FAST; floaty moon-gravity debris means fix scale/gravity/mass and re-sim. Dust burst at the breach, secondary debris skittering across the concrete outside. Because there is no cut, the sim must look correct from the ENTIRE camera arc, not one flattering angle. Continuity: the hole and floor shards persist for the rest of the shot — if the camera ever sees the showroom again, it is wounded.



**Beat 4 — Transit to the circuit (≈0:34–0:42).** Camera pulls back and up into a chase position as the car powers away from the building, through the paddock/access road, and merges onto the circuit. Exposure animates from interior spill to full daylight over ~15 frames. This beat is the world-design linchpin: the route from showroom to track must be dressed at full fidelity (paddock concrete, pit buildings, fencing, signage) because the camera crosses it in one take.



**Beat 5 — The lap (≈0:42–1:45).** The camera stays with the car for a full flying lap, continuously morphing between vantage points WITHOUT cutting: swooping from chase to low kerb-height alongside at the hairpin, rising into a helicopter arc through the esses, diving down to a near-trackside pass (this close pass with the camera briefly near-static as the car rips by is the doppler beat — the camera may slow its own motion to nearly a hover for ≥3 s while the car passes, then whip after it), tucking into a tight onboard-like follow down the main straight at ~330 km/h, and optionally ONE more brief speed ramp at the fastest apex (suspension compression visible). Every transition between vantage points is flown, eased, and motivated. A second lap is NOT required — one lap, flown beautifully.



**Beat 6 — The ending (≈ last 8–10 s).** As the car crosses the line, the camera decelerates and rises/pulls back into a closing wide — the circuit, the car streaking on, the breached showroom visible in the distance with its wound — and holds a final composed frame for ~3 s. End.



## THE WORLD



- Circuit: 12–16 corners as a curve object with real F1 geometry language — long main straight, heavy braking hairpin, esses complex, fast double-apex sweeper, 8–12 m elevation change. The showroom/paddock placement is part of the layout design.

- Surface: tiling-free asphalt (2–3 mixed detail scales), rubbered-in racing line tightening through apexes, two-tone serrated kerbs, white lines, faded paint on the straight.

- Surroundings: pit building + gantry, grandstand blocks, barriers + catch fencing (instanced, dense), gravel traps at braking zones, distant terrain/treeline, procedural sky, late-afternoon sun for long shadows.

- Dressing: marshal posts, fictional-brand advertising boards (no real sponsors or real team liveries beyond our own car), tire stacks, sparse instanced grass clumps.

- LOD honesty: because one camera crosses everything, there are no "cheap far-side" zones the camera never sees — but you know the camera path exactly, so budget detail by distance-to-path: full fidelity within ~50 m of the path, progressively simpler beyond, and verify no LOD seam is ever visible in a rendered frame.



## MOTION & TELEMETRY



One speed profile drives everything. Build a per-frame telemetry CSV: position along path, speed (hairpin ~80 km/h, straight ~330 km/h) from plausible accel/braking envelopes, extended to cover the launch and transit beats. It drives: wheel rotation (rotation = distance / wheel radius — rolling contact everywhere except the sanctioned launch wheelspin), steering articulation, chassis pitch/roll (brake dive, power squat, cornering lean, 1–2°, sell it don't cartoon it), the camera choreography timing, AND the audio. The racing line offsets from centerline to hit apexes. During speed ramps, world-time remapping applies to the telemetry too, so physics and sound stay locked to the picture. Motion blur ON throughout (shutter 180°); during ramps, scale shutter with world-time so blur reads correctly at slowed speed. ONE agent owns the telemetry CSV + camera beat sheet as the single source of truth; everyone else reads from it.



## AUDIO — ONE CONTINUOUS SYNTHESIZED MIX, ZERO SAMPLES



All audio generated by numpy/scipy code, mixed with ffmpeg, scripts saved. Because the picture never cuts, the audio never cuts: one continuous stereo mix, evolving with the camera.



1. **Engine:** V6 turbo-hybrid model: fundamental = RPM/60 × 3, 10–15 tuned harmonics, exhaust rasp (filtered noise AM'd at firing rate), turbo whine sweeping with RPM, MGU-K harvest whine under braking. RPM per frame from telemetry: speed → gear (8-speed ratio table) → RPM, 80–120 ms shift dips with an upshift crack.

2. **Continuous spatialization:** the listener is the CAMERA. Per audio block, compute car→camera distance and relative radial velocity from telemetry + the camera path; apply doppler (f' = f·c/(c−v_r)), inverse-square amplitude, progressive air-absorption low-pass, and stereo panning from the car's screen-space position — continuously, for the entire duration. The near-static trackside pass in Beat 5 should produce a textbook doppler sweep with no special-casing, because the math is always on.

3. **The breach:** layered event driven by the physics — (a) impact thud (40–80 Hz sine burst, fast decay), (b) shatter cloud: hundreds of short bandpassed resonant pings (2–8 kHz, randomized pitch/decay) with density/timing read from the ACTUAL rigid-body sim's collision/activation events, (c) debris tail tinkles timed from sim floor contacts, (d) structural crunch (filtered brown-noise burst). During the speed ramp, ALL audio time-stretches and pitches with world-time (the engine and shatter smear down as time slows, return as it ramps back) — slow picture with real-time sound is a defect.

4. **Layers:** assembly act — room tone + servo whir + one filtered impact per part/cluster arrival, timed from actual animation keyframes, pitched by real bounding-box volume as mass proxy; track — wind (speed-shaped filtered noise, scaled by CAMERA airspeed since the listener flies), tire roar (brown noise, speed-scaled), kerb strikes triggered from actual racing-line/kerb geometry crossings.

5. **Mix:** one continuous master, -14 LUFS integrated, true-peak limit -1 dBTP. Inspect waveforms/spectrograms like you pixel-peep frames; log audio defects (doppler resample aliasing, ramp artifacts, zipper noise in panning) in the same defect log.



## WORKFLOW — ROUND-1 DISCIPLINE, PER FRAME, PLUS CONTINUITY LAW



- Cycles at final quality, always. Per-beat sample tuning: render one frame, pixel-peep at 100% zoom in the darkest region, raise samples until clean, lock. Denoiser only if with/without crops show zero detail loss on carbon weave and decals.

- Because this is one shot, TEMPORAL CONTINUITY is a first-class defect category: any batch boundary (different agents/machines rendering different frame ranges) must be verified seam-invisible — identical scene state, sim caches, light settings, and grade across the boundary. Render 5 frames of overlap at every batch boundary and diff them; any pop, flicker, or shift at a boundary is a defect.

- Before committing any beat: render frames [first, 25%, 50%, 75%, last] at final settings, pixel-peep tight crops (wing edges, tire contact, shard/car intersections — zero clipping through nose/halo, glass transmission shading — not gray plastic, DOF transitions, motion-blur streaks during ramps, sky banding). Log every defect with before/after crops. Fix, re-render the SAME frame, confirm, then batch.

- After each beat renders, temporal pass: assemble with ffmpeg, watch for flicker, popping shadows, hitches, LOD seams, ramp smoothness. Defects mean fix + re-render the affected range, never "acceptable."

- Never claim a step done from memory — every "done" is backed by a rendered frame or assembled clip you actually inspected.

- Fan out where it's safe (world construction, audio synthesis, sim iteration, beat animation) but the telemetry CSV + beat sheet owner is the single source of truth.

- Merely fine is not done: push DOF, subtle vignette + chromatic aberration (constant across the whole shot — it's one lens for one take), light balance, motion polish.



## FINAL ASSEMBLY



ffmpeg: concatenate the frame sequence into one stream, apply ONE consistent grade across the entire duration (a single pass — per-beat grade changes would betray the cut-free illusion; exposure changes belong in the animated camera, not the grade), mux the continuous audio master, export H.265 4K delivery + lossless master. Final gate: watch the entire video end-to-end at least twice at full attention, specifically hunting for anything that breaks the one-shot spell — a seam, a pop, a time-ramp stutter, an audio zipper. Zero open defects, video or audio, before you call it.
