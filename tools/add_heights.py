#!/usr/bin/env python3
"""
Puts the ground's heights (fetch_heights.py's heights.json) on the end of a city file build_city.py already made,
replacing any heights it had — for cities whose OpenStreetMap extract is not kept, so the file need not be rebuilt.

    add_heights.py <city.bytes> <heights.json>

The heights must have been fetched for the same box the file was built for (the same middle, so the same metres).
"""
import json, struct, sys

path, heights = sys.argv[1], sys.argv[2]
data = open(path, 'rb').read()
assert data[:4] == b'QRC1', "not a city file"
pos = 4
lat0, lon0, minx, minz, maxx, maxz, GW, GH = struct.unpack_from('<ffffffhh', data, pos); pos += struct.calcsize('<ffffffhh')
pos += 4                                                        # the land raster's cell
for _ in range(GH):
    runs, = struct.unpack_from('<H', data, pos); pos += 2 + 4 * runs
count, = struct.unpack_from('<I', data, pos); pos += 4
for _ in range(count):
    kind, sub, levels, n = struct.unpack_from('<BBBH', data, pos); pos += 5 + 4 * n
    nb = data[pos]; pos += 1 + nb
hg = json.load(open(heights))
assert abs(hg['x0'] - minx) < 0.5 and abs(hg['z0'] - minz) < 0.5, f"heights for another box: {hg['x0']:.1f},{hg['z0']:.1f} vs {minx:.1f},{minz:.1f}"
base = min(hg['h'])
tail = b'HGT1' + struct.pack('<HHffff', hg['nx'], hg['nz'], hg['step'], hg['x0'], hg['z0'], base)
tail += struct.pack(f"<{len(hg['h'])}H", *[min(65535, int(round((h - base) * 10))) for h in hg['h']])
open(path, 'wb').write(data[:pos] + tail)
print(f"{path}: heights {hg['nx']}x{hg['nz']} every {hg['step']} m, {base:.0f} to {max(hg['h']):.0f} m (+{len(tail) // 1024} KB)")
