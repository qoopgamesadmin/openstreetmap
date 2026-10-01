#!/usr/bin/env python3
"""
Reads a Qoop World city file (QRC1, see FORMAT.md) and writes its features as GeoJSON in longitude/latitude,
so the derived data can be used without the game. Data © OpenStreetMap contributors, ODbL 1.0.

    qrc_to_geojson.py <city.bytes> [out.geojson] [--land land.pgm] [--heights heights.csv]

--land writes the land/water raster as a PGM image (white land, black water, north up).
--heights writes the ground heights (when the file has them) as CSV: lon, lat, metres.
"""
import json, math, struct, sys

KINDS = {1: 'building', 2: 'road', 4: 'park', 5: 'sight', 6: 'waterway'}
BUILDING = {0: 'other', 1: 'place_of_worship (muslim)', 2: 'residential', 3: 'commercial', 4: 'public', 5: 'historic'}
ROAD = {0: 'main', 1: 'local', 2: 'path', 3: 'steps'}
WATERWAY = {0: 'river', 1: 'stream'}


class Reader:
    def __init__(self, data):
        self.d, self.i = data, 0

    def take(self, fmt):
        v = struct.unpack_from('<' + fmt, self.d, self.i)
        self.i += struct.calcsize('<' + fmt)
        return v

    def left(self):
        return len(self.d) - self.i


def read(path):
    r = Reader(open(path, 'rb').read())
    if r.d[:4] != b'QRC1':
        raise SystemExit(f"{path}: not a QRC1 file")
    r.i = 4
    lat0, lon0, minx, minz, maxx, maxz, gw, gh = r.take('ffffffhh')
    cell, = r.take('f')
    land = []
    for _ in range(gh):
        n, = r.take('H')
        land.append([r.take('HH') for _ in range(n)])
    count, = r.take('I')
    things = []
    for _ in range(count):
        kind, sub, levels, n = r.take('BBBH')
        pts = [(x / 10.0, z / 10.0) for x, z in (r.take('hh') for _ in range(n))]
        ln, = r.take('B')
        name = r.d[r.i:r.i + ln].decode('utf-8', 'replace'); r.i += ln
        things.append((kind, sub, levels, name, pts))
    heights = None
    if r.left() >= 4 and r.d[r.i:r.i + 4] == b'HGT1':
        r.i += 4
        nx, nz, step, x0, z0, base = r.take('HHffff')
        hs = r.take(f'{nx * nz}H')
        heights = (nx, nz, step, x0, z0, [base + h / 10.0 for h in hs])
    return dict(lat0=lat0, lon0=lon0, box=(minx, minz, maxx, maxz), size=(gw, gh), cell=cell,
                land=land, things=things, heights=heights)


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    opts = {}
    for flag in ('--land', '--heights'):
        if flag in args:
            k = args.index(flag); opts[flag] = args[k + 1]; del args[k:k + 2]
    src = args[0]
    out = args[1] if len(args) > 1 else src.rsplit('.', 1)[0] + '.geojson'
    c = read(src)
    ky = 111320.0
    kx = 111320.0 * math.cos(math.radians(c['lat0']))

    def ll(p):
        return [round(c['lon0'] + p[0] / kx, 7), round(c['lat0'] + p[1] / ky, 7)]

    feats = []
    for kind, sub, levels, name, pts in c['things']:
        props = {'kind': KINDS.get(kind, str(kind))}
        coords = [ll(p) for p in pts]
        if kind == 1:
            props['type'] = BUILDING.get(sub, str(sub))
            if levels: props['levels'] = levels
            geom = {'type': 'Polygon', 'coordinates': [coords + coords[:1]]}
        elif kind == 2:
            props['type'] = ROAD.get(sub % 10, str(sub))
            if sub >= 10: props['bridge'] = True
            geom = {'type': 'LineString', 'coordinates': coords}
        elif kind == 4:
            geom = {'type': 'Polygon', 'coordinates': [coords + coords[:1]]}
        elif kind == 5:
            geom = {'type': 'Point', 'coordinates': coords[0]}
        elif kind == 6:
            props['type'] = WATERWAY.get(sub, str(sub))
            geom = {'type': 'LineString', 'coordinates': coords}
        else:
            geom = {'type': 'LineString', 'coordinates': coords}
        if name: props['name'] = name
        feats.append({'type': 'Feature', 'properties': props, 'geometry': geom})

    fc = {'type': 'FeatureCollection',
          'attribution': '© OpenStreetMap contributors, ODbL 1.0 — https://www.openstreetmap.org/copyright',
          'features': feats}
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"{out}: {len(feats)} features")

    if '--land' in opts:
        gw, gh = c['size']
        rows = []
        for runs in reversed(c['land']):          # north up
            row = bytearray(gw)
            for s, n in runs: row[s:s + n] = b'\xff' * n
            rows.append(bytes(row))
        with open(opts['--land'], 'wb') as f:
            f.write(f"P5\n{gw} {gh}\n255\n".encode()); f.write(b''.join(rows))
        print(f"{opts['--land']}: {gw}x{gh} cells of {c['cell']} m")

    if '--heights' in opts and c['heights']:
        nx, nz, step, x0, z0, hs = c['heights']
        with open(opts['--heights'], 'w') as f:
            f.write('lon,lat,metres\n')
            for j in range(nz):
                for i in range(nx):
                    lon, lat = ll((x0 + i * step, z0 + j * step))
                    f.write(f"{lon},{lat},{hs[j * nx + i]:.1f}\n")
        print(f"{opts['--heights']}: {nx}x{nz} points every {step} m")


if __name__ == '__main__':
    main()
