from __future__ import annotations

import argparse

from lut_bundle import build_lut_seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", default="lut-packages")
    parser.add_argument("--channel", default="official")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = build_lut_seed(args.packages, args.channel, args.output)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
