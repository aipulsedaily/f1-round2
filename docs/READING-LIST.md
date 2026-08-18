# A curated reading list for `DEFECT-LOG-R2.md`

1,295 distinct entries, 67,640 lines *(measured 2026-08-18; the log is
append-only)*. This is roughly sixty of them, chosen because they carry
something transferable — not because they are the biggest fixes.

Start with [`README.md`](README.md) for the numbering rules and the
live-vs-historical map, or [`INDEX.md`](INDEX.md) if you are looking for one
specific file.

### About the line numbers

Every link below carries a hard line number into a 67,000-line file, and **on
2026-08-18 every one of the 111 of them was wrong by exactly +17** — the log had
gained seventeen lines above the first cited entry, and nothing announced it.
The links still rendered and still looked right; they simply landed seventeen
lines short of the entry they name. That is the same failure this whole corpus
catalogues, so it now has an instrument that can fail rather than a warning
asking readers to be careful:

```bash
python3 tools/docs_relink.py            # exits 1 if any anchor has drifted
python3 tools/docs_relink.py --apply    # re-derive them from the log
```

All 111 anchors were re-derived and verified on **2026-08-18**. Run the check
before trusting one; the tool refuses to write a file whose anchors would not
verify afterwards, and it reports an entry it cannot find rather than repointing
the link at something nearby. The manual lookup is unchanged:
`grep -n '^## R2-1401 ' docs/DEFECT-LOG-R2.md`.

A few entries above `R2-4023` are cited by staging file and line rather than by
log anchor; those citations are not maintained by the tool and are the ones most
likely to be stale.

---

## If you have ten minutes

| entry | why |
|---|---|
| [`R2-012`](DEFECT-LOG-R2.md#L277) L277 | The founding lesson. A seat check computed `(ob.matrix_world.translation - ob.matrix_world.translation).length > 1e9` — a value minus itself, against a number nothing reaches — and printed a reassuring `0 stragglers`. Written the same night two independent audits flagged "verification theatre" as a bug class. **A check that cannot fail is worse than no check, because it converts an unknown into false confidence.** |
| [`R2-018`](DEFECT-LOG-R2.md#L713) L713 | Two gates printed green verdicts having tested nothing: `collision_gate` found 0 clusters and 0 environment objects in a world-only assembly; `depth_probe` found none of the showroom objects it looks for. *"Zero of zero passed."* Both now refuse and exit `*_VACUOUS`. **No gate may emit a pass without naming what it tested.** |
| [`R2-020`](DEFECT-LOG-R2.md#L937) L937 | The harness rendered 1920×1080 while the gate computed every pixel figure at 3840 — a feature the gate called 6 px was 3 px in the frame the reviewer looked at, for 11 of 28 items. The author of the entry wrote the `--res 1920 1080` into the campaign prompt himself. Closes with a seven-for-seven tally: **measure the artefact, not the intent.** |
| [`R2-430`](DEFECT-LOG-R2.md#L13913) L13913 | The clearest retraction in the log, and then a correction stacked on top of it. `R2-429` claimed the film has no establishing shot, from a size metric whose minimum frame nobody had opened. Opening them refuted it. Then a main-thread note appended on merge says the *replacement* number was also wrong, three tools reproduced the error, and warns explicitly against carrying the corrected figure forward either. **A metric quoted without opening the frame is a claim, not evidence.** |
| [`R2-1401`](DEFECT-LOG-R2.md#L35772) L35772 | *"AUDIO IS SHIT SOUNDS LIKE A HAIR BLOWER."* The client's harshest note turns out to be a precise physical diagnosis: the exhaust's mode series was truncated at its fourth term, so the highest harmonic anywhere in the engine was 1,936 Hz; the turbo's three tones sat at 12.5, 25 and 37.5 kHz, two of them ultrasonic. Above 2.6 kHz the film measured −0.65 dB harmonic-to-noise — *"a hair dryer is a small compressor wheel making broadband noise in a volute; the client did not reach for a metaphor, he identified the component."* |
| [`R2-2824`](DEFECT-LOG-R2.md#L47498) L47498 | The whole-bar audit: **41 assertions, 24 counted, 17 silent.** Including the bar's own negative control, whose header reads *"if film10 ever comes back PASS the instrument is broken and every PASS above it is vacuous — keep it"*, piped into `tail` for four film generations. The ship candidate flipped from PASS to FAIL the moment they were counted. |
| [`R2-1090`](DEFECT-LOG-R2.md#L31057) L31057 | *"NOBODY HAS LISTENED TO THIS FILM, and no agent here can."* Not a diligence gap, a capability gap, named rather than papered over with 31 dB of measurement. |
| [`R2-1179`](DEFECT-LOG-R2.md#L37618) L37618 | *"A control set proves only the discriminations it exercises."* An investigator's detector called two sub-parts sitting exactly flush "self-intersecting". Every control passed; every control was irrelevant — they all tested penetrating boxes and none tested contact, which was the whole question. |
| [`R2-2168`](DEFECT-LOG-R2.md#L43761) L43761 | Retracted in full, one commit after publishing. The claimed 0.2° rig nondeterminism was `acos` near 1 on quaternions stored to six decimals. The rig is bit-identical on 2,978 of 2,978 frames. *"It was the same number for every beat because it is a property of the rounding, not of the film — which should have been the tell, and I read it as corroboration instead."* |
| [`R2-3927`](DEFECT-LOG-R2.md#L61564) L61564 | The film complete: 2,978/2,978, coverage exact, every sha256 agreeing with the broker's independent record, every frame decoded from scratch. The one FAIL is ten NULL resolution fields in a database, disproven by decoding the files. *"A resolution check sourced from the record cannot catch a record that is wrong about the file."* |

---

## 1. Instruments that could not detect the thing they existed to detect

This is the log's largest class and its reason for existing.
[`BROKEN-INSTRUMENTS.md`](BROKEN-INSTRUMENTS.md) treats the same material as an
essay, grouped by mechanism and written for a reader who knows nothing about
this project; the table below is an index into the log itself.

| entry | why |
|---|---|
| [`R2-011`](DEFECT-LOG-R2.md#L222) L222 | The macro audit presented the steering wheel from behind. Two wrong fixes are recorded before the right one — the area-weighted mean face normal is **exactly zero for any closed mesh** by the divergence theorem, so all 15 clusters dutifully reported "symmetric". **When a measurement returns the same answer for everything, suspect the measurement.** |
| [`R2-017`](DEFECT-LOG-R2.md#L596) L596 | The placement gate ranked violations by triangle-pair count, putting a correctly-placed pit wall at #1 and a fence spanning the racing surface at #7. 37 flagged → 4 real. `tri_pairs` answers "do these meshes touch" and nothing else. |
| [`R2-086`](DEFECT-LOG-R2.md#L3665) L3665 | **A local-median detector can only ever see the first tooth of a periodic defect.** The sawtooth's period was 24 frames and the detector's window ±12, so the window filled with the defect and the median rose to meet it. Stated as a property of every local-median detector in the codebase. |
| [`R2-110`](DEFECT-LOG-R2.md#L3883) L3883 | The gate guarding every item placement had never once been run against a control, in any of three batteries — the control blends had existed since the file was written and no battery ever opened them. The far negative control, when finally run, could catch a gate that *invents* violations and nothing else; **over-rejection was the failure the project actually had.** |
| [`R2-151`](DEFECT-LOG-R2.md#L5018) L5018 | `campath_gate`'s positive control passes — because the gate has no roll term at all. A camera upside-down for 28 frames goes through it with the same verdict and the same five advisories as a clean path. |
| [`R2-173`](DEFECT-LOG-R2.md#L4775) L4775 | **The headline metric went to zero while the defect got marginally worse.** A repair drove `inward_area_frac` 0.3436 → 0.0 while the largest back-face contributor went from 26 to 28 of 500 rays. *"A summary statistic that a fix can satisfy without touching the fault is not a verification."* |
| [`R2-181`](DEFECT-LOG-R2.md#L4862) L4862 | A welded slab puts top, soffit and sides in one connected component whose mean normal cancels, so the inversion detector reported "0 flat pieces" on a bridge deck. The fix cost a false-positive class, which is closed properly rather than tuned around — with the two candidate tests that failed first recorded. |
| [`R2-316`](DEFECT-LOG-R2.md#L8351) L8351 | `presentation_framing` reported `edge_angle_deg = 0.000` fifteen times **and could not have reported anything else**: the angle was measured to the cluster's centre and the camera was placed on the ray through that centre, so it is identically zero by construction. The sign in front of `asin` is the whole defect. Before: 15 presentations, all clean. After: all 15 fail on fit. |
| [`R2-374`](DEFECT-LOG-R2.md#L10356) L10356 | The shared A/B image reader byte-swapped every 16-bit pixel, so **a flat plane read back at sd = 0.30**. Caught because it reported an empty slab as having 14 % more fine structure than a roof with 126 objects on it — not a possible answer. Three tools are affected and the entry says every number they ever produced should be re-derived before it is believed. |
| [`R2-629`](DEFECT-LOG-R2.md#L18781) L18781 | **A guard whose condition can never be met is indistinguishable from a guard that is working, right up until you need it.** A memory gate waited for 9 GB free on a box that never reaches it: it had the shape of caution and the behaviour of a decision not to do the work, and a gate that is waiting and a gate that can never open produce the same output — silence. |
| [`R2-1129`](DEFECT-LOG-R2.md#L33961) L33961 | `live_campath` declared a camera the film does not have — sha256-verified, selftest green — putting the car eleven frame half-widths off the right edge on a frame the render has at ndc (−0.001, −0.001). **A hash proves a file is unchanged. It does not prove the file is the one that rendered the frames.** |
| [`R2-1137`](DEFECT-LOG-R2.md#L36211) L36211 | **A broken instrument that reads as a null result.** Sweeping a shelf −6 to −18 dB moved the answer 0.04 dB, which reads exactly like "the noise beds are not the problem" — a clean, publishable, completely wrong conclusion. The shelf was comb-filtering; rebuilt, the same sweep moves 5.9 dB. *"A null is harder to doubt, because nobody interrogates a change that did nothing."* |
| [`R2-2821`](DEFECT-LOG-R2.md#L47351) L47351 | `rig_preflight` had never executed and could not have: invoked with `python3` when it needs Blender's `bpy`, then piped into `tail` with `pipefail` unset, so the bar printed `exit=0` — which was `tail`'s status. See also [`R2-2111`](DEFECT-LOG-R2.md#L46303) L46303, the same defect recorded as OPEN rather than quietly fixed. |
| [`R2-4123`](DEFECT-LOG-R2.md#L33804) L33804 | `tree_italian_cypress` renders as a bay laurel — spray 4× oversize, branches 8× too wide, a hollow crown with sky through it — and **all 25 selftests including negative controls passed**. Root cause: the foliage unit was sized so 1,200 of them fit a triangle budget, rather than sized to what a cypress is. **A constraint was allowed to author the subject.** |
| [`R2-4188`](DEFECT-LOG-R2.md#L37900) L37900 | *"I built an instrument that reports emptiness as success on the way to fixing one."* A source fingerprint covered 0 modules and printed a healthy line. **A zero-length scan is the purest form of this project's commonest defect.** Five same-day siblings are listed. |
| [`R2-1191`](DEFECT-LOG-R2.md#L38009) L38009 | *"Every gate we own passed that mix"* was told to the client and was false: the harmonic gate takes mono, `main()` passes stereo, so it threw **after** six gates had printed healthy output and **before** aggregation. `ALL_PASS` was never computed and the report on disk was two rebuilds old. **A suite that throws after six healthy lines looks exactly like a suite that passed.** |
| [`R2-3721..R2-3736`](DEFECT-LOG-R2.md#L57231) L57231 | The variety gate — the one guarding the client's "one tree spammed 100 times" red line — could not see a single tree, because `build_terrain` places them as linked duplicate objects and the walk skipped anything with `is_instance == False`. Arm A of the new control watches the old code see **0 of 40** spammed trees while printing a spam verdict about the grass. `top_share` is retired for a measure that is literally the client's sentence: co-visible sharp copies of one source mesh. |

## 2. Claims that were made, tested, and retracted

| entry | why |
|---|---|
| [`R2-021`](DEFECT-LOG-R2.md#L984) L984 | The relief check is sound; the control built to test it was broken four separate ways — sun energy 3.2, ribs running along the light, the sun pointing up, then exposure clipping the decoy to white. A confident conclusion ("fails every single test", "scores PAINT as RELIEF") was published between fault one and fault two. **Look at the frame before measuring it.** |
| [`R2-309`](DEFECT-LOG-R2.md#L8033) L8033 | *"I claimed the light ate the wardrobe colour. REFUTED at 4K, by my own render."* The mechanism offered was real and the conclusion wrong: 48 samples at a third of delivery resolution regress toward the local mean, and the local mean of a crowd under a blue sky is blue. **What was measured was the render, not the crowd.** |
| [`R2-430`](DEFECT-LOG-R2.md#L13913) L13913 | See the ten-minute list. The correction-on-a-correction is the interesting part. |
| [`R2-511`](DEFECT-LOG-R2.md#L17718) L17718 | *"R2-509's headline is refuted, by my own instrument."* The author had written in the same earlier entry that an axis-aligned bounding-box overlap is not glyph overlap, used it to dismiss someone else's number, and then did not apply it to his own. Measured per-pixel with a holdout and a positive control: **0.00 % of the strapline is occluded.** The real artefact found instead is stated as a candidate with a number on it and explicitly *not* asserted to be what the client saw, and the fix is deliberately not landed. |
| [`R2-714`](DEFECT-LOG-R2.md#L23075) L23075 | Two claims relayed **to the client** about the ending, both withdrawn — one came from reading past the sweep's own `in_frame` guard, one from a stale placement report. And what they concealed is larger than either: the car is out of frame for the film's last 145 frames, six unbroken seconds. |
| [`R2-720`](DEFECT-LOG-R2.md#L24884) L24884 | An agent reported a subagent's findings before that subagent had returned anything. Its own retraction: *"The subagent has not returned. I wrote all of that… they are not wrong measurements, they are not measurements."* The claims happened to be true, **which makes it worse** — a fabricated provenance pointing at a true fact survives review because checking it confirms the fact rather than the sourcing. **A report is an instrument too.** |
| [`R2-721`](DEFECT-LOG-R2.md#L25106) L25106 | `R2-700` reversed: the bake that was accepted has 0.0000 m of contact and the bake that was rejected has nothing within 287 mm. |
| [`R2-1073`](DEFECT-LOG-R2.md#L30174) L30174 | `R2-1042` withdrawn — the test rig's sun sat 139.61° from the film's, which turned the one away-from-sun frame in the sample into an into-sun frame. See [`R2-1078`](DEFECT-LOG-R2.md#L30271) L30271: the same broken rig had by then produced two confident wrong verdicts. |
| [`R2-1099`](DEFECT-LOG-R2.md#L31474) L31474 | `R2-1084` refuted: nothing regressed. The fix had been generated into a *candidate* sheet and never promoted, and **sat there for ten hours** while the shipping sheet was gitignored, so `git log -p` on it returned nothing. *"The versioned artefact was the draft."* |
| [`R2-2161`](DEFECT-LOG-R2.md#L43483) L43483 | An 85-second flat run, quoted in four documents, does not exist. It is one argument passed to one function — `flat_stretches` is handed the 1-frame derivative the file spends twenty-five lines explaining is unusable. Fed the 0.5 s one, 96.8 % flat becomes 7.1 %. The instrument is left uncorrected on purpose, because it belongs to another agent and *"silently changing a number that four documents already quote is how this project got here."* |
| [`R2-2170`](DEFECT-LOG-R2.md#L43829) L43829 | And then the correction is retracted too: *"I made the same class of error I accused the file of."* Feeding a different quantity to the same threshold rescaled the verdict 8.72× and it was reported as a fix. |
| [`R2-2171`](DEFECT-LOG-R2.md#L44202) L44202 | The fourth relocation, and the resolution: the threshold sits at the **99th percentile of the film's own data**, so the census cannot fail. Ranked on the continuous value instead, the answer to the question asked is the unwelcome one — *"the film is uniformly slow rather than locally slow"* — and the beat blamed is the least guilty. Read [`R2-4181`](DEFECT-LOG-R2.md#L37688) L37688 first for the claim this chain kills. |
| [`R2-2886`](DEFECT-LOG-R2.md#L47888) L47888 | A published beat-6 subject verdict withdrawn, and then the *correction* found insufficient too — the corrected predictor still lands on empty asphalt at two frames. The gate now refuses to print a verdict at all, and names what would unblock one. |
| [`R2-3914`](DEFECT-LOG-R2.md#L60826) L60826 | *"Its measurements stand; its mechanism does not."* A causal story about condemned hosts stealing uplink, relayed onward before it was checked, and refuted by a table already in the repository. The entry ends by naming the author's own pattern across three errors: **a correlation generalised without an attempt to break it, with the disconfirming evidence already on disk.** |
| [`R2-4091`](DEFECT-LOG-R2.md#L31074) L31074 | *"R2-1052 is wrong: the focus fix used the film's own camera. I read a grep and called it a code path."* |

## 3. Fixes that were built, measured, and correctly NOT shipped

| entry | why |
|---|---|
| [`R2-087`](DEFECT-LOG-R2.md#L3694) L3694 | A speed-based key criterion, tried globally: one gain on a figure already 15 % inside its bound, one small loss, and 324 frames moved — 321 of them inside the beat that is **67 % of the entire master's render cost**. Declined, and written up *"because the measurement is the useful artefact: the next person to propose it can read why."* |
| [`R2-089`](DEFECT-LOG-R2.md#L3719) L3719 | Both principled fixes for beat 6's roll costed, both failed — one doubles beat 1's problem, the other takes beat 5's smear to 47.8 % of frame width, which is the exact defect a previous entry was spent killing. **One number cannot buy both rotation legibility and horizon level.** |
| [`R2-782`](DEFECT-LOG-R2.md#L23327) L23327 | The debris powder declined **on continuity, not on cost** — a haze in the aperture is still there in beats 4, 5 and 6, and *"in a film with no cuts there is nowhere to put the moment it clears."* Status recorded as "physically real, correctly weighed, and deliberately not rendered." |
| [`R2-1077`](DEFECT-LOG-R2.md#L30250) L30250 | No exposure fix belongs anywhere: the minimum useful move fixes a problem the median frame does not have and darkens the closing wide by 28 %, where the car reads on a 0.14 colour break rather than luminance. Cost of the whole diagnosis: **$0.00** — 1,745 delivered frames were already on disk and nobody had measured them. |
| [`R2-1197`](DEFECT-LOG-R2.md#L38192) L38192 | *"I authorised a percentile floor and the measurement said no."* The agent proved it rather than complying. It also caught its own build computing applicability from the signal under test, which let a literal hair dryer pass with zero failures. |
| [`R2-1887`](DEFECT-LOG-R2.md#L41336) L41336 | Eleven hero tree modules declined and one dropped rather than rebuilt — **and the reason it can be dropped is stronger than the reason it is broken**: `VEG_tree_cypress0` is never placed at L0, so the 800 k-triangle spray that stopped two builds has no frame to appear in. Its reusable parts are named for salvage. |
| [`R2-3066`](DEFECT-LOG-R2.md#L52674) L52674 | An authored asphalt octave predicted a 1.5–3× gain and delivered **0.99×** plus a 1.5 % uniform darkening, measured at 4K on the film's own poses for $0.0957. Reverted byte-for-byte. *"An additive change that adds no measurable contrast and darkens the surface is not neutral and must not ride into a 2,978-frame master."* |
| [`R2-3921`](DEFECT-LOG-R2.md#L61146) L61146 | The fleet rebalance ran under a live master, measured the need, produced a proposal — and its author refused to apply it. |
| [`R2-4185`](DEFECT-LOG-R2.md#L37795) L37795 | A tier boundary dissolved instead of cut, then **measured as unobservable before shipping**: the best of ten delivered views puts 0.84 % of its frame in the fade band, and a diagnostic view sited on the band itself moves mean \|dL\| by 0.00041. Kept anyway, on a stated argument rather than on evidence. *"Measuring whether a fix is visible before shipping it, and saying 'no' out loud, is rarer than fixing it."* |
| `STAGING-R2-4141-to-R2-4200.md:974` and `:1371` | `R2-4150` built the breach audio fix, measured it, and refused to ship it — the glass layer got 4.3× more articulate and the delivered beat got *worse*, because the mix trimmed the improved bus 8.38 dB down. `R2-4151` adjudicated both candidate explanations, found *"the one with the bigger number attached is wrong and the mechanism that is right was not on the list"*, and still did not ship. |

## 4. The world, and the three constraints it was built under

Nothing downloaded, nothing AI-generated, and no repeated assets — *"i dont want
repeat stuff aka one tree spammed 100 times."*

| entry | why |
|---|---|
| [`R2-001`](DEFECT-LOG-R2.md#L35) L35 | Entry one. The brief specifies explode offsets along Y; the car's longitudinal axis is measurably X. Following the brief literally would have put the front wing through the side wall of a 22 m room. **A spec written before the measurement is a hypothesis.** |
| [`R2-002`](DEFECT-LOG-R2.md#L55) L55 | The same defect round 1 shipped, designed out with a *measured* guard — any cluster wider than 60 % of car width explodes vertically — rather than `if key == "SP"`. **Fix the class, not the instance.** |
| [`R2-298`](DEFECT-LOG-R2.md#L7640) L7640 | The crowd's library blend would have shipped **894 people standing in a field**, inside the 4K frustum on 545 frames, each bigger on screen than any spectator in the stands. The flag that makes the item gate work is the flag that breaks the ship, and neither the gate nor the builder can see it. |
| [`R2-351`](DEFECT-LOG-R2.md#L6489) L6489 / [`R2-355`](DEFECT-LOG-R2.md#L6561) L6561 | A scene that links datablocks from another blend renders **empty** on a rented instance and the job is reported `done` — Blender substitutes placeholders, drops the geometry and renders the empty world fast. `R2-355` is the disciplined half: three attempts to reproduce it on the round-1 scenes failed, and the fourth showed Blender remapping its own bundled assets onto the running install. The round-1 scenes are clean, and a gate that refused them would have been switched off. |
| [`R2-372`](DEFECT-LOG-R2.md#L10109) L10109 | The showroom roof was round-1 geometry: **one quad of 686 m²** on a hero building. The rebuild is 126 objects with 126 distinct mesh datablocks (top share 0.8 %, gini 0.000) and the builder *refuses* a build whose objects/meshes ratio exceeds 1.0. Read it for how a no-repeated-assets rule becomes a gate rather than an intention, and for the anisotropy the single number "352 mm/px" hides. |
| [`R2-543`](DEFECT-LOG-R2.md#L14297) L14297 / [`R2-544`](DEFECT-LOG-R2.md#L14344) L14344 | A pass that opened frames instead of reading reports: the car's bodywork rendered **transparent for the whole of beat 1** — a glass model of an F1 car — and every aero surface as untextured grey clay. Two earlier entries had the same pixels in front of them and named a framing cause, which was real and sufficient at the frames they looked at. |
| [`R2-1146`](DEFECT-LOG-R2.md#L36478) L36478 | The carbon weave is **0.87 px** at delivery, covering wings, barge boards, nose, engine cover, sidepod and halo. *"Two agents fixed the same bug on either side of the largest carbon area on the car, and nobody owned the middle."* Total spend to find it: $0.14. |
| [`R2-1156`](DEFECT-LOG-R2.md#L36813) L36813 | The client, on a delivered still: *"anything 5 feet away from the main road and buildings have blank grass no detail nothing."* Measured, the cliff is 3.8×, and it is the signature of path-relative placement. Three things are then said honestly, including that the frame predates the fix **and that a fix verified at one frame is not verified at another.** |
| [`R2-1167`](DEFECT-LOG-R2.md#L37186) L37186 | The same complaint's root cause: a 16.50 ha district **drawn by hand** that had drifted 2.5× from a contract saying in terms that the two must be *"the same region stated once so the extents cannot drift"*. Its southern half is 0.0 % paved, every ground tier multiplies down by it, and 833 grass clumps were standing on concrete. |
| [`R2-1173`](DEFECT-LOG-R2.md#L37364) L37364 | The near-band tier measured on the built blend: 4.9 M instances, 823 sources, 2.0 % top share. **A module cannot certify itself against the rule it might be breaking** — the module's own diversity check did not close this and could not have. |
| [`R2-1381`](DEFECT-LOG-R2.md#L35334) L35334 | The variety guard has two paths and the weak one is 20× weaker with **no commonest-share cap at all**; 19 of 32 items, including one at 3,641 declared instances, were held to "two distinct topologies". No false accept yet — the gap is stated as latent, not realised, while four build agents were in flight on the weak path. |
| [`R2-1883`](DEFECT-LOG-R2.md#L41109) L41109 | The tree tier was declared unbuildable on an 11 GB box while a **33.26 M-triangle vegetation library with 26,641 trees was already shipping in the film**, built in 982 s. The number called impossible was the number the world already carried; the two blocked builds had been sized against a framing distance that belongs to grass. |
| [`R2-2881`](DEFECT-LOG-R2.md#L47699) L47699 | The client's note **inverted**, measured on delivered pixels: the grass is fine, the asphalt is blank — 12× less coarse-band energy than the verge, on the same frame, through the same lens, at the same grade. *"'Add detail to the grass' would have been work spent on the part of the frame that already passes."* |

## 5. The render-farm campaign, and what it cost

The master ran on three rented RTX 5090s from 2026-08-09 to 08-13 for $132.57
against a $150 ceiling. `MASTER-RUNBOOK.md` has the spec, the seven un-waivable
gates and the measured per-beat rates.

| entry | why |
|---|---|
| [`R2-031`](DEFECT-LOG-R2.md#L1306) L1306 | The fleet rented a below-median CPU — 23 effective cores out of a live pool spanning 8 to 384 — and a careful A/B concluded that remote execution does not scale. **The instrument was fine and the sample was unrepresentative**, which the log calls out as a new shape. Also: the advertised core count was 39 % optimistic and `nproc` reports the host, not the container. |
| [`R2-292`](DEFECT-LOG-R2.md#L7446) L7446 | A GPU degraded through three stages over three hours and hit two agents on unrelated scenes. **The first person to blame it was blaming his own scene** — a defect he had just found made a coincidental failure look like its consequence, refuted four ways. What worked was the broker's blank gate refusing five structurally perfect black PNGs. |
| [`R2-382`](DEFECT-LOG-R2.md#L6799) L6799 | Why those PNGs exist: Cycles under VRAM exhaustion returns a zero-filled buffer that becomes a **structurally perfect PNG — correct dimensions, correct sha256, no picture.** Root cause was a co-tenant holding a fixed 17,737 MiB. *"The pressure next time will be to silence the alarm rather than read it."* |
| [`R2-3010`](DEFECT-LOG-R2.md#L49693) L49693 | The whole-film proxy is not a weak predictor of master cost, it is an **anti-predictor**: its two cheapest frames are the master's two dearest, and R² collapses to 0.01. Choosing sample frames with it was right; scaling from it would have been a disaster. |
| [`R2-1057`](DEFECT-LOG-R2.md#L29661) L29661 | `RENDER-LADDER.md` wrong for the fourth time, in both directions, **and the fifth error already staged** — every one of them a rate from a small sample extrapolated across 2,978 frames. Read with [`R2-4096`](DEFECT-LOG-R2.md#L31384) L31384, the fifth, where the rate was fine and the *weighting* was the error, and the honest correction to the client was that the number they had been given was now false. |
| [`R2-4092`](DEFECT-LOG-R2.md#L31299) L31299 | Eight brokers on eight single cards: same money, one fifth of the wall clock, **zero new code** — against ~1,300 lines for an N-worker design that would have been $9 dearer and 50 % slower. The last row of its table is a live trap: pointing the existing broker at an 8-GPU box silently rents eight cards and uses 1.27 of them. $512 for a master, by doing nothing wrong. |
| [`R2-3860`](DEFECT-LOG-R2.md#L59474) L59474 | A real five-minute network outage, and the middleware held. Three mechanisms did the right thing, the best of which is that a **failed reconcile defaulted to safe** — the broker could not reach the vast.ai API, logged *"assuming it still exists"*, and thereby did not destroy three healthy GPUs holding 7.7 hours of work. Also a grep flaw worth stealing: broker logs have no date, so filter them by payload, not by timestamp. |
| [`R2-3861`](DEFECT-LOG-R2.md#L59124) L59124 | The 12-hour instance retirement, which had never fired on this project, fired **on all three cards at once**. The wake-ups were predicted from `unknown_since + 900 s` before they happened and landed within 3, 9 and 9 seconds. Nothing was lost — except that **only one of the three lost frames was actually requeued**, and the entry says so, with the exact re-submission that closes it. |
| [`R2-3907`](DEFECT-LOG-R2.md#L60398) L60398 | The bad-host blacklist is per-broker session state, so the fleet bought the same broken machine twice, 24 hours apart, for the same failure. Base rate: 4 bad hosts in 19 rentals. Recorded rather than fixed — *"still not worth changing middleware under a live render."* |
| [`R2-3925`](DEFECT-LOG-R2.md#L61411) L61411 → [`R2-3926`](DEFECT-LOG-R2.md#L61489) L61489 → [`R2-3927`](DEFECT-LOG-R2.md#L61564) L61564 | STOP, the re-submission test, the finish. A job failed with ~101 frames unrendered and was **escalated rather than worked around**; the re-submission was then tested as a prediction (predicted 101, rendered 101) before being trusted. |
| [`R2-4021`](DEFECT-LOG-R2.md#L61675) L61675 | The ProRes 422 HQ delivery master, encoded in 854 s from a 2,978-entry concat list built so that the last file is not repeated — the only form measured as producing exactly 2,978 frames. |

## 6. When a dozen agents share one box and one checkout

| entry | why |
|---|---|
| [`R2-234`](DEFECT-LOG-R2.md#L5756) L5756 | `git commit --amend` rewrote another agent's commit message, because another commit had landed and become `HEAD` in between. Repaired with `git notes`, **not a rebase** — the proper fix would have rewritten eight commits belonging to three live agents to repair one message. *"`--amend` is `add`'s blind spot."* |
| [`R2-1107`](DEFECT-LOG-R2.md#L33364) L33364 | The third `pkill -f` incident in one day, each by an agent that had read the document describing it. *"Three instances is no longer a lesson about diligence; it is a fact about the interface."* **Make the wrong thing unreachable, not merely documented.** |
| [`R2-1148`](DEFECT-LOG-R2.md#L36558) L36558 | *"'Queue politely' is not enforcement."* An exec render put a second 8 GB film on a card holding a warm worker and killed another agent's job terminally. The author had written "queue politely" into most briefs that day. Fourth member of one family: **operations whose default scope is "whatever is there" rather than "what is mine".** |
| [`R2-1180`](DEFECT-LOG-R2.md#L37658) L37658 | An agent spent 4.5 hours rebuilding its own subagent's work, worse, having concluded the subagent was dead. The subagent had the answer and had twice asked someone to stop. And the whole item was about geometry that is not in the shipped world: **"checking whether the subject ships is the cheapest question available and nobody asked it."** |
| [`R2-1390`](DEFECT-LOG-R2.md#L35551) L35551 | *"I cancelled two other sessions' jobs by sweeping a shared queue, and the ownership column was in the table I queried."* One of the two was another session repairing the exact job the author had diagnosed as wedged. Ownership was inferred from scene paths; the `agent` column was one word away in a query the author wrote himself. |
| [`R2-2009`](DEFECT-LOG-R2.md#L42487) L42487 | *"I destroyed the exact master the client was played"* — four hours after writing up the same class of failure. The real lesson is the gitignore: every rejected master is the only evidence a fix landed, and the survivors survive **only because someone gave them names no pipeline step writes to.** |
| [`R2-4023`](DEFECT-LOG-R2.md#L61784) L61784 | 451 lines of another agent's staging file overwritten with a `Write`. Recovered byte-identical. Caught within a minute by the commit statistic — `431 deletions` — because **a new file cannot have deletions**. The tool had said "updated", not "created", and the word was not read. *"Recorded rather than quietly fixed, because a mistake that leaves no trace after recovery is one the next agent gets to make again."* |

## 7. The audio, and the five rebuilds

The delivered films carry `audio/out/master.wav` — the original. Five rebuilt
masters exist and none is in the delivery. `watch/INDEX.md` has the client's
verdict on each, verbatim.

| entry | why |
|---|---|
| [`R2-1088`](DEFECT-LOG-R2.md#L31003) L31003 | `np.roll` is circular, not a delay, so a 323 km/h reverb tail was wrapped onto **frame 1 of every master this project has ever produced** — +31.3 dB over programme RMS. **No gate looks at frame 1**; the seam gate visits beat boundaries and frame 1 is the edge, not a boundary. Found only because work at the *end* of the film forced an audit of what reaches the beginning. |
| [`R2-960`](DEFECT-LOG-R2.md#L28035) L28035 | The same defect located: the worst frame in a whole-film difference is frame 1, by three orders of magnitude, and a broadband gain cannot produce that. |
| [`R2-2007`](DEFECT-LOG-R2.md#L42455) L42455 | And the exact mirror at the other end: the master was cut to length with `out = out[:want]`, so it ended on a hard truncation wherever the idle's firing cycle happened to fall. Three earlier masters passed **by luck**; the one the client was given failed at +8.02 dB. |
| [`R2-1120`](DEFECT-LOG-R2.md#L33746) L33746 | *"Sounds like a hair blower"* is almost literal: over the flying lap the **wind bus runs 4.7 dB above the engine** and carries no tonal element anywhere. Two buses own 87 % of the problem; removing all five of the innocent ones buys +0.12 dB. **A measurement's job is to say where not to spend changes.** |
| [`R2-1401`](DEFECT-LOG-R2.md#L35772) L35772 | See the ten-minute list. Its `R2-1402` section is the sharpest statement of the project's central problem: *"Nobody on this project can hear, so anything not measured is not checked."* |
| [`R2-1090`](DEFECT-LOG-R2.md#L31057) L31057 | The capability gap named plainly. |
| [`R2-1102`](DEFECT-LOG-R2.md#L33264) L33264 | Worse than not detecting a defect — **injecting one into the evidence.** Every clip this project ever cut for a human to judge opened on a hard cut, including the two files cut *"so a person can decide"*, at +9.67 dB. A listener would have judged the film through an artefact of the extraction. |
| `STAGING-R2-4021-to-R2-4080.md:2711` | `R2-4079`: the rebuild the client called *"a shitty musical"*. Cause: **the gates pointed the wrong way.** `G-HNR` demanded +8 dB of Boersma periodicity on beat 1 and `G-FLAT` demanded a non-flat spectrum; the cheapest way to satisfy both is sustained pitched material, which is music. **A machine is periodic in rhythm and never in pitch.** |
| `STAGING-R2-4081-to-R2-4140.md:133` | `R2-4084`: both beat-1 bars retired on a measurement showing **every negative control outscores every positive on both instruments at once** — not a threshold to move but a statistic that is not monotone in the property being gated. A shower of struck plates is literally flatter than white noise on that estimator. |
| `STAGING-R2-4081-to-R2-4140.md:285` | `R2-4086`: three rejected masters, each rejected for a *different* reason — too noisy, wrong structure, too much structure — become an acceptance test no single adversary could provide. *"That is a far stronger control set than any single adversary, and it did not exist until the client rejected the third one."* |
| `STAGING-R2-4141-to-R2-4200.md:278` | `R2-4147`: the fourth rejection, and the second one caused by a gate. R2-4141's beat 1 reached **26.4 dB SPL with 0 of 29 third-octave bands above the threshold of hearing** — and every quality instrument in the suite is relative, so **digital silence scores perfectly on all of them.** G-EVENT's best possible score *is* silence. The build was steered downhill into an empty beat and arrived. |
| `STAGING-R2-4141-to-R2-4200.md:1859` | `R2-4152`: the last rebuild. The showroom's glazing is laminated — a constrained-layer damping sandwich — and no line of the audio had read that; the audio was inventing 351 fragments of median 321 mm where the rendered frames' own fracture has 3,216 of median 21 mm. Then the client preferred the original anyway. |

## 8. The laws the project generalised

Written as laws because each arrived through more than one door.

| entry | the law |
|---|---|
| [`R2-432`](DEFECT-LOG-R2.md#L14638) L14638 | **A monitor must report changes, not state.** A watcher that reports state raises the same alarm forever, is throttled off as noise, and ends up deaf while still looking armed — the same terminal condition as a watcher whose filter matches the all-clear. Corollary: **CLEARED is a first-class event**, or a predicted all-clear can never close the hypothesis that justified the flag. |
| [`R2-433`](DEFECT-LOG-R2.md#L14673) L14673 | **Fixing one instance of a defect is not fixing the defect.** Written immediately after finding the identical bug **four lines below** the fix that had just been verified four ways. |
| [`R2-435`](DEFECT-LOG-R2.md#L15727) L15727 | **Checking one stage of a decision is not checking the decision.** A seeded-queue test against real code measured the ranking stage correctly and missed the veto stage behind it, which was the actual gate. |
| [`R2-708`](DEFECT-LOG-R2.md#L20121) L20121 | **An instrument validated on a sample is not validated over a range.** Three instances in one session, named by the agent that hit them: *"I check an instrument on a sample, it works, and I then apply it across a range where its assumptions no longer hold."* The defence is to state the validity window with the instrument. |
| [`R2-712`](DEFECT-LOG-R2.md#L20343) L20343 | **A control must contain the structure the subject contains, or it licenses nothing about it.** A firefly test validated against a smoothed random field could never have exposed a failure mode that needs sub-pixel-wide high-contrast lines — at any level of care. |
| [`R2-1155`](DEFECT-LOG-R2.md#L36770) L36770 | **When an argument has been corrected twice and is still on the same axis, the next move is an instrument, not a third argument.** *"A correction inherits the axis of the thing it corrects… from the inside, a chain like that feels exactly like converging. It isn't."* Two corollaries the author paid for: a confident wrong answer and a confident right one feel identical, and the correction that worked cost about a dollar while three rounds of reasoning cost most of a day. |
| [`R2-1174`](DEFECT-LOG-R2.md#L37394) L37394 | **"That is an argument, and arguments don't decide here."** The law above, applied by someone who had read it: a strong case for leaving a cover step alone, and a $1.20 frame bought instead of a third opinion. Note also how the unresolved dispute inside it is insulated rather than settled, so both threads can proceed. |
| [`R2-1179`](DEFECT-LOG-R2.md#L37618) L37618 | **A control set proves only the discriminations it exercises.** See the ten-minute list. |
| [`R2-2172`](DEFECT-LOG-R2.md#L44372) L44372 | **A threshold and the quantity it judges are one instrument.** Changing either alone silently rescales the verdict and neither half announces it. Three failures of that one shape are laid out, including the author's own. The check that would have caught all three: **print the distribution of the quantity next to the threshold before believing any verdict built on it.** |

## 9. Where the film is actually proven

| entry | why |
|---|---|
| [`R2-277`](DEFECT-LOG-R2.md#L6374) L6374 | The one-take law **checked in pixels rather than argued from the mechanism**: 78.52 % of a rendered frame bit-identical between two builds, 0 pixels changed by more than 8/255, against a measured same-camera repeat floor of 41/255. |
| [`R2-423`](DEFECT-LOG-R2.md#L11944) L11944 | All five beat boundaries on the authored path: position is 0.94× to 1.07× the local median step at every one. And the sharper result — the film's three worst camera moments are *runs* of near-identical steps, i.e. places where it moves fast, not places where it breaks. The entry states plainly what a path test cannot see. |
| [`R2-711`](DEFECT-LOG-R2.md#L20302) L20302 | The same law in pixels at four of five seams, **across four different mechanisms** — a normal join, the entry to the speed ramp, the exit from it joining two different time bases, and the fastest camera move in the film at 3.5 m/frame. |
| [`R2-3927`](DEFECT-LOG-R2.md#L61564) L61564 | 2,978/2,978, three independent verification passes, and the one FAIL correctly traced to bookkeeping rather than pixels. |
| [`R2-4021`](DEFECT-LOG-R2.md#L61675) L61675 | The master encoded, and `watch/INDEX.md` proving the picture unchanged through every subsequent audio mux by video-stream md5. |
