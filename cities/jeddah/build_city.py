#!/usr/bin/env python3
"""
Turns OpenStreetMap extracts (Overpass JSON, `out geom`) into a compact city file for the game
(RealCityData.cs reads it). Data © OpenStreetMap contributors, ODbL.

    build_city.py <in-dir> <out.bytes> <south> <west> <north> <east>

in-dir holds buildings.json, roads.json, coast.json, parks.json, sights.json, water.json (rivers and streams,
optional), and heights.json if
fetch_heights.py was run for it (the ground's heights, appended to the file).
Coordinates become metres from the middle of the box (x east, z north). The land is a raster: the coastline
is drawn into it, the cells on its left are land and on its right water (OSM's rule), then both sides are
flooded out from there.
"""
import json, math, struct, sys
from collections import deque

src, out = sys.argv[1], sys.argv[2]
S, W, N, E = map(float, sys.argv[3:7])
lat0, lon0 = (S + N) / 2, (W + E) / 2
KY = 111320.0
KX = 111320.0 * math.cos(math.radians(lat0))

def xy(p):
    return ((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY)

minx, maxx = (W - lon0) * KX, (E - lon0) * KX
minz, maxz = (S - lat0) * KY, (N - lat0) * KY

def load(name):
    try:
        return json.load(open(f"{src}/{name}.json"))['elements']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        # A missing or failed download (the server's busy page) counts as none: inland towns have no coast.
        print(f"  ({name}: none)")
        return []

def simplify(pts, tol):
    if len(pts) < 3: return pts
    def rdp(a, b):
        (ax, az), (bx, bz) = pts[a], pts[b]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz) or 1e-9
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, pz = pts[i]
            d = abs(dz * px - dx * pz + bx * az - bz * ax) / L
            if d > best: best, bi = d, i
        if best > tol:
            return rdp(a, bi)[:-1] + rdp(bi, b)
        return [pts[a], pts[b]]
    return rdp(0, len(pts) - 1)

def inside(p):
    return minx - 50 <= p[0] <= maxx + 50 and minz - 50 <= p[1] <= maxz + 50

# ---- land raster ---------------------------------------------------------------------------------------
CELL = 4.0
GW, GH = int((maxx - minx) / CELL) + 1, int((maxz - minz) / CELL) + 1
grid = bytearray(GW * GH)          # 0 unknown, 1 land, 2 water, 3 coast
seeds = []
def cell(x, z):
    return int((x - minx) / CELL), int((z - minz) / CELL)
for way in load('coast'):
    g = [xy(p) for p in way.get('geometry', [])]
    for (ax, az), (bx, bz) in zip(g, g[1:]):
        L = math.hypot(bx - ax, bz - az)
        steps = max(1, int(L / (CELL * 0.5)))
        nx, nz = -(bz - az) / (L or 1), (bx - ax) / (L or 1)      # the left of the way's direction
        for i in range(steps + 1):
            t = i / steps
            px, pz = ax + (bx - ax) * t, az + (bz - az) * t
            cx, cz = cell(px, pz)
            if 0 <= cx < GW and 0 <= cz < GH: grid[cz * GW + cx] = 3
            for side, mark in ((1, 1), (-1, 2)):
                sx, sz = cell(px + nx * side * CELL * 1.5, pz + nz * side * CELL * 1.5)
                if 0 <= sx < GW and 0 <= sz < GH: seeds.append((sx, sz, mark))
q = deque()
for sx, sz, mark in seeds:
    i = sz * GW + sx
    if grid[i] == 0:
        grid[i] = mark
        q.append((sx, sz))
while q:
    x, z = q.popleft()
    mark = grid[z * GW + x]
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx_, nz_ = x + dx, z + dz
        if 0 <= nx_ < GW and 0 <= nz_ < GH and grid[nz_ * GW + nx_] == 0:
            grid[nz_ * GW + nx_] = mark
            q.append((nx_, nz_))
land = [1 if v in (0, 1, 3) else 0 for v in grid]

# ---- things ----------------------------------------------------------------------------------------------
things = []   # (kind, sub, levels, name, points)
def outer_rings(rel):
    """A multipolygon's outer rings: its outer members, joined end to end where they are split."""
    parts = [[(p['lat'], p['lon']) for p in m.get('geometry', [])] for m in rel.get('members', [])
             if m.get('role') == 'outer' and m.get('geometry')]
    rings = []
    while parts:
        ring = parts.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, part in enumerate(parts):
                if part[0] == ring[-1]: ring += part[1:]
                elif part[-1] == ring[-1]: ring += part[::-1][1:]
                elif part[-1] == ring[0]: ring = part[:-1] + ring
                elif part[0] == ring[0]: ring = part[::-1][:-1] + ring
                else: continue
                parts.pop(i); changed = True; break
        if ring[0] == ring[-1] and len(ring) >= 4: rings.append([{'lat': a, 'lon': b} for a, b in ring])
    return rings

def joined_rings(rel, roles):
    """A multipolygon's rings of these roles, their ways joined end to end; what never closes is left out."""
    parts = [[(p['lat'], p['lon']) for p in m.get('geometry', [])] for m in rel.get('members', [])
             if m.get('role') in roles and m.get('geometry')]
    rings = []
    while parts:
        ring = parts.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, part in enumerate(parts):
                if part[0] == ring[-1]: ring += part[1:]
                elif part[-1] == ring[-1]: ring += part[::-1][1:]
                elif part[-1] == ring[0]: ring = part[:-1] + ring
                elif part[0] == ring[0]: ring = part[::-1][:-1] + ring
                else: continue
                parts.pop(i); changed = True; break
        if ring[0] == ring[-1] and len(ring) >= 4: rings.append([{'lat': a, 'lon': b} for a, b in ring])
    return rings

def latin(text):
    """Whether the game's fonts can draw a name: Latin letters (with Turkish and European accents), digits, marks."""
    return all(ord(ch) < 0x250 or ch in '’–—' for ch in text)

def pick_name(tags):
    """The name a Turkish child reads best: Turkish, else English, else the local one if it is in Latin letters
    (Tokyo's and Cairo's are not, and the game's fonts would draw boxes)."""
    for key in ('name:tr', 'name:en', 'name'):
        n = tags.get(key, '').strip()
        if n and latin(n): return n
    return ''

# ---- inland water: rivers' beds, lakes, docks (waterarea.json, natural=water / waterway=riverbank) -------------
# Drawn into the land raster as water, so the Thames and the Seine are water as wide as they are, not a line.
# Even-odd over each area's rings: an island in a river (a multipolygon's inner ring) stays land.
def poly_area(ring):
    return abs(sum(ax * bz - bx * az for (ax, az), (bx, bz) in zip(ring, ring[1:] + ring[:1]))) / 2
def fill_water(rings):
    zs = [z for r in rings for _, z in r]
    for cz in range(max(0, cell(0, min(zs))[1]), min(GH, cell(0, max(zs))[1] + 1)):
        zc = minz + (cz + 0.5) * CELL
        xs = []
        for r in rings:
            for (ax, az), (bx, bz) in zip(r, r[1:] + r[:1]):
                if (az <= zc < bz) or (bz <= zc < az):
                    xs.append(ax + (zc - az) * (bx - ax) / (bz - az))
        xs.sort()
        for x0, x1 in zip(xs[0::2], xs[1::2]):
            for cx in range(max(0, cell(x0, 0)[0]), min(GW, cell(x1, 0)[0] + 1)):
                land[cz * GW + cx] = 0
water_areas = 0
for w in load('waterarea'):
    if w.get('type') == 'relation':
        # A big water's rings come as many ways (Venice's lagoon): joined end to end into closed rings first — each
        # way closed on its own drew water across the islands.
        rings = [[xy(p) for p in ring] for ring in joined_rings(w, ('outer', 'inner'))]
    else:
        rings = [[xy(p) for p in w.get('geometry', [])]]
    rings = [r[:-1] if len(r) > 1 and r[0] == r[-1] else r for r in rings]
    rings = [r for r in rings if len(r) >= 3]
    if not rings or max(poly_area(r) for r in rings) < 1500: continue          # a fountain, a garden pond
    fill_water(rings)
    water_areas += 1
if water_areas: print(f"  inland water: {water_areas} areas; land {100 * sum(land) // max(1, len(land))}%")

buildings = list(load('buildings'))
for rel in load('relations') or load('rel'):   # the downloads have it as rel.json
    for ring in outer_rings(rel):
        buildings.append({'geometry': ring, 'tags': rel.get('tags', {})})

for b in buildings:
    g = [xy(p) for p in b.get('geometry', [])]
    if len(g) < 4 or not all(inside(p) for p in g): continue
    tags = b.get('tags', {})
    t = tags.get('building', 'yes')
    sub = 1 if t == 'mosque' or tags.get('religion') == 'muslim' and (tags.get('amenity') == 'place_of_worship' or t == 'mosque') else \
          2 if t in ('apartments', 'residential', 'house') else \
          3 if t in ('commercial', 'retail', 'hotel', 'office') else \
          4 if t in ('school', 'university', 'public', 'civic', 'government') else \
          5 if tags.get('historic') or t in ('palace', 'castle', 'church', 'tower') else 0
    try: levels = int(float(tags.get('building:levels', '0')))
    except ValueError: levels = 0
    # A real height wins: Galata Tower is 62.6 m, which is no number of floors.
    try:
        h = float(str(tags.get('height', '0')).replace('m', '').strip())
        if h > 0: levels = int(round(h / 3.2))
    except ValueError: pass
    name = pick_name(tags) if sub in (1, 5) else ''
    things.append((1, sub, max(0, min(levels, 30)), name, simplify(g[:-1], 0.6)))
ROAD = {'primary': 0, 'secondary': 0, 'tertiary': 0, 'primary_link': 0, 'secondary_link': 0, 'tertiary_link': 0, 'trunk': 0,
        'residential': 1, 'living_street': 1, 'service': 1, 'unclassified': 1,
        'pedestrian': 2, 'footway': 2, 'steps': 3, 'cycleway': 2, 'path': 2}
for r in load('roads'):
    tags = r.get('tags', {})
    sub = ROAD.get(tags.get('highway'))
    if sub is None: continue
    g = [xy(p) for p in r.get('geometry', [])]
    if len(g) < 2: continue
    bridge = 1 if tags.get('bridge') == 'yes' else 0
    things.append((2, sub + (10 if bridge else 0), 0, tags.get('name', '') if bridge else '', simplify(g, 1.0)))
for p in load('parks'):
    g = [xy(q) for q in p.get('geometry', [])]
    if len(g) >= 4: things.append((4, 0, 0, '', simplify(g[:-1], 1.0)))
# Rivers and streams (water.json, when downloaded): kind 6, sub 0 a river, 1 a stream; their names kept.
for w in load('water'):
    tags = w.get('tags', {})
    g = [xy(p) for p in w.get('geometry', [])]
    if len(g) < 2: continue
    things.append((6, 0 if tags.get('waterway') == 'river' else 1, 0, tags.get('name', ''), simplify(g, 1.5)))
for s in load('sights'):
    tags = s.get('tags', {})
    name = pick_name(tags)
    c = s.get('center') or ({'lat': s['lat'], 'lon': s['lon']} if 'lat' in s else None)
    if not name or not c: continue
    things.append((5, 0, 0, name, [xy(c)]))

# ---- write -----------------------------------------------------------------------------------------------
def dm(v): return max(-32767, min(32767, int(round(v * 10))))
with open(out, 'wb') as f:
    f.write(b'QRC1')
    f.write(struct.pack('<ffffffhh', lat0, lon0, minx, minz, maxx, maxz, GW, GH))
    f.write(struct.pack('<f', CELL))
    for z in range(GH):
        row = land[z * GW:(z + 1) * GW]
        runs, x = [], 0
        while x < GW:
            if row[x]:
                s0 = x
                while x < GW and row[x]: x += 1
                runs.append((s0, x - s0))
            else: x += 1
        f.write(struct.pack('<H', len(runs)))
        for s0, l in runs: f.write(struct.pack('<HH', s0, l))
    f.write(struct.pack('<I', len(things)))
    for kind, sub, levels, name, pts in things:
        nb = name.encode('utf-8')[:255]
        f.write(struct.pack('<BBBH', kind, sub, levels, len(pts)))
        for x, z in pts: f.write(struct.pack('<hh', dm(x), dm(z)))
        f.write(struct.pack('<B', len(nb))); f.write(nb)
    # The ground's heights, when fetch_heights.py has been run for this area: 'HGT1', the grid's size, spacing and
    # corner (metres, as above), the lowest height, then every point in decimetres above it, row by row from the
    # south-west. Files without it are flat, and older readers stop before it.
    try:
        hg = json.load(open(f"{src}/heights.json"))
        base = min(hg['h'])
        f.write(b'HGT1')
        f.write(struct.pack('<HHffff', hg['nx'], hg['nz'], hg['step'], hg['x0'], hg['z0'], base))
        f.write(struct.pack(f"<{len(hg['h'])}H", *[min(65535, int(round((h - base) * 10))) for h in hg['h']]))
        print(f"  heights {hg['nx']}x{hg['nz']} every {hg['step']} m, {base:.0f} to {max(hg['h']):.0f} m")
    except FileNotFoundError:
        pass
counts = {}
for t in things: counts[t[0]] = counts.get(t[0], 0) + 1
print(f"{out}: grid {GW}x{GH}, land {sum(land)}/{len(land)}, things {counts}")
