from __future__ import annotations

import argparse

from material_bundle import validate_archive, validate_package_collection


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", default="")
    parser.add_argument("--archive", default="")
    args = parser.parse_args()
    if bool(args.packages) == bool(args.archive):
        raise SystemExit("Use exactly one of --packages or --archive")
    if args.archive:
        result = validate_archive(args.archive)
        print(f"ok archive packages={len(result['packages'])}")
        return
    entries = validate_package_collection(args.packages)
    print(f"ok packages={len(entries)}")


if __name__ == "__main__":
    main()
