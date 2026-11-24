# Lumina Materials

[English](README.md) · [简体中文](README_CN.md) · [Catalog layout](#catalog-layout) · [Offline bundles](#offline-bundles) · [Data license](#data-license) · [Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers)

Public filament calibration profiles and LUT presets for [Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers).

`public/v1/` is the active download catalog used by Lumina Studio to preview and download filament profiles or fixed-board LUTs on demand, without a GitHub account. Once imported into your local material library, profiles and LUTs work offline.

For calibration board printing and photography guides, see the [Lumina Studio Wiki](https://wiki.luminastudio.com.cn/).

## What is in the catalog

- Official calibrations, community submissions, and manufacturer-contributed profiles.
- Preserved provenance on every entry: author, source attribution, original filename, resource ID, revision ID, and release channel (`official` or `community`).
- Anonymous download, like, and bookmark snapshots in `activity.json`.

## Catalog layout

```text
public/v1/
├── DATA-LICENSE.md          # Lumina Data License 1.0 (bilingual)
├── materials/
│   ├── catalog.json         # Approved filament profile index
│   └── activity.json        # Anonymous download and bookmark counts
├── packages/                # Filament profile ZIP archives
└── luts/
    ├── catalog.json         # Approved LUT preset index
    ├── activity.json        # Anonymous download and bookmark counts
    ├── packages/            # LUT ZIP archives
    └── previews/            # Swatch and palette preview images
```

## Offline bundles

Versioned [GitHub Releases](https://github.com/lumina-layer-studio/Lumina-materials/releases) publish complete offline seed archives (`lumina-materials-seed.zip`, `lumina-luts-seed.zip`, and `resource-release.json`) for offline browsing and selective import.

To rebuild the seed archives locally from `public/v1/`:

```bash
python scripts/build_public_seeds.py \
  --public-dir public/v1 \
  --dataset-version 2026.11.18.1 \
  --output build/public-resources
```

The script verifies package SHA-256 digests and manifests locally and bundles the distribution ZIPs alongside [DATA-LICENSE.md](DATA-LICENSE.md). Run `python -m unittest discover -s tests` to execute the test suite.

## Data license

Resources marked with `LicenseRef-Lumina-Data-1.0` follow the [Lumina Data License 1.0](DATA-LICENSE.md):

- **Allowed:** Downloading, modifying, and using the data in print workflows; paid printing commissions and selling physical prints or generated models; free redistribution with author, source, and license notices preserved.
- **Restricted:** Selling or reselling the dataset files or modified datasets, charging download fees, or placing the data in paid resource libraries, memberships, or paid APIs.
- **Existing licenses:** Historical entries under licenses such as CC BY 4.0 keep their original terms. Trademarks and brand logos belong to their respective owners.

See [DATA-LICENSE.md](DATA-LICENSE.md) for the full Chinese and English terms.
