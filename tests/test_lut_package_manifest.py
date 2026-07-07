from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lut_bundle import (
    build_lut_package_from_source,
    build_lut_seed,
    validate_lut_archive,
    validate_lut_package_collection,
    validate_lut_seed_archive,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _logical_content_hash(lut_path: str, lut_payload: bytes) -> str:
    lut_hash = _sha256(lut_payload)
    logical_name = Path(lut_path).name
    return _sha256(f"{logical_name}:{lut_hash}".encode("utf-8"))


def _write_lut_package(
    zip_path: Path,
    *,
    lut_id: str = "lut_test",
    revision_id: str = "rev_test",
    channel: str = "official",
    lut_path: str = "luts/BrandA/test.json",
    local_path: str = "BrandA/test.json",
    content_hash_override: str | None = None,
    file_content_hash_override: str | None = None,
    extra_file: str | None = None,
) -> None:
    lut_payload = json.dumps(
        {
            "entries": [
                {
                    "recipe": ["White", "White", "White", "White", "White"],
                    "rgb": [255, 255, 255],
                }
            ]
        },
        separators=(",", ":"),
    ).encode("utf-8")
    lut_hash = _sha256(lut_payload)
    content_hash = _logical_content_hash(lut_path, lut_payload)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(lut_path, lut_payload)
        if extra_file:
            archive.writestr(extra_file, b"extra")
        archive.writestr(
            "lumina_lut_bundle.json",
            json.dumps(
                {
                    "kind": "lumina_lut_bundle",
                    "schema_version": "1.0",
                    "lut_id": lut_id,
                    "revision_id": revision_id,
                    "content_hash": content_hash_override or f"sha256:{content_hash}",
                    "channel": channel,
                    "visibility": channel,
                    "local_path": local_path,
                    "display": {"name": "Test LUT", "manufacturer": "BrandA"},
                    "compatibility": {"color_mode": "4-color"},
                    "files": [
                        {
                            "path": lut_path,
                            "role": "lut_file",
                            "sha256": lut_hash,
                            "bytes": len(lut_payload),
                            "content_hash": file_content_hash_override
                            or f"sha256:{lut_hash}",
                            "required": True,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )


def test_validate_lut_archive_accepts_registry_package(tmp_path: Path) -> None:
    archive_path = tmp_path / "lut.zip"
    _write_lut_package(archive_path)

    result = validate_lut_archive(archive_path)

    assert result["lut"]["lut_id"] == "lut_test"
    assert result["lut"]["local_path"] == "BrandA/test.json"


def test_validate_lut_archive_rejects_local_only_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad-local.zip"
    _write_lut_package(archive_path, extra_file="luts/BrandA/_Solver_Cache/cache.bin")

    with pytest.raises(ValueError, match="local-only"):
        validate_lut_archive(archive_path)


def test_validate_lut_archive_rejects_content_hash_mismatch(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad-content-hash.zip"
    _write_lut_package(archive_path, content_hash_override="sha256:" + "0" * 64)

    with pytest.raises(ValueError, match="content_hash mismatch"):
        validate_lut_archive(archive_path)


def test_validate_lut_archive_rejects_file_content_hash_mismatch(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad-file-content-hash.zip"
    _write_lut_package(archive_path, file_content_hash_override="sha256:" + "0" * 64)

    with pytest.raises(ValueError, match="file content_hash mismatch"):
        validate_lut_archive(archive_path)


def test_validate_lut_archive_rejects_undeclared_payload_file(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad-extra.zip"
    _write_lut_package(archive_path, extra_file="luts/BrandA/extra.json")

    with pytest.raises(ValueError, match="not declared"):
        validate_lut_archive(archive_path)


def test_validate_lut_package_collection_rejects_duplicate_revisions(tmp_path: Path) -> None:
    packages_dir = tmp_path / "lut-packages"
    _write_lut_package(packages_dir / "official" / "a.zip")
    _write_lut_package(packages_dir / "official" / "b.zip")

    with pytest.raises(ValueError, match="duplicate lut_id"):
        validate_lut_package_collection(packages_dir)


def test_build_lut_package_from_source_preserves_local_path(tmp_path: Path) -> None:
    source_root = tmp_path / "luts-src"
    source_file = source_root / "official" / "BrandA" / "PLA" / "test.npy"
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(b"lut bytes")

    package_path = build_lut_package_from_source(
        source_file,
        tmp_path / "lut-packages",
        "official",
        source_root=source_root,
    )
    result = validate_lut_archive(package_path)

    assert result["lut"]["local_path"] == "BrandA/PLA/test.npy"
    assert result["lut"]["display"]["manufacturer"] == "BrandA"


def test_build_lut_package_from_source_reads_json_color_mode_metadata(tmp_path: Path) -> None:
    source_root = tmp_path / "luts-src"
    source_file = source_root / "community" / "BrandA" / "lumina_lut.json"
    source_file.parent.mkdir(parents=True)
    source_file.write_text(
        json.dumps(
            {
                "color_mode": "8-Color Max",
                "palette": {
                    f"Slot {index}": {"hex_color": "#ffffff"}
                    for index in range(1, 9)
                },
                "entries": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    package_path = build_lut_package_from_source(
        source_file,
        tmp_path / "lut-packages",
        "community",
        source_root=source_root,
    )
    result = validate_lut_archive(package_path)

    assert result["lut"]["compatibility"]["color_mode"] == "8-color"


def test_build_lut_seed_is_official_only_and_valid(tmp_path: Path) -> None:
    packages_dir = tmp_path / "lut-packages"
    _write_lut_package(packages_dir / "official" / "lut_test" / "rev_test.zip")
    output_path = tmp_path / "lut-seed" / "lumina-luts-seed.zip"

    seed_path = build_lut_seed(packages_dir, "official", output_path)
    result = validate_lut_seed_archive(seed_path)

    assert result["packages"][0]["channel"] == "official"


def test_build_lut_seed_rejects_non_official_channel(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="official-only"):
        build_lut_seed(tmp_path / "lut-packages", "community", tmp_path / "seed.zip")
