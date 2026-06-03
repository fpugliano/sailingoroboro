#!/usr/bin/env /usr/bin/python3
"""
Generate js/map.js from the three Oroboro GPX files.
Uses streaming line-by-line parsing (no full-XML load) and iterative RDP.

Run:  /usr/bin/python3 gpx_to_mapjs.py
"""

import re, json, math, zipfile, os, sys
from pathlib import Path
from collections import defaultdict

REPO    = Path("/Users/francesco/Documents/SailingOroboro Website")
TMPDIR  = Path("/tmp/gpx_work")
TMPDIR.mkdir(exist_ok=True)

# ── Extract zips if needed ────────────────────────────────────────────────────

def ensure_extracted(zip_name, gpx_name):
    src  = REPO / zip_name
    dest = TMPDIR / gpx_name
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    print(f"  Extracting {zip_name} …")
    with zipfile.ZipFile(src) as z:
        z.extract(gpx_name, TMPDIR)
    return dest

print("── Extracting GPX files ───────────────────────────────────────────────")
f_all  = ensure_extracted("TracksOROBOROall.gpx.zip",   "TracksOROBOROall.gpx")
f_2021 = ensure_extracted("Archive_08_20_2021.gpx.zip", "Archive_08_20_2021.gpx")
f_2025 = ensure_extracted("Archive_05_01_2025.gpx.zip", "Archive_05_01_2025.gpx")
# New raw GPX files (not zipped)
f_1234 = REPO / "TRACK1234_2022.gpx"   # Track 4: Elba → N. Sardinia
f_0606 = REPO / "Tracks060626.gpx"     # Tracks 13-18: Greek Aegean continuation
f_t2s  = REPO / "Turkey to Syros.gpx"  # Bodrum → Syros passage

# ── Streaming GPX parser ──────────────────────────────────────────────────────

_trkpt_re  = re.compile(r'<trkpt\s+lon="([^"]+)"\s+lat="([^"]+)"')
_trkptal_re = re.compile(r'<trkpt\s+lat="([^"]+)"\s+lon="([^"]+)"')
_name_re   = re.compile(r'<name>(.*?)</name>')

def parse_gpx_tracks(path):
    """
    Stream-parse a GPX file.  Returns dict  {track_name: [(lat,lon), ...]}
    in file order.  Only reads trkpt lines — no full tree in memory.
    """
    tracks = {}           # ordered dict (Python 3.7+)
    cur_name  = None
    cur_pts   = []
    in_trk    = False
    in_trkpt  = False

    with open(path, 'r', errors='replace') as f:
        for line in f:
            l = line.strip()
            # Track open/close
            if '<trk>' in l:
                in_trk   = True
                cur_name = None
                cur_pts  = []
            elif '</trk>' in l and in_trk:
                if cur_name and cur_pts:
                    name = cur_name.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
                    if name in tracks:
                        tracks[name + '_dup'] = cur_pts
                    else:
                        tracks[name] = cur_pts
                in_trk = False
                cur_pts = []
            # Track name (first <name> inside <trk>, not inside <trkpt>)
            elif in_trk and not in_trkpt and '<name>' in l and cur_name is None:
                m = _name_re.search(l)
                if m:
                    cur_name = m.group(1)
            # trkpt open
            elif '<trkpt ' in l and in_trk:
                in_trkpt = True
                m = _trkpt_re.search(l)
                if m:
                    cur_pts.append((float(m.group(2)), float(m.group(1))))  # lat, lon
                else:
                    m2 = _trkptal_re.search(l)
                    if m2:
                        cur_pts.append((float(m2.group(1)), float(m2.group(2))))
            elif '</trkpt>' in l:
                in_trkpt = False
    return tracks

# ── Iterative Ramer-Douglas-Peucker ──────────────────────────────────────────

def rdp(points, epsilon):
    """Simplify polyline.  Iterative to avoid Python recursion limit."""
    if len(points) <= 2:
        return list(points)
    n = len(points)
    keep = bytearray(n)   # 0/1
    keep[0] = keep[n-1] = 1
    stack = [(0, n-1)]
    while stack:
        start, end = stack.pop()
        x1, y1 = points[start]
        x2, y2 = points[end]
        dx, dy = x2 - x1, y2 - y1
        mag = math.hypot(dx, dy)
        max_d, max_i = 0.0, start
        for i in range(start+1, end):
            x, y = points[i]
            if mag > 0:
                d = abs(dy*(x-x1) - dx*(y-y1)) / mag
            else:
                d = math.hypot(x-x1, y-y1)
            if d > max_d:
                max_d, max_i = d, i
        if max_d > epsilon:
            keep[max_i] = 1
            stack.append((start, max_i))
            stack.append((max_i, end))
    return [points[i] for i in range(n) if keep[i]]

# ── Nearest-point finder ──────────────────────────────────────────────────────

def nearest(lat, lon, pts):
    best_d, best_p = float('inf'), pts[0]
    for p in pts:
        d = (p[0]-lat)**2 + (p[1]-lon)**2
        if d < best_d:
            best_d, best_p = d, p
    return best_p

# ── Parse all three GPX files ─────────────────────────────────────────────────

print("\n── Parsing GPX tracks (streaming) ────────────────────────────────────")

print("  TracksOROBOROall.gpx …")
trk1 = parse_gpx_tracks(f_all)
print(f"    {len(trk1)} tracks  ({sum(len(v) for v in trk1.values()):,} pts)")

print("  Archive_08_20_2021.gpx …")
trk2 = parse_gpx_tracks(f_2021)
print(f"    {len(trk2)} tracks  ({sum(len(v) for v in trk2.values()):,} pts)")

print("  Archive_05_01_2025.gpx …")
trk3 = parse_gpx_tracks(f_2025)
print(f"    {len(trk3)} tracks  ({sum(len(v) for v in trk3.values()):,} pts)")

print("  TRACK1234_2022.gpx …")
trk4 = parse_gpx_tracks(f_1234)
print(f"    {len(trk4)} tracks  ({sum(len(v) for v in trk4.values()):,} pts)")

print("  Tracks060626.gpx …")
trk5 = parse_gpx_tracks(f_0606)
print(f"    {len(trk5)} tracks  ({sum(len(v) for v in trk5.values()):,} pts)")

print("  Turkey to Syros.gpx …")
trk6 = parse_gpx_tracks(f_t2s)
print(f"    {len(trk6)} tracks  ({sum(len(v) for v in trk6.values()):,} pts)")

# ── Assemble ordered route ────────────────────────────────────────────────────
# Two solid GPS segments separated by an estimated gap (dashed on map):
#
#  SEGMENT 1 — Cape Town → N. Sardinia (continuous real GPS)
#   Phase 1 (2018-2020): Cape Town → Caribbean  — TracksOROBOROall.gpx
#   Phase 2 (2021-a)   : Grenada → Azores       — Archive_08_20_2021.gpx Track 1+2
#   Phase 2b(2021-b)   : Azores → Elba          — Archive_08_20_2021.gpx Track 3
#   Phase 3 (2022)     : Elba → N. Sardinia     — TRACK1234_2022.gpx Track 4
#
#  [GAP — estimated dashed: La Maddalena → E. Sardinia → Egadi → SW Sicily → Licata → Malta → Pylos → Peloponnese → Milos → Parikia, Paros]
#
#  SEGMENT 2 — Turkey → Greece / Aegean (continuous real GPS)
#   Phase 4 (2022-2023): Turkey → Greek islands — Archive_05_01_2025.gpx
#   Phase 5 (2023-2025): Greek Aegean loops     — Tracks060626.gpx

SEG1_PHASES = [
    ('CPT>STH',      trk1),   # Cape Town → St. Helena
    ('STH>BRZ',      trk1),   # St. Helena → Brazil
    ('ILHAG>VITORIA',trk1),   # Ilha Grande → Vitória
    ('VIT>SALVADOR', trk1),   # Vitória → Salvador
    ('SAL>FORTALEZA',trk1),   # Salvador → Fortaleza
    ('FORTA>TOBAGO', trk1),   # Fortaleza → Tobago
    ('Caribe2019',   trk1),   # Caribbean 2019
    ('Caribe2020',   trk1),   # Caribbean 2020
    ('Track 1',      trk2),   # Grenada → Bahamas
    ('Track 2',      trk2),   # Bahamas → Azores (2nd Atlantic crossing)
    ('Track 3',      trk2),   # Azores → Elba
    ('Track 4',      trk4),   # Elba → N. Sardinia (Porto Pozzo)
]

SEG2_PHASES = [
    ('Turkey to Syros Track', trk6),  # Bodrum → Syros (passage plan)
    ('Turkey2Greece',trk3),   # Turkey/Bodrum → Dodecanese
    ('Track 8',      trk3),   # Dodecanese / Aegean
    ('Track 9',      trk3),   # Aegean toward Athens
    ('Track 10',     trk3),   # Cyclades
    ('Track 11',     trk3),   # Cyclades / Dodecanese
    ('Track 13',     trk5),   # Samos/Ikaria → Cyclades (new)
    ('Track 14',     trk5),   # Cyclades (new)
    ('Track 15',     trk5),   # Cyclades (new)
    ('Track 16',     trk5),   # Cyclades → Athens (new)
    ('Track 17',     trk5),   # Athens/Piraeus area (new)
    ('Track 18',     trk5),   # Athens → N. Aegean/Sporades (new)
]

# Estimated waypoints for the unrecorded gap, mid-2022:
#   La Maddalena → E. Sardinia → Egadi Islands → SW Sicily → Licata
#   → Malta → Pylos → Peloponnese coast → Milos → Parikia, Paros
GAP_WAYPOINTS = [
    # ── La Maddalena Archipelago (Track 4 endpoint) ───────────
    [41.2995,  9.3380],  # Porto Pozzo / La Maddalena
    [41.2267,  9.5200],  # East of La Maddalena, clearing the islands
    # ── East coast of Sardinia — 5 nm offshore ────────────────
    # Coast runs at ~9.60-9.75°E; keeping ≥0.15° east for 5 nm clearance
    [41.0500,  9.7000],  # Golfo Aranci offshore
    [40.8967,  9.9500],  # East of Tavolara island (island E coast ~9.75°E)
    [40.5583,  9.8800],  # Siniscola offshore
    [40.2833,  9.7700],  # Gulf of Orosei / Cala Gonone offshore
    [39.9333,  9.8600],  # Arbatax offshore
    [39.5150,  9.7800],  # Capo Monte Santu offshore
    [39.1000,  9.7300],  # Capo Carbonara offshore (cape tip ~9.52°E)
    # ── Open water crossing to Egadi Islands ──────────────────
    [38.6000, 10.0500],  # Clear of SE Sardinia
    [38.2000, 10.9000],  # Sicilian Channel, mid-crossing
    [38.1500, 11.8000],  # Approaching NW Sicily, staying clear
    [37.9500, 12.1700],  # Egadi approach — 5 nm W of Favignana
    # ── Egadi Islands and SW coast of Sicily — 5 nm offshore ──
    # SW coast faces WSW; keeping ≥0.12° west/south for 5 nm clearance
    [37.7500, 12.2900],  # Marsala area — 5 nm W of coast
    [37.5900, 12.4700],  # Mazara del Vallo — 5 nm SW
    [37.4800, 12.6700],  # Menfi area — 5 nm SW
    [37.4000, 13.0300],  # Sciacca — 5 nm S
    [37.2000, 13.4200],  # Porto Empedocle — 5 nm S
    [37.0150, 13.9400],  # Licata — 5 nm S of coast
    # ── Crossing to Malta ─────────────────────────────────────
    [36.6000, 14.1500],  # Open water SE of Sicily
    [36.1800, 14.3500],  # Approaching Malta from N
    [35.9000, 14.5133],  # Valletta, Malta
    # ── Ionian Sea crossing to Pylos ──────────────────────────
    [35.8500, 15.6000],  # Open Ionian Sea
    [36.0000, 17.2000],  # Mid Ionian
    [36.3000, 19.0000],  # E Ionian approach
    [36.6000, 20.5000],  # W Greece coast approach
    [36.8167, 21.3500],  # Methoni
    [36.9133, 21.6817],  # Pylos / Navarino Bay
    # ── Along the Peloponnese — 5 nm offshore ─────────────────
    # S coast faces south; keeping ≥0.083° south for 5 nm clearance
    [36.7200, 21.9500],  # Koroni area — 5 nm S
    [36.5100, 22.0700],  # S. Messenia coast — 5 nm S
    [36.2800, 22.4883],  # 5 nm south of Cape Matapan tip
    [36.3500, 22.8500],  # Mid Laconian Gulf — clear of both coasts
    [36.3700, 23.1500],  # Cape Malea — 5 nm S of tip
    # ── NE toward the Cyclades ────────────────────────────────
    [36.5500, 23.5500],  # Open Aegean, heading NE
    # ── Milos ─────────────────────────────────────────────────
    [36.7233, 24.4433],  # Adamas, Milos
    # ── Paros ─────────────────────────────────────────────────
    [36.9500, 24.8000],  # Between Milos and Paros
    [37.0850, 25.1483],  # Parikia, Paros
]

# ── Short reconstructed routes (Aegean / Turkey) ─────────────────────────────

LEROS_DIDIM = [
    # Lakki, Leros → Didim marina (Turkey)
    [37.1183, 26.8533],  # Lakki harbor, Leros
    [37.1417, 26.8200],  # Exit Lakki bay, head N
    [37.1883, 26.8667],  # N tip of Leros
    [37.2167, 26.9333],  # Between Leros and Kalymnos
    [37.2650, 27.0167],  # Open water NE
    [37.3100, 27.1167],  # Approaching Turkish coast
    [37.3583, 27.2000],  # Turkish coastal water
    [37.3750, 27.2650],  # Didim marina
]

DIDIM_PATMOS = [
    # Didim marina (Turkey) → Skala, Patmos
    [37.3750, 27.2650],  # Didim marina
    [37.3667, 27.0333],  # Head W along Turkish coast
    [37.3833, 26.8000],  # Through Turkish/Greek channel
    [37.3667, 26.6667],  # Past Arki island
    [37.3383, 26.5833],  # Approach Patmos from E
    [37.3183, 26.5483],  # Skala, Patmos
]

MYKONOS_DIDIM = [
    # Mykonos (old port) → Didim marina
    [37.4467, 25.3250],  # Mykonos old port
    [37.5167, 25.6333],  # ENE past Naxos gap
    [37.6167, 26.0167],  # Ikaria north coast
    [37.5700, 26.4833],  # Fourni islands
    [37.5333, 26.8000],  # Toward Samos strait
    [37.4500, 27.0167],  # SE toward Didim
    [37.3750, 27.2650],  # Didim marina
]

DIDIM_MYKONOS = [
    # Didim marina → Mykonos (old port)  — slightly different route
    [37.3750, 27.2650],  # Didim marina
    [37.4833, 26.9833],  # NW past Samos area
    [37.5667, 26.5167],  # W past Fourni
    [37.6333, 26.1167],  # W past Ikaria
    [37.5500, 25.7167],  # WSW toward Mykonos
    [37.4467, 25.3250],  # Mykonos old port
]

print("\n── Assembling route segments ─────────────────────────────────────────")
seg1_pts = []
print("  Segment 1 (Cape Town → N. Sardinia):")
for name, src in SEG1_PHASES:
    if name in src:
        seg = src[name]
        seg1_pts.extend(seg)
        print(f"    +{len(seg):6,} pts  [{name}]")
    else:
        print(f"    WARNING: track {name!r} not found", file=sys.stderr)

seg2_pts = []
print("  Segment 2 (Turkey → Aegean/Sporades):")
for name, src in SEG2_PHASES:
    if name in src:
        seg = src[name]
        seg2_pts.extend(seg)
        print(f"    +{len(seg):6,} pts  [{name}]")
    else:
        print(f"    WARNING: track {name!r} not found", file=sys.stderr)

all_pts   = seg1_pts + seg2_pts
raw_total = len(all_pts)
print(f"\n  Seg1 raw : {len(seg1_pts):,} pts")
print(f"  Seg2 raw : {len(seg2_pts):,} pts")
print(f"  Total    : {raw_total:,} pts")

# ── Simplify each segment separately with RDP ─────────────────────────────────
EPS = 0.012   # ~1.2 km tolerance at equator
simp1 = rdp(seg1_pts, EPS)
simp2 = rdp(seg2_pts, EPS)
print(f"  After RDP (ε={EPS}°): seg1={len(simp1):,}  seg2={len(simp2):,}  gap={len(GAP_WAYPOINTS)} estimated pts")

# ── Blog post → coordinate table ──────────────────────────────────────────────
# (slug, display_name, approx_lat, approx_lon, date_str, region)
# All 75 published posts are listed here.
POST_LOCS = [
    # ── South Africa: pre-departure & Cape Town ────────────────────────────
    ("about-the-name-of-the-boat",          "Cape Town",              -33.91,  18.43, "Sep 2018", "south-africa"),
    ("choosing-the-right-boat",             "Cape Town",              -33.91,  18.43, "Sep 2018", "south-africa"),
    ("quitting-our-jobs",                   "Cape Town",              -33.91,  18.43, "Sep 2018", "south-africa"),
    ("sailing-vessel-oroboro",              "Cape Town",              -33.91,  18.43, "Oct 2018", "south-africa"),
    ("three-weeks-worth-of-work",           "Cape Town",              -33.91,  18.43, "Oct 2018", "south-africa"),
    ("enough-with-work",                    "Cape Town",              -33.91,  18.43, "Nov 2018", "south-africa"),
    ("7%c2%bd-weeks",                       "Cape Town",              -33.91,  18.43, "Nov 2018", "south-africa"),
    ("stress-test",                         "Cape Town",              -33.91,  18.43, "Nov 2018", "south-africa"),
    ("how-the-boat-was-built",              "Cape Town",              -33.91,  18.43, "Nov 2018", "south-africa"),
    ("discovering-south-africa",            "Cape Town",              -33.91,  18.43, "Dec 2018", "south-africa"),
    ("cape-town-arrival",                   "Cape Town",              -33.91,  18.43, "Sep 2018", "south-africa"),
    ("shake-down-sail-to-langebaan",        "Langebaan",              -33.17,  18.03, "Dec 2018", "south-africa"),
    ("maiden-voyage",                       "Cape Town → Namibia",    -33.88,  18.44, "Dec 2018", "south-africa"),
    # ── Namibia ───────────────────────────────────────────────────────────
    ("passage-to-namibia",                  "Lüderitz, Namibia",      -26.65,  15.16, "Dec 2018", "namibia"),
    ("kolmanskop-namibia",                  "Lüderitz, Namibia",      -26.65,  15.16, "Dec 2018", "namibia"),
    ("hottentot-bay-namibia",               "Hottentot Bay",          -24.36,  14.98, "Dec 2018", "namibia"),
    ("crossing-the-tropic-of-capricorn",    "Tropic of Capricorn",    -23.44,  14.68, "Jan 2019", "namibia"),
    # ── South Atlantic ────────────────────────────────────────────────────
    ("crossing-the-south-atlantic-ocean",   "South Atlantic",         -14.00, -20.00, "Feb 2019", "atlantic"),
    ("st-helena",                           "St Helena",              -15.96,  -5.71, "Mar 2019", "atlantic"),
    ("trindade",                            "Trindade Island",        -20.51, -29.33, "Mar 2019", "atlantic"),
    # ── Brazil: arrival & south coast ────────────────────────────────────
    ("welcome-to-brazil",                   "Ilha Grande",            -23.18, -44.21, "Mar 2019", "brazil"),
    ("how-to-repair-a-spectra-newport-watermaker", "Ilha Grande",     -23.18, -44.21, "Mar 2019", "brazil"),
    ("ubatuba",                             "Ubatuba",                -23.44, -45.07, "Apr 2019", "brazil"),
    ("ilha-grande",                         "Ilha Grande",            -23.18, -44.21, "Apr 2019", "brazil"),
    ("carnival-in-rio-de-janeiro",          "Rio de Janeiro",         -22.91, -43.17, "Apr 2019", "brazil"),
    ("ouro-preto-or-black-gold",            "Ouro Preto",             -20.32, -40.34, "Apr 2019", "brazil"),  # land trip from Vitória
    ("sao-paulo",                           "São Paulo",              -23.95, -46.32, "May 2019", "brazil"),  # Santos port
    ("brasilia",                            "Brasília",               -20.32, -40.34, "May 2019", "brazil"),  # land trip from Vitória
    ("pirenopolis",                         "Pirenópolis",            -20.32, -40.34, "May 2019", "brazil"),  # land trip from Vitória
    ("cabo-frio",                           "Cabo Frio",              -22.89, -42.02, "May 2019", "brazil"),
    ("armacao-dos-buzios-simply-known-as-buzios", "Búzios",           -22.75, -41.88, "May 2019", "brazil"),
    ("guarapari",                           "Guarapari",              -20.67, -40.50, "May 2019", "brazil"),
    ("vitoria",                             "Vitória",                -20.32, -40.34, "May 2019", "brazil"),
    ("abrolhos",                            "Abrolhos",               -17.97, -38.70, "May 2019", "brazil"),
    ("cumuruxatiba",                        "Cumuruxatiba",           -17.09, -39.18, "May 2019", "brazil"),
    ("corao-vernelho",                      "Coroa Vermelha",         -16.44, -39.01, "May 2019", "brazil"),
    ("porto-seguro",                        "Porto Seguro",           -16.45, -39.06, "May 2019", "brazil"),
    ("santo-andre-and-santa-cruz-cabralia", "Santa Cruz Cabrália",    -16.28, -39.02, "May 2019", "brazil"),
    # ── Brazil: Bahia coast ───────────────────────────────────────────────
    ("ilheus",                              "Ilhéus",                 -14.79, -39.05, "2019",     "brazil"),
    ("itacare",                             "Itacaré",                -14.28, -38.99, "2019",     "brazil"),
    ("the-dark-science-of-weather-forecasts","Bahia coast",           -14.00, -38.90, "2019",     "brazil"),
    ("camamu-bay",                          "Camamù Bay",             -13.95, -39.10, "2019",     "brazil"),
    ("salvador-de-bahia",                   "Salvador de Bahia",      -12.97, -38.50, "Aug 2019", "brazil"),
    ("morro-de-sao-paulo",                  "Morro de São Paulo",     -13.38, -38.91, "Sep 2019", "brazil"),
    ("santo-antonio-do-paraguacu",          "Sto. Antônio Paraguaçu", -12.68, -38.96, "Sep 2019", "brazil"),
    ("itaparica",                           "Itaparica",              -12.89, -38.69, "Nov 2019", "brazil"),
    # ── Brazil: north-east ────────────────────────────────────────────────
    ("crossing-the-equator",               "Equator",                  -3.00, -35.50, "Oct 2019", "brazil"),
    ("recife",                             "Recife",                   -8.05, -34.88, "Nov 2019", "brazil"),
    ("olinda",                             "Olinda",                   -7.99, -34.85, "Nov 2019", "brazil"),
    ("jacare",                             "Jacaré",                   -7.03, -34.85, "Nov 2019", "brazil"),
    ("pipa",                               "Pipa Beach",               -6.23, -35.05, "Nov 2019", "brazil"),
    ("tibao-do-sul",                       "Tibão do Sul",             -6.19, -35.09, "Nov 2019", "brazil"),
    ("joao-pessoa",                        "João Pessoa",              -7.12, -34.86, "Nov 2019", "brazil"),
    ("fortaleza",                          "Fortaleza",                -3.72, -38.54, "Nov 2019", "brazil"),
    ("from-brazil-to-the-caribbean-in-60-seconds","Fortaleza",        -3.72, -38.54, "Dec 2019", "brazil"),
    # ── Caribbean passage & French Guiana ─────────────────────────────────
    ("french-guiana",                      "French Guiana",             4.94, -52.33, "Dec 2019", "caribbean"),
    ("trinidad",                           "Trinidad",                 10.69, -61.22, "Dec 2019", "caribbean"),
    ("tobago",                             "Tobago",                   11.19, -60.69, "Jan 2020", "caribbean"),
    ("grenada",                            "Grenada",                  12.12, -61.68, "Jan 2020", "caribbean"),
    # ── Caribbean: COVID lockdown year ────────────────────────────────────
    ("covid-19-in-paradise",              "Grenada",                   12.12, -61.68, "Mar 2020", "caribbean"),
    ("hurricanes-and-caribbean",          "Grenada",                   12.12, -61.68, "Aug 2020", "caribbean"),
    ("oroboros-energy-system",            "Grenada",                   12.12, -61.68, "Aug 2020", "caribbean"),
    ("water-maker",                       "Grenada",                   12.12, -61.68, "Sep 2020", "caribbean"),
    ("one-year-in-the-caribbean",         "Grenada",                   12.12, -61.68, "Nov 2020", "caribbean"),
    ("vendee-globe-2020",                 "Grenada",                   12.12, -61.68, "Nov 2020", "caribbean"),
    ("how-to-rebuild-a-spectra-watermaker","Grenada",                  12.12, -61.68, "Dec 2020", "caribbean"),
    ("recap-of-year-2020",                "Grenada",                   12.12, -61.68, "Dec 2020", "caribbean"),
    # ── 2021: Greater Antilles → Bahamas ──────────────────────────────────
    ("entering-the-greater-antilles",     "US Virgin Islands",         18.34, -64.89, "Jan 2021", "caribbean"),
    ("us-virgin-islands",                 "US Virgin Islands",         18.34, -64.89, "Apr 2021", "caribbean"),
    ("spanish-virgin-islands",            "Spanish Virgin Islands",    18.35, -65.45, "Apr 2021", "caribbean"),
    ("puerto-rico",                       "Puerto Rico",               18.22, -66.59, "Apr 2021", "caribbean"),
    ("anti-fouling-review-pettit-trinidad-pro-sucks","Puerto Rico",   18.22, -66.59, "Apr 2021", "caribbean"),
    ("dominican-republic",                "Dominican Republic",        18.49, -69.93, "Apr 2021", "caribbean"),
    ("sailing-in-the-bahamas",            "Bahamas",                   24.70, -77.79, "Apr 2021", "caribbean"),
    # ── 2021: 2nd Atlantic Crossing ───────────────────────────────────────
    ("2nd-atlantic-crossing",             "North Atlantic",            35.00, -45.00, "Sep 2021", "atlantic"),
]

# ── Snap every post to the nearest GPS point on the actual route ──────────────
print("\n── Matching posts to route ───────────────────────────────────────────")

snapped = {}   # slug → (lat, lon)
for slug, name, alat, alon, date, region in POST_LOCS:
    pt = nearest(alat, alon, all_pts)
    snapped[slug] = (round(pt[0], 4), round(pt[1], 4))

# ── Cluster nearby posts into one map pin ────────────────────────────────────
def coord_key(lat, lon, prec=2):
    return (round(lat, prec), round(lon, prec))

clusters = defaultdict(list)
for slug, name, alat, alon, date, region in POST_LOCS:
    lat, lon = snapped[slug]
    clusters[coord_key(lat, lon)].append((slug, name, date, region, lat, lon))

# Build waypoints list: one pin per cluster, primary = first post
waypoints_out = []
seen_keys = set()
for slug, name, alat, alon, date, region in POST_LOCS:
    lat, lon = snapped[slug]
    ck = coord_key(lat, lon)
    if ck in seen_keys:
        continue
    seen_keys.add(ck)
    group = clusters[ck]
    waypoints_out.append({
        'name':   group[0][1],
        'coords': [group[0][4], group[0][5]],
        'date':   group[0][2],
        'slug':   group[0][0],
        'slugs':  [g[0] for g in group],
        'region': group[0][3],
    })

# ── Extra geographic waypoints (named GPS saves + key milestone positions) ────
# These are shown on the map but don't link to blog posts.
# Coordinates are snapped to the nearest real track point.
EXTRA = [
    # Atlantic milestones 2021
    ("azores",         "Azores",          38.52, -28.71, "2021", "atlantic"),
    ("lisbon",         "Lisbon",          38.72,  -9.14, "2021", "europe"),
    ("gibraltar",      "Gibraltar",       36.14,  -5.35, "2021", "europe"),
    # Med 2021-2022 (from named GPX waypoints)
    ("trafalgar",      "Cape Trafalgar",  36.17,  -6.04, "2021", "europe"),
    ("sotogrande",     "Sotogrande",      36.28,  -5.27, "2021", "europe"),
    ("cabo-de-gata",   "Cabo de Gata",    36.71,  -2.19, "2021", "europe"),
    ("ibiza",          "Ibiza",           38.91,   1.46, "2021", "europe"),
    ("mallorca",       "Mallorca",        39.80,   2.69, "2021", "europe"),
    ("menorca",        "Menorca",         40.06,   4.02, "2021", "europe"),
    ("cadaques",       "Cadaqués",        42.29,   3.27, "2021", "europe"),
    ("marseille",      "Marseille",       43.30,   5.35, "2021", "europe"),
    ("st-tropez",      "Saint-Tropez",    43.27,   6.63, "2021", "europe"),
    ("nice",           "Nice",            43.69,   7.28, "2021", "europe"),
    ("corsica",        "Corsica",         42.58,   8.76, "2021", "europe"),
    ("sardinia",       "Sardinia",        41.14,   9.53, "2022", "europe"),
    ("elba",           "Elba",            42.77,  10.41, "2021", "europe"),
    # Med 2022-2025 (Turkey / Greece)
    ("sicily",         "Sicily",          37.50,  14.00, "2022", "europe"),
    ("turkey",         "Turkey",          37.34,  27.26, "2022", "europe"),
    ("dodecanese",     "Dodecanese",      36.45,  28.23, "2023", "europe"),
    ("athens",         "Athens/Aegean",   37.41,  23.13, "2024", "europe"),
    ("cyclades",       "Cyclades",        37.38,  25.24, "2024", "europe"),
    ("greece-current", "Greece (current)",36.98,  25.11, "2025", "europe"),
]
for wid, wname, wlat, wlon, wdate, wreg in EXTRA:
    pt = nearest(wlat, wlon, all_pts)
    waypoints_out.append({
        'name':   wname,
        'coords': [round(pt[0],4), round(pt[1],4)],
        'date':   wdate,
        'slug':   None,
        'slugs':  [],
        'region': wreg,
    })

print(f"  {len(waypoints_out)} map pins ({len(POST_LOCS)} posts + extras)")

# ── Summary table of all post matches ────────────────────────────────────────
print("\n── Post → coordinate match summary ──────────────────────────────────")
uncertain = []
for slug, name, alat, alon, date, region in POST_LOCS:
    lat, lon = snapped[slug]
    dist_deg = math.hypot(lat - alat, lon - alon)
    dist_km  = dist_deg * 111.0
    flag = " ⚠ UNCERTAIN" if dist_km > 200 else ""
    if flag: uncertain.append(slug)
    print(f"  {'OK' if not flag else '??'}  {date:10s}  {name:35s}  "
          f"{lat:8.3f},{lon:8.3f}  snap_err={dist_km:.0f}km  {slug}{flag}")

print(f"\n  Uncertain matches ({len(uncertain)}):")
for s in uncertain:
    print(f"    {s}")

# ── Generate js/map.js ────────────────────────────────────────────────────────

route1_js        = json.dumps([[round(p[0],4), round(p[1],4)] for p in simp1])
route2_js        = json.dumps([[round(p[0],4), round(p[1],4)] for p in simp2])
sardinia_paros_js = json.dumps(GAP_WAYPOINTS)
leros_didim_js   = json.dumps(LEROS_DIDIM)
didim_patmos_js  = json.dumps(DIDIM_PATMOS)
mykonos_didim_js = json.dumps(MYKONOS_DIDIM)
didim_mykonos_js = json.dumps(DIDIM_MYKONOS)

# Pre-join so f-string doesn't contain backslash inside {}
wp_lines = []
for wp in waypoints_out:
    wp_lines.append(
        f'  {{ name:{json.dumps(wp["name"])}, '
        f'coords:{json.dumps(wp["coords"])}, '
        f'date:{json.dumps(wp["date"])}, '
        f'slug:{json.dumps(wp["slug"])}, '
        f'slugs:{json.dumps(wp["slugs"])}, '
        f'region:{json.dumps(wp["region"])} }}'
    )

wp_block = ',\n'.join(wp_lines)

simp_total = len(simp1) + len(simp2)
MAPJS = f'''/* ============================================
   Sailing Oroboro — Journey Map
   GPS sources:
     TracksOROBOROall.gpx   (Cape Town → Caribbean 2020, 8 tracks)
     Archive_08_20_2021.gpx (Grenada → Azores → Elba,    3 tracks)
     TRACK1234_2022.gpx     (Elba → N. Sardinia,          1 track)
     Archive_05_01_2025.gpx (Turkey → Greek islands,      5 tracks)
     Tracks060626.gpx       (Greek Aegean / Sporades,      6 tracks)
   Reconstructed routes (solid, no GPS):
     Sardinia → E coast → Egadi → SW Sicily → Licata → Malta → Pylos → Peloponnese → Milos → Paros
     Lakki (Leros) → Didim  |  Didim → Patmos
     Mykonos → Didim  |  Didim → Mykonos
   Raw GPS points : {raw_total:,}  →  simplified to {simp_total:,}
   ============================================ */

// ── GPS segments ───────────────────────────────────────────────────
const ROUTE_PT1 = {route1_js};      // Cape Town → N. Sardinia (real GPS)
const ROUTE_PT2 = {route2_js};      // Turkey → Greek Aegean/Sporades (real GPS)

// ── Reconstructed routes (no GPS, waypoint-based) ─────────────────
const ROUTE_SARDINIA_PAROS = {sardinia_paros_js};  // La Maddalena → E. Sardinia → Egadi → Licata → Malta → Pylos → Peloponnese → Milos → Parikia
const ROUTE_LEROS_DIDIM    = {leros_didim_js};     // Lakki, Leros → Didim marina
const ROUTE_DIDIM_PATMOS   = {didim_patmos_js};    // Didim marina → Skala, Patmos
const ROUTE_MYKONOS_DIDIM  = {mykonos_didim_js};   // Mykonos → Didim
const ROUTE_DIDIM_MYKONOS  = {didim_mykonos_js};   // Didim → Mykonos

// For minimap start/end markers
const ROUTE_COORDS = ROUTE_PT1.concat(ROUTE_PT2);

const WAYPOINTS = [
{wp_block}
];

/* ─ Map initialisation ─────────────────────────────────────────── */
function initMap(containerId) {{
  const map = L.map(containerId, {{
    center: [10, -20],
    zoom: 3,
    zoomControl: true,
  }});

  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 18,
  }}).addTo(map);

  // All route segments — solid lines throughout
  const solidStyle = {{ color: '#2E86AB', weight: 2.5, opacity: 0.80, lineJoin: 'round' }};
  [ROUTE_PT1, ROUTE_SARDINIA_PAROS, ROUTE_PT2,
   ROUTE_LEROS_DIDIM, ROUTE_DIDIM_PATMOS,
   ROUTE_MYKONOS_DIDIM, ROUTE_DIDIM_MYKONOS
  ].forEach(seg => L.polyline(seg, solidStyle).addTo(map));

  // Continent labels
  const contStyle = 'font-family:Georgia,serif;font-size:12px;color:rgba(80,100,130,0.45);font-style:italic;letter-spacing:0.12em;text-transform:uppercase;white-space:nowrap;pointer-events:none;user-select:none;';
  [
    {{ name:'North America', lat: 47.0, lon:-102.0 }},
    {{ name:'South America', lat:-14.0, lon: -58.0 }},
    {{ name:'Africa',        lat:  2.0, lon:  22.0 }},
    {{ name:'Europe',        lat: 52.0, lon:  16.0 }},
    {{ name:'Asia',          lat: 42.0, lon:  75.0 }},
  ].forEach(c => L.marker([c.lat, c.lon], {{
    icon: L.divIcon({{ className:'', html:`<span style="${{contStyle}}">${{c.name}}</span>`, iconSize:[160,20], iconAnchor:[80,10] }}),
    interactive: false, keyboard: false,
  }}).addTo(map));

  // ── Marker icons ────────────────────────────────────────────
  const makeIcon = () => L.divIcon({{
    className: '',
    html: '<div style="width:11px;height:11px;background:#2E86AB;border:2.5px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.35);"></div>',
    iconSize: [11,11], iconAnchor: [5,5],
  }});
  const makeActiveIcon = () => L.divIcon({{
    className: '',
    html: '<div style="width:16px;height:16px;background:#E76F51;border:3px solid white;border-radius:50%;box-shadow:0 0 0 5px rgba(231,111,81,0.28),0 2px 10px rgba(0,0,0,0.3);"></div>',
    iconSize: [16,16], iconAnchor: [8,8],
  }});

  // ── Build all markers ────────────────────────────────────────
  const allMarkers = [];
  let activeIdx = -1;

  // activateWaypoint: highlight dot, open popup, sync sidebar
  function activateWaypoint(idx) {{
    if (activeIdx >= 0 && allMarkers[activeIdx]) {{
      allMarkers[activeIdx].setIcon(makeIcon());
    }}
    activeIdx = idx;
    allMarkers[idx].setIcon(makeActiveIcon());
    allMarkers[idx].openPopup();
    map.setView(WAYPOINTS[idx].coords, 7, {{ animate: true }});
    document.querySelectorAll('.waypoint-item').forEach(el => el.classList.remove('active'));
    const sidebarItem = document.querySelector('[data-waypoint="' + idx + '"]');
    if (sidebarItem) {{
      sidebarItem.classList.add('active');
      sidebarItem.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
    }}
  }}

  WAYPOINTS.forEach((wp, i) => {{
    const marker = L.marker(wp.coords, {{ icon: makeIcon() }}).addTo(map);
    allMarkers.push(marker);

    let links = '';
    if (wp.slugs && wp.slugs.length) {{
      links = wp.slugs
        .map(s => `<a href="/posts/${{s}}.html" style="display:block;font-size:11px;color:#2E86AB;font-weight:600;margin-top:4px;">${{s.replace(/-/g,' ').replace(/%c2%bd/g,'\xbd')}}</a>`)
        .join('');
    }}

    const popup = `<div style="font-family:Inter,sans-serif;min-width:160px">
      <strong style="display:block;margin-bottom:3px;color:#0B1426">${{wp.name}}</strong>
      <span style="font-size:11px;color:#6B7B8D">${{wp.date}}</span>
      ${{links}}
    </div>`;

    marker.bindPopup(popup, {{ maxWidth: 260, className: 'oroboro-popup' }});
    // Clicking the dot also activates the sidebar item
    marker.on('click', () => activateWaypoint(i));
  }});

  // ── Sidebar → map (event delegation — works regardless of init order) ──
  const wpList = document.querySelector('.waypoint-list');
  if (wpList) {{
    wpList.addEventListener('click', e => {{
      const item = e.target.closest('.waypoint-item');
      if (!item) return;
      const idx = parseInt(item.dataset.waypoint, 10);
      if (!isNaN(idx) && idx >= 0 && idx < allMarkers.length) activateWaypoint(idx);
    }});
  }}

  const style = document.createElement('style');
  style.textContent = `.oroboro-popup .leaflet-popup-content-wrapper{{border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.15);padding:4px}}.oroboro-popup .leaflet-popup-tip{{background:#fff}}`;
  document.head.appendChild(style);

  return map;
}}

/* ─ Mini-map (homepage) ────────────────────────────────────────── */
function initMiniMap(containerId) {{
  const map = L.map(containerId, {{
    center: [10, -20], zoom: 2,
    zoomControl: false, scrollWheelZoom: false,
    doubleClickZoom: false, dragging: false, attributionControl: false,
  }});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',
    {{ maxZoom: 10 }}).addTo(map);
  [ROUTE_PT1, ROUTE_SARDINIA_PAROS, ROUTE_PT2,
   ROUTE_LEROS_DIDIM, ROUTE_DIDIM_PATMOS,
   ROUTE_MYKONOS_DIDIM, ROUTE_DIDIM_MYKONOS
  ].forEach(seg => L.polyline(seg, {{ color: '#2E86AB', weight: 2, opacity: 0.85 }}).addTo(map));
  return map;
}}

document.addEventListener('DOMContentLoaded', () => {{
  if (document.getElementById('journey-map')) initMap('journey-map');
  if (document.getElementById('mini-map'))    initMiniMap('mini-map');
}});
'''

out = REPO / 'js' / 'map.js'
out.write_text(MAPJS, encoding='utf-8')
size_kb = out.stat().st_size / 1024
print(f"\n── Done ──────────────────────────────────────────────────────────────")
print(f"  Seg1              : {len(simp1):,} pts  (Cape Town → N. Sardinia)")
print(f"  Sardinia → Paros  : {len(GAP_WAYPOINTS)} waypoints  (solid, reconstructed)")
print(f"  Seg2              : {len(simp2):,} pts  (Turkey → Sporades)")
print(f"  Leros → Didim     : {len(LEROS_DIDIM)} waypoints")
print(f"  Didim → Patmos    : {len(DIDIM_PATMOS)} waypoints")
print(f"  Mykonos → Didim   : {len(MYKONOS_DIDIM)} waypoints")
print(f"  Didim → Mykonos   : {len(DIDIM_MYKONOS)} waypoints")
print(f"  Written: js/map.js  ({size_kb:.0f} KB)")
print(f"  Pins    : {len(waypoints_out)}")
