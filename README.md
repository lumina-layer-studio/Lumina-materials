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
scripts/
  build_packages.py
  validate_packages.py
  build_seed.py
```

## Commands

```powershell
python scripts/build_packages.py --source materials-src --packages packages
python scripts/validate_packages.py --packages packages
python scripts/build_seed.py --channel official --packages packages --output seed/lumina-materials-seed.zip
python scripts/validate_packages.py --archive seed/lumina-materials-seed.zip
```

`seed/lumina-materials-seed.zip` must contain official material packages only.
