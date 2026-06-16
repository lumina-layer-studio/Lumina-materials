from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from material_bundle import build_seed, validate_archive, validate_package_collection


def _write_package(
    zip_path: Path,
    *,
    material_id: str = "mat_test",
    revision_id: str = "rev_test",
    channel: str = "official",
    content_hash_override: str | None = None,
    include_local_only: bool = False,
) -> None:
    material_payload = json.dumps(
        {"material_name": "PLA Basic", "stage_a_params_file": "stage_A_parameters.json"},
        ensure_ascii=False,
    ).encode("utf-8")
    stage_payload = json.dumps({"parameters": {}}, ensure_ascii=False).encode("utf-8")
    material_hash = hashlib.sha256(material_payload).hexdigest()
    stage_hash = hashlib.sha256(stage_payload).hexdigest()
    content_hash = hashlib.sha256(
        f"material.json:{material_hash}\nstage_A_parameters.json:{stage_hash}".encode(
            "utf-8"
        )
    ).hexdigest()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("materials/BrandA/pla-basic/material.json", material_payload)
        archive.writestr("materials/BrandA/pla-basic/stage_A_parameters.json", stage_payload)
        if include_local_only:
            archive.writestr("materials/BrandA/pla-basic/usage_stats.json", "{}")
        archive.writestr(
            "lumina_material_bundle.json",
            json.dumps(
                {
                    "kind": "lumina_material_bundle",
                    "schema_version": "2.0",
                    "packages": [
                        {
                            "material_id": material_id,
                            "revision_id": revision_id,
                            "content_hash": content_hash_override or f"sha256:{content_hash}",
                            "channel": channel,
                            "visibility": channel,
                            "local_directory": "BrandA/pla-basic",
                            "display": {},
                            "files": [
                                {
                                    "path": "materials/BrandA/pla-basic/material.json",
                                    "role": "material_archive",
                                    "sha256": material_hash,
                                    "bytes": len(material_payload),
                                    "required": True,
                                },
                                {
                                    "path": "materials/BrandA/pla-basic/stage_A_parameters.json",
                                    "role": "stage_a_parameters",
                                    "sha256": stage_hash,
                                    "bytes": len(stage_payload),
                                    "required": True,
                                },
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )


def test_validate_archive_accepts_v2_package(tmp_path: Path) -> None:
    archive_path = tmp_path / "packages" / "official" / "mat_test" / "rev_test.zip"
    _write_package(archive_path)

    result = validate_archive(archive_path)

    assert result["packages"][0]["material_id"] == "mat_test"


def test_validate_archive_rejects_local_only_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad.zip"
    _write_package(archive_path, include_local_only=True)

    with pytest.raises(ValueError, match="local-only"):
        validate_archive(archive_path)


def test_validate_archive_rejects_content_hash_mismatch(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad-content-hash.zip"
    _write_package(archive_path, content_hash_override="sha256:" + "0" * 64)

    with pytest.raises(ValueError, match="content_hash mismatch"):
        validate_archive(archive_path)


def test_validate_package_collection_rejects_duplicate_revisions(tmp_path: Path) -> None:
    packages_dir = tmp_path / "packages"
    _write_package(packages_dir / "official" / "a.zip")
    _write_package(packages_dir / "official" / "b.zip")

    with pytest.raises(ValueError, match="duplicate material_id"):
        validate_package_collection(packages_dir)


def test_validate_package_collection_rejects_cross_channel_duplicate_revisions(
    tmp_path: Path,
) -> None:
    packages_dir = tmp_path / "packages"
    _write_package(
        packages_dir / "community" / "mat_test" / "rev_test.zip",
        channel="community",
    )
    _write_package(
        packages_dir / "official" / "mat_test" / "rev_test.zip",
        channel="official",
    )

    with pytest.raises(ValueError, match="duplicate material_id"):
        validate_package_collection(packages_dir)


def test_build_seed_is_official_only_and_valid(tmp_path: Path) -> None:
    packages_dir = tmp_path / "packages"
    _write_package(packages_dir / "official" / "mat_test" / "rev_test.zip")
    output_path = tmp_path / "seed" / "lumina-materials-seed.zip"

    seed_path = build_seed(packages_dir, "official", output_path)
    result = validate_archive(seed_path)

    assert result["packages"][0]["channel"] == "official"


def test_build_seed_rejects_non_official_channel(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="official-only"):
        build_seed(tmp_path / "packages", "community", tmp_path / "seed.zip")
