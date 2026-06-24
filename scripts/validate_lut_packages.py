from __future__ import annotations

import argparse

from lut_bundle import (
    validate_lut_archive,
    validate_lut_package_collection,
    validate_lut_seed_archive,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", default="")
    parser.add_argument("--archive", default="")
    parser.add_argument("--seed", default="")
    args = parser.parse_args()
    selected = sum(bool(value) for value in (args.packages, args.archive, args.seed))
    if selected != 1:
        raise SystemExit("Use exactly one of --packages, --archive, or --seed")
    if args.archive:
        result = validate_lut_archive(args.archive)
        print(f"ok LUT archive lut_id={result['lut']['lut_id']}")
        return
    if args.seed:
        result = validate_lut_seed_archive(args.seed)
        print(f"ok LUT seed packages={len(result['packages'])}")
        return
    entries = validate_lut_package_collection(args.packages)
    print(f"ok LUT packages={len(entries)}")


if __name__ == "__main__":
    main()
