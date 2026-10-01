# Istanbul (historic peninsula, Golden Horn, Galata) — derived map data

This data is derived from OpenStreetMap.

**© OpenStreetMap contributors.** Available under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/ — https://www.openstreetmap.org/copyright

## What it is
`istanbul-core.bytes` is a derived database made from an OpenStreetMap extract. It is used by the game Qoop World
(qoop games) to draw the real streets, building footprints, coast, parks and sights of this area.

## How it was made (the method of the alterations)
- Downloaded: 27 September 2026, from the Overpass API (https://overpass-api.de), with the queries in `q-*.txt`.
- Area: south 41.000, west 28.960, north 41.030, east 28.985 (coastline: 40.995, 28.955, 41.035, 28.990).
- Processed with `build_city.py` (in this folder):
  `python3 build_city.py <folder with buildings/roads/coast/parks/sights/relations .json> istanbul-core.bytes 41.000 28.960 41.030 28.985`
  The script keeps geometry and a few tags (building type, levels, height; road type, bridge; names of mosques,
  historic buildings and sights), simplifies lines, converts to metres from the middle of the area, and draws the
  land and sea as a 4 m raster from the coastline.

## File format
See the header of `build_city.py`: magic `QRC1`, the area, the land raster as runs per row, then the features
(kind, sub-type, levels, points in decimetres, name).

## Ground heights (added 29 September 2026)
The file ends with the ground's heights (`HGT1` section), from the Terrain Tiles on the AWS Registry of Open Data
(Tilezen/Mapzen, terrarium PNG, zoom 14; in Turkey from NASA's SRTM), fetched with `fetch_heights.py` for the same
box and appended by `build_city.py` / `add_heights.py`. Attribution for the terrain data:
https://github.com/tilezen/joerd/blob/master/docs/attribution.md
