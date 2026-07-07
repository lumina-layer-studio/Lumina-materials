from __future__ import annotations

import argparse
from pathlib import Path

from lut_bundle import LUT_FILE_EXTENSIONS, build_lut_package_from_source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="luts-src")
    parser.add_argument("--packages", default="lut-packages")
    args = parser.parse_args()
    source_root = Path(args.source)
    output_root = Path(args.packages)
    built = []
    for channel_dir in sorted(path for path in source_root.iterdir() if path.is_dir()):
        channel = channel_dir.name
        for source_file in sorted(path for path in channel_dir.rglob("*") if path.is_file()):
            if source_file.suffix.lower() not in LUT_FILE_EXTENSIONS:
                continue
            built.append(
                build_lut_package_from_source(
                    source_file,
                    output_root,
                    channel,
                    source_root=source_root,
                )
            )
    print(f"built {len(built)} LUT packages")


if __name__ == "__main__":
    main()
