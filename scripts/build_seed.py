from __future__ import annotations

import argparse

from material_bundle import build_seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", default="packages")
    parser.add_argument("--channel", default="official")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = build_seed(args.packages, args.channel, args.output)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
