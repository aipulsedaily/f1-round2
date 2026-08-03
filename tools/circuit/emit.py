"""Emit all final data blocks (world frame) + circuit_spec.json."""
import numpy as np, math, json, sys
from geo import D2R
from build import (E, REC, X, Y, Z, S, V, T, K, GRAD, LEN, LAP, CORNERS, to_world,
                   DS, N, FREE, RES, PVI, PS, PZ, PL, GRADES, THETA, RM, CD, CW,
                   a_trac, a_pow, a_drag, a_brk, G, corner_speed)
from part2 import (V_GLASS, T_LAUNCH, V_A, T_A, V_M, T_M, V_L, T_L, T_LAP_ONSCREEN,
                   V_WS, D_WS, T_WS)
from part3 import car_at_t, angsep
from final import cps, dop_station, catchup, DOP_S

R2D = 180.0/math.pi
def W(x, y):
    a, b = to_world(x, y); return float(a), float(b)
def Wpt(x, y, z):
    a, b = W(x, y); return (round(a, 2), round(b, 2), round(float(z), 3))

WX, WY = to_world(X, Y)
NAMES = ["T1 Vitrine", "T2 Threshold", "T3 Long Kink", "T4 LE PIN", "T5 La Rampe",
         "T6 Weave 1", "T7 Weave 2", "T8 Crest", "T9 Weave 4", "T10 Panorama 1",
         "(release)", "T11 Panorama 2", "T12 Plongee", "T13 Hook", "T14 Flick", "T15 Gate"]
TYPES = ["fast left", "linked left", "fast right kink", "HAIRPIN 176deg",
         "medium right, uphill", "esse left", "esse right", "esse left (summit)",
         "esse right", "double-apex A", "release arc", "double-apex B",
         "heavy-braking left", "slow left", "right kink", "fast final left"]
BANK = [2, 2, 3, 0, 1, 0, 0, -1, 0, 4, 4, 4, 0, 0, 0, 3]

# ---------------------------------------------------------------- braking zones
def bz(s_turnin):
    i = int(round(s_turnin/DS))
    j = i
    while j > 1 and V[j-1] >= V[j] - 1e-9:
        j -= 1
    return dict(s0=float(S[j]), s1=float(S[i]), v0=float(V[j]*3.6), v1=float(V[i]*3.6),
                dist=float(S[i]-S[j]), time=float(T[i]-T[j]),
                g=float((V[j]**2-V[i]**2)/(2*max(S[i]-S[j], 1e-9))/G))

# ---------------------------------------------------------------- clothoids
def clothoid(R):
    Lc = 0.55*R if R <= 100 else 0.40*R
    return Lc, math.sqrt(R*Lc)

# ---------------------------------------------------------------- control points
IDX = cps(0.12)
CP = [Wpt(X[i], Y[i], Z[i]) for i in IDX]

# ---------------------------------------------------------------- world constants
SF_W = W(0.0, 0.0)
HOLD = np.array([104.0, -288.0, 140.0])
KEY0 = np.array([-62.1, -52.6, 27.8])
PEEL = np.array([-260.5, 0.0, 2.8])
DOPCAM, DOPROWS, DOPDWELL = dop_station(DOP_S)
CH, PA, DT, VC, VCAR = catchup(DOP_S)

def blk(title): print("\n" + "="*70 + "\n" + title + "\n" + "="*70)

if __name__ == "__main__":
    blk("HEADLINE")
    print(f"length {LEN:.1f} m | lap {LAP:.2f} s | on-screen line-to-line {T_LAP_ONSCREEN:.2f} s")
    print(f"avg {LEN/LAP*3.6:.1f} km/h | vmax {V.max()*3.6:.1f} @ s={S[np.argmax(V)]:.0f}"
          f" | vmin {V.min()*3.6:.1f} | line speed flying {V[0]*3.6:.1f} out {V_L*3.6:.1f}")
    print(f"elev range {Z.max()-Z.min():.2f} m [{Z.min():+.2f} .. {Z.max():+.2f}]"
          f" grades {GRAD.max()*100:+.2f}% / {GRAD.min()*100:+.2f}%")
    sec = [0, 1200, 2450, int(LEN)]
    for a, b in zip(sec[:-1], sec[1:]):
        print(f"  sector s {a}-{b}: {T[int(b/DS) if b < LEN else N-1]-T[int(a/DS)]:.2f} s")
    print(f"free straights S2={FREE[0]:.3f} S9={FREE[1]:.3f} S11={FREE[2]:.3f}; residual {RES}")

    blk("ELEMENT LIST (world start points)")
    print(f"{'element':30s}{'R':>7s}{'ang':>8s}{'len':>9s}{'s0':>9s}"
          f"  {'world start (x,y)':>22s}{'hdg_w':>8s}")
    for e in REC:
        w = W(e['x0'], e['y0'])
        R = f"{e['R']:.0f}" if e['R'] else "inf"
        A = f"{e['ang']:+.1f}" if e['ang'] else "-"
        print(f"{e['name']:30s}{R:>7s}{A:>8s}{e['L']:9.2f}{e['s0']:9.2f}"
              f"  ({w[0]:9.2f},{w[1]:9.2f}){(e['h0']+40.0)%360:8.2f}")

    blk("CORNER TABLE")
    print(f"{'#':4s}{'name':18s}{'R':>6s}{'arc':>8s}{'m':>8s}{'brake@':>8s}{'apex':>7s}"
          f"{'exit':>7s}{'latg':>6s}{'bank':>6s}{'z':>7s}{'grd%':>7s}{'t':>7s}  world apex")
    for i, c in enumerate(CORNERS):
        w = W(c['x'], c['y'])
        print(f"{i+1:<4d}{NAMES[i]:18s}{c['R']:6.0f}{c['ang']:+8.1f}{c['arc']:8.1f}"
              f"{c['v_in']:8.1f}{c['v_apex']:7.1f}{c['v_out']:7.1f}{c['latg']:6.2f}"
              f"{BANK[i]:+6d}{c['z']:+7.2f}{c['grad']:+7.2f}{c['t']:7.2f}"
              f"  ({w[0]:8.1f},{w[1]:8.1f})")

    blk("BRAKING ZONES")
    for nm, sti in (("T1", 250.0), ("T4", 939.27), ("T10", 2142.81), ("T12", 2700.64)):
        b = bz(sti)
        print(f"  {nm}: {b['v0']:6.1f} -> {b['v1']:6.1f} km/h in {b['dist']:6.1f} m / "
              f"{b['time']:.2f} s, mean {b['g']:.2f} g  (s {b['s0']:.0f}->{b['s1']:.0f}, "
              f"grade {GRAD[int(b['s0']/DS)]*100:+.2f}%..{GRAD[int(b['s1']/DS)]*100:+.2f}%)")

    blk("ELEVATION PVIs (world z)")
    for i in range(len(PS)):
        gi = GRADES[i-1]*100 if i > 0 else 0.0
        go = GRADES[i]*100 if i < len(GRADES) else 0.0
        print(f"  s={PS[i]:8.1f}  z={PZ[i]:+7.3f}  Lvc={PL[i]:6.1f}  g_in={gi:+7.3f}%  g_out={go:+7.3f}%")
    print(f"  z(0)={Z[0]:+.4f} z(L)={Z[-1]:+.4f} -> closes to {abs(Z[-1]-Z[0]):.2e} m")

    blk("CLOTHOIDS")
    seen = set()
    for e in REC:
        if e['type'] != 'A' or e['R'] in seen: continue
        seen.add(e['R']); Lc, A = clothoid(e['R'])
        print(f"  R={e['R']:5.0f} m -> Lc={Lc:6.2f} m, A={A:7.2f}")

    blk("DOPPLER")
    print(f"  station s={DOP_S:.0f}  camera world {Wpt(DOPCAM[0], DOPCAM[1], DOPCAM[2])}"
          f"  dwell +-220 m = {DOPDWELL:.2f} s")
    for d, vk, dt, rng, vr, f in DOPROWS:
        print(f"    {d:+5d} m {vk:6.1f} km/h t{dt:+6.2f}s range {rng:6.1f} m vr {vr:+7.1f} f'/f {f:.3f}")
    fs = [r[5] for r in DOPROWS]
    print(f"    sweep {max(fs):.3f} -> {min(fs):.3f} = {12*math.log2(max(fs)/min(fs)):.2f} semitones")
    print(f"  catch-up: chord {CH:.0f} m vs car path {PA:.0f} m in {DT:.2f} s, ratio {CH/PA:.3f},"
          f" camera mean {VC:.1f} m/s ({VC*3.6:.0f} km/h)")

    blk("BEAT 6 (world)")
    for nm, p in (("peel-off t=-3.0", PEEL), ("key t=0", KEY0), ("HOLD t=+7..+10", HOLD)):
        print(f"  {nm:18s} design ({p[0]:8.1f},{p[1]:8.1f},{p[2]:6.1f})  world {Wpt(p[0], p[1], p[2])}")
    print(f"  showroom breach face world (15.00, 0.00, 0.00..6.20); wall centre (15, 0, 3.10)")
    print(f"  S/F line world {SF_W}")

    blk("CONTROL POINTS")
    print(f"  {len(CP)} points, sagitta tolerance 0.12 m")
    for i in range(0, len(CP), 1):
        pass
    blk("TRANSIT (world)")
    legs = [("launch inside", (0.0, 0.0, 0.0), (15.0, 0.0, 0.0), 11.98, 0.0, V_GLASS*3.6, T_LAUNCH),
            ("apron run", (15.0, 0.0, 0.0), (64.6, 0.0, 0.0), 49.6, 0.0, V_A*3.6, T_A),
            ("merge arc R150/40L", (64.6, 0.0, 0.0), (161.02, 35.09, 0.0), 104.7, 0.0, V_M*3.6, T_M),
            ("pit straight to line", (161.02, 35.09, 0.0), SF_W+(0.0,), 215.6, 0.0, V_L*3.6, T_L)]
    for nm, a, b, L, g, ve, tt in legs:
        print(f"  {nm:22s} ({a[0]:8.2f},{a[1]:8.2f},{a[2]:5.2f}) -> ({b[0]:8.2f},{b[1]:8.2f},{b[2]:5.2f})"
              f"  L={L:7.2f} m  grade {g:+.2f}%  exit {ve:6.1f} km/h  t={tt:.2f} s")

    # ------------------------------------------------------------ JSON
    doc = dict(
        schema="f1-round2/circuit_spec/1.0",
        name="Circuit Vitrine",
        datum=dict(
            description=("world origin = round-1 showroom floor centre; +X east, +Y north, "
                         "+Z up; Z=0 is the showroom finished floor AND the pit-straight surface"),
            circuit_design_frame=dict(rotation_deg_about_z=40.0,
                                      pivot_design=[-350.0, 72.0], pivot_world=[15.0, 0.0],
                                      note="world = Rz(40deg)*(design - pivot_design) + pivot_world"),
            start_finish_world=[round(SF_W[0], 3), round(SF_W[1], 3), 0.0],
            racing_direction_world_deg=40.0, lap_direction="counter-clockwise"),
        headline=dict(length_m=round(float(LEN), 2), corners=15,
                      lap_time_s=round(float(LAP), 3),
                      onscreen_lap_time_s=round(float(T_LAP_ONSCREEN), 3),
                      avg_speed_kph=round(float(LEN/LAP*3.6), 1),
                      vmax_kph=round(float(V.max()*3.6), 1),
                      vmin_kph=round(float(V.min()*3.6), 1),
                      line_speed_flying_kph=round(float(V[0]*3.6), 1),
                      line_speed_outlap_kph=round(float(V_L*3.6), 1),
                      elevation_range_m=round(float(Z.max()-Z.min()), 3),
                      max_grade_pct=round(float(GRAD.max()*100), 3),
                      min_grade_pct=round(float(GRAD.min()*100), 3),
                      closure_residual_m=[float(RES[0]), float(RES[1])],
                      elevation_closure_m=float(Z[-1]-Z[0])),
        elements=[dict(name=e['name'], type=e['type'], radius_m=e['R'], turn_deg=e['ang'],
                       length_m=round(e['L'], 4), s_start=round(e['s0'], 4),
                       start_world=list(Wpt(e['x0'], e['y0'], 0.0))[:2],
                       heading_world_deg=round((e['h0']+40.0) % 360, 4)) for e in REC],
        corner_count=15,
        corners=[dict(index=(i+1 if i < 10 else (None if i == 10 else i)),
                      is_numbered_corner=(i != 10), name=NAMES[i], type=TYPES[i], radius_m=c['R'],
                      turn_deg=c['ang'], arc_m=round(c['arc'], 2),
                      direction="left" if c['ang'] > 0 else "right",
                      s_apex=round(c['sapex'], 2),
                      apex_world=list(Wpt(c['x'], c['y'], c['z'])),
                      entry_kph=round(c['v_in'], 1), apex_kph=round(c['v_apex'], 1),
                      exit_kph=round(c['v_out'], 1), lateral_g=round(c['latg'], 2),
                      banking_deg=BANK[i], grade_pct=round(c['grad'], 2),
                      lap_t_s=round(c['t'], 2)) for i, c in enumerate(CORNERS)],
        centerline=dict(units="metres, world frame", spline="POLY, cyclic",
                        sagitta_tolerance_m=0.12, count=len(CP),
                        points=[list(p) for p in CP]),
        elevation=dict(method="tangent grades joined by parabolic vertical curves",
                       station_z_pvi=[dict(s=float(PS[i]), z=float(PZ[i]),
                                           vertical_curve_len_m=float(PL[i]))
                                      for i in range(len(PS))]),
        track_section=dict(
            pit_straight_m=16.0, standard_m=14.0, hairpin_m=15.0, esses_m=13.0,
            access_road_m=12.0, transition_len_m=60.0,
            kerb=dict(width_m=1.50, outer_lip_mm=50, inner_lip_mm=25,
                      serration_pitch_mm=250, serration_amplitude_mm=25,
                      alternation_m=1.0),
            negative_kerb=dict(locations=["T8 apex", "T12 exit"], depth_mm=-60, width_m=0.80)),
        vehicle_model=dict(
            mass_kg=830.0,
            a_lat="min(15.0 + 0.0050*v^2, 48.0) m/s^2",
            a_traction="min(11.0 + 0.0022*v^2, 20.0) m/s^2",
            a_power="800/v m/s^2 (664 kW at the wheels)",
            a_drag="0.00092*v^2 m/s^2",
            a_brake="min(1.25 + 2.2e-4*v^2, 5.0)*9.81 m/s^2 + drag  [grafted from layout A]",
            grade_term="-g*dz/ds",
            mu_derate=dict(circuit=1.00, access_road=0.90, showroom_floor=0.85)),
        showroom=dict(
            transform="IDENTITY - round-1 geometry is NOT moved",
            floor_centre_world=[0.0, 0.0, 0.0], interior_m=[30.0, 22.0, 6.50],
            clear_head_m=6.20,
            breach_wall="GW_Right, plane X=+15.00, 10 glass panels of 2.125 m, 11 mullions "
                        "at 2.20 m centres (one on the launch axis Y=0), 3 transoms, head, "
                        "sill, base reveal",
            breach_face_centre_world=[15.0, 0.0, 3.10],
            breach_exit_vector=[1.0, 0.0, 0.0],
            breach_aperture_m=dict(width=9.6, height=5.6,
                                   centre_world=[15.0, 0.0, 2.85],
                                   y_range=[-4.8, 4.8], z_range=[0.11, 5.71]),
            dais=dict(radius_m=3.70, deck_top_z=0.340,
                      delivery_ramp="0.340 m rise over 2.60 m (13.1%), full 3.0 m width, "
                                    "from the dais lip X=+3.70 to X=+6.30"),
            launch_run_m=11.98, impact_speed_kph=round(float(V_GLASS*3.6), 1),
            exterior_ground_fix="raise round-1 ExteriorGround from z -0.14..-0.08 to exactly "
                                "0.000 over X 10..90, Y -40..+40, then blend over 20 m"),
        paddock=dict(
            frame="design frame, then transformed to world by the datum block",
            pit_wall_design_y=11.5, pit_lane_design_y=[11.5, 23.5],
            garages_design=dict(x=[-245.0, 75.0], y=[23.5, 40.5], roof_z=12.0, bays=14),
            paddock_design=dict(x=[-480.0, 100.0], y=[40.5, 115.0]),
            apron_design=dict(x=[-480.0, -245.0], y=[0.0, 45.0]),
            showroom_design_footprint=dict(x=[-380.5, -342.9], y=[63.6, 100.1]),
            grandstands_design=dict(y=[-34.0, -62.0], x=[-420.0, 180.0], height_m=14.0,
                                    protected_gap="none required - Beat-6 rays clear by "
                                                  ">=36 m; see sightline block"),
            gantry_design=dict(x=0.0, legs_y=[-11.0, 11.0], soffit_z=9.0, depth_m=2.2),
            footbridge_design=dict(x=-450.0, soffit_z=7.5, depth_m=4.0, span_y=[-24.0, 28.0]),
            plunge_bridge_design=dict(s=2410.0, soffit_z=6.8, span_m=30.0, deck_width_m=6.0)),
        transit=dict(
            legs=[dict(name="launch inside showroom", from_world=[0.0, 0.0, 0.0],
                       to_world=[15.0, 0.0, 0.0], length_m=11.98, grade_pct=0.0,
                       exit_kph=round(float(V_GLASS*3.6), 1), time_s=round(float(T_LAUNCH), 2)),
                  dict(name="apron run (flat, unrubbered)", from_world=[15.0, 0.0, 0.0],
                       to_world=[64.6, 0.0, 0.0], length_m=49.6, grade_pct=0.0,
                       exit_kph=round(float(V_A*3.6), 1), time_s=round(float(T_A), 2)),
                  dict(name="merge arc R150 / 40 deg left", from_world=[64.6, 0.0, 0.0],
                       to_world=[161.02, 35.09, 0.0], length_m=104.7, grade_pct=0.0,
                       exit_kph=round(float(V_M*3.6), 1), time_s=round(float(T_M), 2)),
                  dict(name="pit straight to the line", from_world=[161.02, 35.09, 0.0],
                       to_world=[round(SF_W[0], 2), round(SF_W[1], 2), 0.0], length_m=215.6,
                       grade_pct=0.0, exit_kph=round(float(V_L*3.6), 1),
                       time_s=round(float(T_L), 2))],
            total_length_dais_to_line_m=381.88,
            total_time_dais_to_line_s=round(float(T_LAUNCH+T_A+T_M+T_L), 2),
            total_length_glass_to_line_m=369.90,
            total_time_glass_to_line_s=round(float(T_A+T_M+T_L), 2),
            beat4_world_time_s=5.6,
            beat4_note="Beat 4 is 5.6 s of world time: the 7.13 s glass-to-line figure less "
                       "the ~1.6 s of world time consumed inside Beat 3's speed ramp over the "
                       "first 30 m past the glass"),
        doppler=dict(station_s=DOP_S, camera_world=list(Wpt(*DOPCAM)),
                     offset_from_centreline_m=26.0, height_above_grade_m=2.40,
                     peak_kph=round(float(V[int(DOP_S/DS)]*3.6), 1),
                     slant_range_m=26.1, dwell_s=round(float(DOPDWELL), 2),
                     semitone_sweep=round(float(12*math.log2(max(r[5] for r in DOPROWS) /
                                                            min(r[5] for r in DOPROWS))), 2),
                     fallback_station_s=2600.0),
        beat6=dict(peel_off_t=-3.0, peel_off_world=list(Wpt(*PEEL)),
                   key0_world=list(Wpt(*KEY0)), key0_lens_mm=24.0,
                   hold_world=list(Wpt(*HOLD)), hold_lens_mm=18.75,
                   hold_start_t=8.0, hold_end_t=11.0,
                   trajectory="minimum-energy cubic from (peel, v=83.1 m/s along the pit "
                              "straight) to (hold, v=0) in 11.0 s; peak |a| 19.9 m/s^2 (2.03 g) "
                              "at the peel-off, easing monotonically",
                   keys=[dict(t=-3.0, world=list(Wpt(-260.5, 0.0, 2.8)), lens_mm=32.0, speed=83.1),
                         dict(t=-1.0, world=list(Wpt(-117.5, -25.1, 14.8)), lens_mm=28.0, speed=65.8),
                         dict(t=0.0, world=list(Wpt(-62.1, -52.6, 27.8)), lens_mm=24.0, speed=61.1),
                         dict(t=2.0, world=list(Wpt(20.6, -124.4, 62.1)), lens_mm=21.0, speed=54.2),
                         dict(t=4.0, world=list(Wpt(71.4, -201.4, 98.8)), lens_mm=19.5, speed=44.3),
                         dict(t=6.0, world=list(Wpt(97.0, -262.9, 128.0)), lens_mm=18.75, speed=27.0),
                         dict(t=8.0, world=list(Wpt(104.0, -288.0, 140.0)), lens_mm=18.75, speed=0.0),
                         dict(t=11.0, world=list(Wpt(104.0, -288.0, 140.0)), lens_mm=18.75, speed=0.0)],
                   facade_px=[109, 119], aperture_px=[48, 52],
                   wound_enters_frame_t=6.0,
                   sightline_clearance_m=29.4),
        sun=dict(direction_to_sun=[0.518, -0.828, 0.216], bearing_world_deg=-58.0,
                 elevation_deg=12.5, shadow_length_ratio=4.51,
                 note="round 1 has NO sun lamp (23 interior lamps only), so this is a free "
                      "choice; -58 deg puts the sun 34 deg off the GW_Front normal (key light "
                      "for beat 1), 58 deg off the GW_Right breach-wall normal (raking, so the "
                      "wound reads as a deep notch in beat 6), and 98 deg to the right of the "
                      "racing direction (cross-light, long shadows across the pit straight)"),
        terrain=dict(frame="circuit", landforms=[
            dict(name="the plateau", x=[-620, 300], y=[-120, 140], z="flat 0.000"),
            dict(name="north-east escarpment", x=[300, 520], y=[680, 1000],
                 z="falls at -8% from the edge of T4 gravel to -9.5 m at 120 m out",
                 purpose="silhouette background for the kerb-height hairpin camera"),
            dict(name="the ridge", x=[-380, 260], y=[400, 760],
                 z="rises with La Rampe, carries the esses; infield banked to +11 m behind T7/T8"),
            dict(name="the west hillside", x=[-960, -560], y=[80, 400],
                 z="falls to -12 m at the world edge west of the sweeper/doppler straight"),
            dict(name="the return hollow", x=[-620, -240], y=[-260, -80], z="-3.7 m bowl at T12/T13")]),
        runoff=[dict(corner="T1", asphalt_m=45, gravel_m=12, barrier="TecPro"),
                dict(corner="T3", asphalt_m=40, gravel_m=15, barrier="Armco"),
                dict(corner="T4", asphalt_m=0, gravel_m=30, barrier="TecPro x3"),
                dict(corner="T5", asphalt_m=0, grass_m=20, barrier="Armco"),
                dict(corner="T8", asphalt_m=20, gravel_m=25, barrier="Armco"),
                dict(corner="T10_T11", asphalt_m=55, gravel_m=15, barrier="Armco"),
                dict(corner="T12", asphalt_m=0, gravel_m=30, barrier="TecPro x3"),
                dict(corner="T15", asphalt_m=30, barrier="Armco"),
                dict(corner="default", grass_m=[18, 25], barrier="Armco + 3.6 m debris fence")],
        empty_zones=[dict(name="infield bowl", frame="circuit", x=[-340, 160], y=[180, 420],
                          max_height_m=4.0, purpose="helicopter arc over the esses"),
                     dict(name="west outfield", frame="circuit", x=[-1010, -860], y=[150, 560],
                          max_height_m=3.0, purpose="doppler sight line both ways"),
                     dict(name="south apron", frame="circuit", x=[-120, 260], y=[-340, -62],
                          max_height_m=4.0, purpose="Beat-6 crane-out volume and held-frame ground")],
        camber_overrides=[dict(corner="T4", entry_pct=-1.5, apex_pct=0.0,
                               note="adverse camber falling away from the turn, grafted from C")],
        verification=dict(
            plan_closure_m=[float(RES[0]), float(RES[1])],
            heading_closure_deg=0.0,
            elevation_closure_m=float(Z[-1]-Z[0]),
            length_m=round(float(LEN), 3),
            lap_s=round(float(LAP), 3),
            min_nonadjacent_separation_m=60.6,
            control_point_max_chord_error_m=0.123,
            net_turn_deg=360.0))
    with open("circuit_spec.json", "w") as fh:
        json.dump(doc, fh, indent=1)
    print(f"\nwrote circuit_spec.json  ({len(json.dumps(doc))} bytes, "
          f"{len(CP)} control points)")
