#!/usr/bin/env python3
"""
The real cities' street names, beside their city files (RealCityStreets reads them): every named street of the city's
box from OpenStreetMap (Overpass JSON, `out geom`), in the same metres as the city file (read from its header), its
name as a child reads it best (build_city.pick_name) and its kind of road. A file of its own so the city files — and
the plots bought in them, numbered by their buildings — stay exactly as they are. Data © OpenStreetMap contributors, ODbL.

    build_names.py <city.bytes> <out.names.bytes> [roads.json]

Without roads.json the named streets are fetched from Overpass for the city's box (kept beside the output as
<name>.roads.json, so a rebuild does not fetch again).
"""
import json, math, os, struct, sys, time, urllib.parse, urllib.request

city, out = sys.argv[1], sys.argv[2]
roads_path = sys.argv[3] if len(sys.argv) > 3 else None

with open(city, 'rb') as f:
    assert f.read(4) == b'QRC1', city
    lat0, lon0, minx, minz, maxx, maxz, gw, gh = struct.unpack('<ffffffhh', f.read(28))
KY = 111320.0
KX = 111320.0 * math.cos(math.radians(lat0))
S, N = lat0 + minz / KY, lat0 + maxz / KY
W, E = lon0 + minx / KX, lon0 + maxx / KX

if roads_path and os.path.exists(roads_path):
    elements = json.load(open(roads_path))['elements']
else:
    cache = out.replace('.names.bytes', '') + '.roads.json'
    if os.path.exists(cache):
        elements = json.load(open(cache))['elements']
    else:
        query = f'[out:json][timeout:180];way["highway"]["name"]({S:.5f},{W:.5f},{N:.5f},{E:.5f});out geom;'
        for attempt in range(4):
            try:
                req = urllib.request.Request('https://overpass-api.de/api/interpreter',
                                             data=urllib.parse.urlencode({'data': query}).encode(),
                                             headers={'User-Agent': 'qoop-world street names (ODbL)'})
                body = urllib.request.urlopen(req, timeout=240).read()
                elements = json.loads(body)['elements']
                open(cache, 'wb').write(body)
                break
            except Exception as e:
                print('  overpass:', e); time.sleep(20 * (attempt + 1))
        else:
            sys.exit('no streets for ' + city)

def latin(text):
    return all(ord(ch) < 0x250 or ch in '’–—' for ch in text)

def pick_name(tags):
    for key in ('name:tr', 'name:en', 'name'):
        n = tags.get(key, '').strip()
        if n and latin(n): return n
    return ''

ROAD = {'primary': 0, 'secondary': 0, 'tertiary': 0, 'primary_link': 0, 'secondary_link': 0, 'tertiary_link': 0, 'trunk': 0,
        'residential': 1, 'living_street': 1, 'service': 1, 'unclassified': 1,
        'pedestrian': 2, 'footway': 2, 'steps': 3, 'cycleway': 2, 'path': 2}

def xy(p):
    return ((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY)

streets = []
for r in elements:
    tags = r.get('tags', {})
    sub = ROAD.get(tags.get('highway'))
    name = pick_name(tags)
    if sub is None or not name: continue
    g = [xy(p) for p in r.get('geometry', [])]
    g = [p for p in g if minx - 20 <= p[0] <= maxx + 20 and minz - 20 <= p[1] <= maxz + 20]
    if len(g) < 2: continue
    streets.append((sub, name, g))

with open(out, 'wb') as f:
    f.write(b'QRN1')
    f.write(struct.pack('<i', len(streets)))
    for sub, name, g in streets:
        raw = name.encode('utf-8')[:255]
        f.write(struct.pack('<BB', sub, len(raw)))
        f.write(raw)
        f.write(struct.pack('<H', len(g)))
        for x, z in g:
            f.write(struct.pack('<ff', x, z))
print(f'{os.path.basename(out)}: {len(streets)} named streets, {len({s[1] for s in streets})} names')
