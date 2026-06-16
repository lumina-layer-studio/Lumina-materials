from __future__ import annotations

import argparse
from pathlib import Path

from material_bundle import build_package_from_source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="materials-src")
    parser.add_argument("--packages", default="packages")
    args = parser.parse_args()
    source_root = Path(args.source)
    output_root = Path(args.packages)
    built = []
    for channel_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        channel = channel_dir.name
        for material_json in sorted(channel_dir.rglob("material.json")):
            material_dir = material_json.parent
            if not (material_dir / "stage_A_parameters.json").is_file():
                raise SystemExit(f"missing stage_A_parameters.json: {material_dir}")
            built.append(build_package_from_source(material_dir, output_root, channel))
    print(f"built {len(built)} packages")


if __name__ == "__main__":
    main()
