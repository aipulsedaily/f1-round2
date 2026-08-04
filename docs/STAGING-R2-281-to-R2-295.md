
### Beat 3 at f0880 — the same direction, and one honest caveat

| f0880, 1920 × 1080, 256 spp | changed > 8/255 | > 32/255 | mean &#124;Δ&#124; |
|---|---|---|---|
| pre-R6 → R6 | 6.396 % | 3.199 % | 4.188/255 |
| **R6 → re-bake** | **32.570 %** | **10.585 %** | **12.569/255** |

`render/r2281/COMPARE_f0880_preR6_R6_REBAKE.png`. Panels 1 and 2 both show the
car behind a heavy, largely intact dark grid. **Panel 3 has no grid over the
car**: the transom that crossed it has gone, the vertical member is displaced,
and a large bright aluminium member is tumbling above it.

**The caveat, because it is a real trade and not mine to settle.** The two shed
segments R2-276 celebrated — *"the size of the car's rear wing, turning over in
the aperture"* — are **less prominent** at f0880 than in R6, because they are
the pieces the car sweeps downrange (R2-290). What replaces them is a more
completely opened wall and a larger member falling. **That is a change of
character, not a strict improvement, and it should be judged looking at the
frame by whoever owns beat 3.** The measurement says the event is five times
bigger; it cannot say it is five times better.

---

## R2-298 — three corrections the recovered frames force, two of them to my own conclusions

The eight-frame set was re-rendered on a **verified-healthy** GPU, including the
three the matched-96 verdict was computed on. Those came back at identical
statistics (mean 0.39049, sd 0.11416), and re-running the verdict against the
replacement files reproduces every published number to the third decimal —
WOUND_bridged **0.03963 → 0.00908 at 51.55 %** becomes **0.03965 → 0.00908 at
51.86 %**. **The verdict stands.** What changes is three things around it.

### 1. R2-292's mechanism was wrong, and it was my second wrong diagnosis in the same place

I said the instance "degraded progressively" and that the failures "cluster in
TIME, not by scene, agent, sample count or persistent-data setting". **The
clustering is by memory size, not time.** Sorted by effective megapixels, every
full-frame 4K job failed and **every bordered (0.07 Mpx) or 1080p job succeeded**
— continuously, through the same window, right to the end. That is why the box
kept looking alive: a cheap render always passed.

The cause was measured over SSH rather than inferred: **the instance was not a
dedicated card.** 31,165 MiB of 32,607 MiB in use while our Blender held 13,428
MiB — a foreign process outside our PID namespace sat rock-steady at **~17.7 GB**.
We had ~14.9 GB of a 32 GB card, and a 4K frame of these scenes needs ~13.4 GB:
**98.6 % occupancy, ~1.4 GB of headroom.** `persistent_data=True` holding a
previous scene's BVH across a scene switch is what tipped it, the OOM poisoned
the CUDA context, and the byte-identical black frames are the denoiser running
on a garbage buffer — which is exactly why they were identical across unrelated
scenes.

**So I was wrong twice about the same failure**: first that my own debris field
caused it, then that it was time-ordered decay. Both times the correction came
from someone with no stake in the answer, and the second time it came with a
VRAM measurement instead of an argument.

### 2. The control failures are geometry, not the debris field

R2-294 attributed the untouched bay-groups' 5.21 % and 4.20 % to the frozen
debris field crossing them. **That is wrong**, and R2-296's finding is the whole
explanation. Audited against the newly-released members:

| control region | newly-released geometry inside it | f2978, **real re-bake, 256 spp** |
|---|---|---|
| CTL_UNTOUCHED_bays789 | bay 7's transom | 4.39 % |
| CTL_UNTOUCHED_bays012 | bay 2's transom | 4.78 % |
| **CTL_UNTOUCHED_bays01** | **none** | **0.0652 %** |

**Bays 0–1 hold at 0.0652 % against a 0.0000 % floor on the real re-bake — the
one with the full 88 m debris field in it.** If the debris were contaminating
the controls it would contaminate that one too. It does not. The two failures
are the fix's blast radius growing, exactly and only.

### 3. The floor is 0.0000 %, not 1.77 %

The 256-sample verdict quoted a repeat floor of 1.77 % in the wound. That floor
came from the **pre-R6** build's repeat pair, rendered on the starved box. The
diagnostic's **own** repeat, both frames on the healthy GPU, gives:

> **0.0000 % at 8/255 in every region, sky 0.0004 %.**

So the verdict's 11.33 % in the wound stands against a measured zero, not
against 1.77 %.

---

## R2-299 — f2940 reproduces R2-278 exactly, on my own data, in the direction R2-278 warned about

The corrected frame against R6 at **f2940**, where the wall is 9.69 px/m and a
75 mm transom is **0.58 px**:

| | `grid_contrast` WOUND_bridged | changed > 8/255 |
|---|---|---|
| R2-278's record, DEMO vs R6 | 0.02572 → 0.02672 (**blind**) | 12.44 % |
| **R2-281 corrected frame vs R6** | **0.02572 → 0.02688** (**blind**) | **12.98 %** |
| CTL_UNTOUCHED_bays01 | 0.03937 → 0.03910 | **0.0000 %** |
| sky | — | **0.0000 %** |

`grid_contrast` moves **upward by 0.5 %** on a frame where 12.98 % of the wound's
pixels changed at 8/255 with a perfectly clean control and a clean sky. It is
sub-pixel and the local baseline is sampling the same antialiased smear as the
line, precisely as R2-278 sets out.

**The instruction to let the picture and the change fraction win where they
disagree with `grid_contrast` is not a general caution — it is load-bearing on
this exact frame**, and my own numbers would have reported "no change at f2940"
if I had taken the metric at its word. The corrected frame tracks the
demonstrator here too: 12.98 % against 12.44 %.

### The real re-bake at full 256 samples, for completeness

Now that it exists (it never rendered at 256 on the failing box):

| | `grid_contrast` | changed > 8/255 | bays01 control |
|---|---|---|---|
| re-bake, 96 spp | 0.03963 → 0.00908 | 51.55 % | — |
| **re-bake, 256 spp** | **0.03675 → 0.01103** | **50.85 %** | **0.0652 %** |
| corrected frame only, 256 spp | 0.03675 → 0.00785 | 11.33 % | 0.0435 % |
| demonstrator, 256 spp | 0.03675 → 0.00777 | 11.17 % | — |

The real re-bake reads slightly *less* collapsed than the frame-only diagnostic
(0.01103 against 0.00785) and moves four and a half times as many pixels,
because its debris lies in front of the wound as well as its frame having left
it. **Both are far below R6's 0.03675 and the conclusion is unchanged.**
