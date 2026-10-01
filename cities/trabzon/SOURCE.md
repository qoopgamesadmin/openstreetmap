# trabzon — derived map data

This data is derived from OpenStreetMap.

**© OpenStreetMap contributors.** Available under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/ — https://www.openstreetmap.org/copyright

## What it is
`trabzon.bytes` is a derived database made from an OpenStreetMap extract. It is used by the game Qoop World
(qoop games) to draw the real streets, building footprints, coast, parks and sights of this area.

## How it was made (the method of the alterations)
- Downloaded: 27 September 2026, from the Overpass API (https://overpass-api.de), with the queries in `q-*.txt`.
- Area: south 40.995, west 39.715, north 41.012, east 39.745 (coastline: 0.005° wider).
- Processed with `build_city.py` (in this folder):
  `python3 build_city.py <folder with buildings/roads/coast/parks/sights/relations .json> trabzon.bytes 40.995 39.715 41.012 39.745`
  The script keeps geometry and a few tags (building type, levels, height; road type, bridge; names of mosques,
  historic buildings and sights), simplifies lines, converts to metres from the middle of the area, and draws the
  land and sea as a 4 m raster from the coastline.

## File format
See the header of `build_city.py`: magic `QRC1`, the area, the land raster as runs per row, then the features
(kind, sub-type, levels, points in decimetres, name).
