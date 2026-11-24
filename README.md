# Lumina Materials

[English](README.md) · [简体中文](README_CN.md) · [Catalog layout](#catalog-layout) · [Offline bundles](#offline-bundles) · [Data license](#data-license) · [Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers)

Public filament calibration profiles and LUT presets for [Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers).

`public/v1/` is the active download catalog used by Lumina Studio to browse previews and fetch calibrated filament profiles or fixed-board LUTs on demand, without requiring a GitHub account.

## What is in the catalog

- **662 filament profiles** and **99 LUT presets** across official calibrations, community submissions, and manufacturer-contributed datasets (including the [Sixshuo PETG CMYW calibration](docs/manufacturer-sources.md)).
- Preserved provenance for every entry: original author, source attribution, original filename, resource ID, revision ID, and release channel (`official` or `community`).
- Anonymous download, like, and bookmark snapshots in `activity.json`, updated alongside the catalog.

## Using with Lumina Studio

Inside Lumina Studio, you can browse catalog previews and download only the filament profiles or LUTs you want to print with. Imported profiles and LUTs are saved in your local material library so they continue to work offline.

For instructions on photographing calibration boards, extracting your own filament profiles, and matching print settings, see the [Lumina Studio Wiki](https://wiki.luminastudio.com.cn/).

## Catalog layout

```text
public/v1/
├── DATA-LICENSE.md          # Lumina Data License 1.0 (bilingual)
├── materials/
│   ├── catalog.json         # Approved filament profile index
│   └── activity.json        # Anonymous download and bookmark counts
├── packages/                # Immutable filament profile ZIP archives
└── luts/
    ├── catalog.json         # Approved LUT preset index
    ├── activity.json        # Anonymous download and bookmark counts
    ├── packages/            # Immutable LUT ZIP archives
    └── previews/            # Swatch and palette preview images
```

Earlier top-level directories (`materials-src/`, `packages/`, `luts-src/`, `lut-packages/`, and `seed/`) are retained for historical provenance; current tooling and releases read from `public/v1/`.

## Offline bundles

Versioned [GitHub Releases](https://github.com/lumina-layer-studio/Lumina-materials/releases) publish complete offline snapshots (`lumina-materials-seed.zip`, `lumina-luts-seed.zip`, and `resource-release.json`) containing all approved official and community entries at that release tag. You can browse these bundles locally and import individual profiles or LUTs as needed.

To build the offline seed archives locally from `public/v1/`:

```bash
python scripts/build_public_seeds.py \
  --public-dir public/v1 \
  --dataset-version 2026.11.18.1 \
  --output build/public-resources
```

The build script runs offline against the checked-in `public/v1/` snapshot, verifies every package's SHA-256 checksum and manifest identity, and packs the original distribution ZIPs unchanged alongside [DATA-LICENSE.md](DATA-LICENSE.md).

Run the local validation tests with:

```bash
python -m unittest discover -s tests
```

## Data license

Resources marked with `LicenseRef-Lumina-Data-1.0` are governed by the [Lumina Data License 1.0](DATA-LICENSE.md):

- **What you can do:** Download, study, modify, and use the data in your own print workflows; take paid printing commissions and sell physical prints or generated models; share the data or modified versions free of charge while keeping author, source, and license notices intact.
- **What is restricted:** Selling or reselling the dataset files or modified datasets, charging download fees, or placing the data behind paid resource libraries, memberships, or paid APIs.
- **Existing licenses:** Historical resources published under terms such as CC BY 4.0 remain under their original licenses. Trademarks, brand names, and logos belong to their respective owners.

See [DATA-LICENSE.md](DATA-LICENSE.md) for the full Chinese and English terms.
