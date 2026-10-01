# Qoop World — OpenStreetMap derived data

**Map data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the
[Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).**

**Qoop World** (by qoop games) is a game for children in which you walk through
the real hearts of cities — Istanbul's historic peninsula, Paris, Venice, Ayder highland and nearly a hundred
more — with their real streets, building footprints, coasts, rivers, parks and sights. That map data comes from
OpenStreetMap.

The game itself is a *Produced Work*. The databases we derived from OpenStreetMap to make it are published here,
under the same licence, together with exactly how they were made, so anyone can use, check or rebuild them.

## What is here

| Path | What |
|---|---|
| [`cities/<key>/`](cities/) | One derived database per area: `<key>.bytes`, `SOURCE.md` (source, date, box, method), the Overpass queries `q-*.txt` and the scripts that built it |
| [`CITIES.md`](CITIES.md) | Index of all areas with their boxes and download dates |
| [`FORMAT.md`](FORMAT.md) | The binary file format (QRC1) |
| [`tools/qrc_to_geojson.py`](tools/qrc_to_geojson.py) | Converts a city file to GeoJSON (plus the land raster as PGM and heights as CSV) |
| [`tools/build_city.py`](tools/build_city.py) | Builds a city file from Overpass JSON (the latest version; each city folder keeps the one actually used) |
| [`tools/fetch_heights.py`](tools/fetch_heights.py), [`tools/add_heights.py`](tools/add_heights.py) | Ground heights for a box (not OpenStreetMap data, see [LICENSE](LICENSE)) |

## Use the data

```bash
python3 tools/qrc_to_geojson.py cities/istanbul-core/istanbul-core.bytes istanbul.geojson --land land.pgm --heights heights.csv
```

The GeoJSON opens in QGIS, geojson.io or any GIS tool. Python 3 only, no packages needed.

## Rebuild a city

1. Download the area with the queries in its folder (`q-*.txt`) from the [Overpass API](https://overpass-api.de),
   one JSON per query (`buildings.json`, `roads.json`, `coast.json`, `parks.json`, `sights.json`, `rel.json`,
   `water.json`, `waterarea.json`).
2. Optionally `python3 fetch_heights.py <folder> <south> <west> <north> <east>`.
3. `python3 build_city.py <folder> <key>.bytes <south> <west> <north> <east>` — the box is in the city's `SOURCE.md`.

## Licence

- Databases: **ODbL 1.0** — full text in [LICENSE-ODbL-1.0.md](LICENSE-ODbL-1.0.md). Individual contents: DbCL 1.0.
- If you use or share this data (or something derived from it), credit **“© OpenStreetMap contributors”**, keep it
  under the ODbL, and see <https://www.openstreetmap.org/copyright>.
- Ground heights: Terrain Tiles (Tilezen/Mapzen, AWS Open Data) — [attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md).

This repository is updated whenever a city is added to or changed in the game.

---

## Türkçe özet

Bu depo, **Qoop World** oyununda kullanılan ve OpenStreetMap'ten türetilen şehir haritası verilerini içerir.
Veriler OpenStreetMap lisansı **ODbL 1.0** ile herkese açıktır: **© OpenStreetMap katkıcıları**. Her şehrin klasöründe
verinin kendisi, ne zaman ve hangi sorgularla indirildiği ve nasıl işlendiği yer alır. `tools/qrc_to_geojson.py`
ile dosyalar GeoJSON'a çevrilebilir. Oyunun kendisi bu verilerden üretilmiş bir eserdir (Produced Work).
Oyun içinde açılış ekranında ve Ayarlar'da "Harita verisi © OpenStreetMap katkıcıları (ODbL)" yazar.
