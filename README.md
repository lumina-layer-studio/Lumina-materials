# Lumina Materials

Independent content repository for Lumina material sources, package artifacts,
and seed artifacts.

## Layout

```text
materials-src/
  official/<brand>/<material>/material.json
  official/<brand>/<material>/stage_A_parameters.json
packages/
  official/<material_id>/<revision_id>-<sha12>.zip
seed/
  lumina-materials-seed.zip
luts-src/
  community/<brand>/<path>/<lut>.json
  community/<brand>/<path>/<lut>.npy
lut-packages/
  community/<lut_id>/<revision_id>-<sha12>.zip
scripts/
  build_packages.py
  validate_packages.py
  build_seed.py
  build_lut_packages.py
  validate_lut_packages.py
  build_lut_seed.py
```

## Commands

```powershell
python scripts/build_packages.py --source materials-src --packages packages
python scripts/validate_packages.py --packages packages
python scripts/build_seed.py --channel official --packages packages --output seed/lumina-materials-seed.zip
python scripts/validate_packages.py --archive seed/lumina-materials-seed.zip

python scripts/build_lut_packages.py --source luts-src --packages lut-packages
python scripts/validate_lut_packages.py --packages lut-packages
```

`seed/lumina-materials-seed.zip` must contain official material packages only.
LUT seed artifacts are official-only; the current LUT package set is community
content, so this repository does not publish a LUT seed archive.

LUT packages are one-LUT-per-archive registry packages. Their registry
`local_path` is relative to `luts-src/<channel>/` and does not include the
channel prefix, so Lumina Studio can install the cloud copy under
`lut-preset/Cloud/<local_path>` while still matching locally installed LUTs by
`local_path` and `content_hash`.
