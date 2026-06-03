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

# ── Assemble ordered route ────────────────────────────────────────────────────
# Two solid GPS segments separated by an estimated gap (dashed on map):
#
#  SEGMENT 1 — Cape Town → N. Sardinia (continuous real GPS)
#   Phase 1 (2018-2020): Cape Town → Caribbean  — TracksOROBOROall.gpx
#   Phase 2 (2021-a)   : Grenada → Azores       — Archive_08_20_2021.gpx Track 1+2
#   Phase 2b(2021-b)   : Azores → Elba          — Archive_08_20_2021.gpx Track 3
#   Phase 3 (2022)     : Elba → N. Sardinia     — TRACK1234_2022.gpx Track 4
#
#  [GAP — estimated dashed line: N. Sardinia → Turkey, mid-2022, no GPS recorded]
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

# Estimated waypoints for the unrecorded gap (N. Sardinia → Turkey, mid-2022)
GAP_WAYPOINTS = [
    [41.30,  9.34],   # Porto Pozzo, N. Sardinia  (Track 4 endpoint)
    [39.22,  9.11],   # S. Sardinia / Cagliari
    [38.13, 13.37],   # Palermo, Sicily
    [38.26, 15.63],   # Strait of Messina
    [37.07, 15.29],   # SE Sicily / Siracusa
    [35.90, 14.51],   # Malta
    [36.50, 19.00],   # Central Ionian Sea
    [38.17, 20.49],   # Kefalonia / W. Greece
    [37.94, 22.95],   # Gulf of Corinth / Corinth Canal
    [37.63, 23.60],   # Athens / Saronic Gulf
    [37.36, 26.75],   # Samos/Ikaria (Track 13 start)
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
    ("welcome-to-brazil",                   "Vitória, Brazil",        -20.32, -40.34, "Mar 2019", "brazil"),
    ("how-to-repair-a-spectra-newport-watermaker", "Vitória",         -20.32, -40.34, "Mar 2019", "brazil"),
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

route1_js = json.dumps([[round(p[0],4), round(p[1],4)] for p in simp1])
route2_js = json.dumps([[round(p[0],4), round(p[1],4)] for p in simp2])
gap_js    = json.dumps(GAP_WAYPOINTS)

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
   Generated from real GPS tracks:
     TracksOROBOROall.gpx   (Cape Town → Caribbean 2020, 8 tracks)
     Archive_08_20_2021.gpx (Grenada → Azores → Elba,    3 tracks)
     TRACK1234_2022.gpx     (Elba → N. Sardinia,          1 track)
     [estimated gap]        (N. Sardinia → Turkey, mid-2022, no GPS)
     Archive_05_01_2025.gpx (Turkey → Greek islands,      5 tracks)
     Tracks060626.gpx       (Greek Aegean / Sporades,      6 tracks)
   Raw GPS points : {raw_total:,}  →  simplified to {simp_total:,}
   ============================================ */

// Two continuous GPS segments with an estimated gap between them
const ROUTE_PT1 = {route1_js};   // Cape Town → N. Sardinia
const ROUTE_PT2 = {route2_js};   // Turkey → Greek Aegean/Sporades
const ROUTE_GAP = {gap_js};      // estimated N. Sardinia → Turkey (dashed)

// Combined for backwards compatibility (minimap etc.)
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

  // Real GPS track — two solid segments
  const solidStyle = {{ color: '#2E86AB', weight: 2.5, opacity: 0.80, lineJoin: 'round' }};
  L.polyline(ROUTE_PT1, solidStyle).addTo(map);
  L.polyline(ROUTE_PT2, solidStyle).addTo(map);

  // Estimated gap: N. Sardinia → Turkey (mid-2022, no GPS recorded)
  L.polyline(ROUTE_GAP, {{
    color: '#2E86AB', weight: 2, opacity: 0.45,
    dashArray: '6, 7', lineJoin: 'round',
  }}).addTo(map);

  const makeIcon = (color = '#2E86AB') => L.divIcon({{
    className: '',
    html: `<div style="width:11px;height:11px;background:${{color}};border:2.5px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.35);"></div>`,
    iconSize: [11,11], iconAnchor: [5,5],
  }});

  const currentIcon = L.divIcon({{
    className: '',
    html: `<div style="width:14px;height:14px;background:#E76F51;border:3px solid white;border-radius:50%;box-shadow:0 2px 8px rgba(231,111,81,.6);animation:pulse 2s infinite;"></div><style>@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(231,111,81,.4)}}50%{{box-shadow:0 0 0 8px rgba(231,111,81,0)}}}}</style>`,
    iconSize: [14,14], iconAnchor: [7,7],
  }});

  WAYPOINTS.forEach((wp, i) => {{
    const isLast = (i === WAYPOINTS.length - 1);
    const icon   = isLast ? currentIcon : makeIcon();

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

    const marker = L.marker(wp.coords, {{ icon }}).addTo(map);
    marker.bindPopup(popup, {{ maxWidth: 260, className: 'oroboro-popup' }});

    // Sidebar interaction
    const item = document.querySelector(`[data-waypoint="${{i}}"]`);
    if (item) {{
      item.addEventListener('click', () => {{
        map.setView(wp.coords, 7, {{ animate: true }});
        marker.openPopup();
        document.querySelectorAll('.waypoint-item').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
      }});
    }}
  }});

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
  L.polyline(ROUTE_PT1, {{ color: '#2E86AB', weight: 2, opacity: 0.85 }}).addTo(map);
  L.polyline(ROUTE_PT2, {{ color: '#2E86AB', weight: 2, opacity: 0.85 }}).addTo(map);
  L.polyline(ROUTE_GAP, {{ color: '#2E86AB', weight: 1.5, opacity: 0.4, dashArray: '5, 6' }}).addTo(map);
  L.circleMarker(ROUTE_PT1[0],
    {{ radius: 5, color: '#E9C46A', fillColor: '#E9C46A', fillOpacity: 1, weight: 2 }}).addTo(map);
  L.circleMarker(ROUTE_PT2[ROUTE_PT2.length - 1],
    {{ radius: 6, color: '#E76F51', fillColor: '#E76F51', fillOpacity: 1, weight: 2 }}).addTo(map);
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
print(f"  Seg1    : {len(simp1):,} pts  (Cape Town → N. Sardinia)")
print(f"  Gap     : {len(GAP_WAYPOINTS)} estimated waypoints  (dashed)")
print(f"  Seg2    : {len(simp2):,} pts  (Turkey → Sporades)")
print(f"  Written: js/map.js  ({size_kb:.0f} KB)")
print(f"  Pins    : {len(waypoints_out)}")
