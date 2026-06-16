"""Build and validate Lumina material bundle archives."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable

MANIFEST_NAME = "lumina_material_bundle.json"
REQUIRED_ROLES = frozenset({"material_archive", "stage_a_parameters"})
LOCAL_ONLY_SEGMENTS = frozenset({"_solver_cache"})
LOCAL_ONLY_FILENAMES = frozenset({"usage_stats.json"})


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_zip_path(value: str) -> str:
    normalized = str(value or "").replace("\\", "/").strip()
    if not normalized or normalized.startswith("/") or PureWindowsPath(normalized).drive:
        raise ValueError(f"unsafe ZIP path: {value}")
    path = PurePosixPath(normalized)
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe ZIP path: {value}")
    return path.as_posix()


def is_local_only(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        any(part in LOCAL_ONLY_SEGMENTS for part in parts)
        or PurePosixPath(path).name in LOCAL_ONLY_FILENAMES
    )


def _normalize_content_hash(value: Any) -> str:
    content_hash = str(value or "").strip().lower()
    if content_hash.startswith("sha256:"):
        content_hash = content_hash.split(":", 1)[1]
    if not re.fullmatch(r"[0-9a-f]{64}", content_hash):
        raise ValueError("content_hash must be sha256")
    return f"sha256:{content_hash}"


def _content_hash_from_file_records(file_records: list[dict[str, Any]]) -> str:
    required_records = [
        record
        for record in file_records
        if str(record.get("role") or "") in REQUIRED_ROLES
    ]
    logical_lines: list[str] = []
    for record in sorted(required_records, key=lambda item: str(item.get("role") or "")):
        role = str(record.get("role") or "")
        logical_path = (
            "material.json"
            if role == "material_archive"
            else PurePosixPath(str(record.get("path") or "")).name
        )
        logical_lines.append(f"{logical_path}:{record['sha256']}")
    return f"sha256:{sha256_bytes(chr(10).join(logical_lines).encode('utf-8'))}"


def validate_archive(archive_path: str | Path) -> dict[str, Any]:
    path = Path(archive_path)
    package_sha256 = sha256_file(path)
    package_bytes = path.stat().st_size
    with zipfile.ZipFile(path, "r") as archive:
        names: set[str] = set()
        for info in archive.infolist():
            safe_name = safe_zip_path(info.filename)
            lowered = safe_name.casefold()
            if lowered in names:
                raise ValueError(f"duplicate ZIP path: {safe_name}")
            names.add(lowered)
            if is_local_only(safe_name):
                raise ValueError(f"local-only file cannot be packaged: {safe_name}")
        try:
            manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
        except KeyError as exc:
            raise ValueError("manifest is missing") from exc
        except UnicodeDecodeError as exc:
            raise ValueError("manifest must be UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("manifest must be valid JSON") from exc
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
        if manifest.get("kind") != "lumina_material_bundle":
            raise ValueError("manifest kind is invalid")
        if str(manifest.get("schema_version") or "") != "2.0":
            raise ValueError("manifest schema_version must be 2.0")
        packages = manifest.get("packages")
        if not isinstance(packages, list) or not packages:
            raise ValueError("manifest packages must be a non-empty list")
        seen: set[tuple[str, str]] = set()
        normalized_packages: list[dict[str, Any]] = []
        for package in packages:
            if not isinstance(package, dict):
                raise ValueError("package must be an object")
            material_id = str(package.get("material_id") or "").strip()
            revision_id = str(package.get("revision_id") or "").strip()
            if not material_id or not revision_id:
                raise ValueError("package identity is incomplete")
            key = (material_id, revision_id)
            if key in seen:
                raise ValueError("duplicate material_id + revision_id")
            seen.add(key)
            files = package.get("files")
            if not isinstance(files, list) or not files:
                raise ValueError("package files must be non-empty")
            role_counts = {role: 0 for role in REQUIRED_ROLES}
            for record in files:
                if not isinstance(record, dict):
                    raise ValueError("file record must be an object")
                file_path = safe_zip_path(str(record.get("path") or ""))
                if file_path.casefold() not in names:
                    raise ValueError(f"file record is missing from ZIP: {file_path}")
                role = str(record.get("role") or "")
                if role in role_counts and bool(record.get("required", True)):
                    role_counts[role] += 1
                payload = archive.read(file_path)
                if sha256_bytes(payload) != str(record.get("sha256") or "").lower():
                    raise ValueError(f"hash mismatch: {file_path}")
                if len(payload) != int(record.get("bytes") or -1):
                    raise ValueError(f"byte count mismatch: {file_path}")
            for role, count in role_counts.items():
                if count != 1:
                    raise ValueError(
                        f"{'missing' if count < 1 else 'duplicate'} required role: {role}"
                    )
            expected_content_hash = _normalize_content_hash(package.get("content_hash"))
            actual_content_hash = _content_hash_from_file_records(files)
            if expected_content_hash != actual_content_hash:
                raise ValueError("content_hash mismatch")
            normalized = dict(package)
            normalized["material_id"] = material_id
            normalized["revision_id"] = revision_id
            normalized["content_hash"] = expected_content_hash
            normalized["local_directory"] = safe_zip_path(str(package.get("local_directory") or ""))
            normalized_packages.append(normalized)
    return {
        "package_sha256": package_sha256,
        "package_bytes": package_bytes,
        "packages": normalized_packages,
    }


def iter_archives(packages_dir: str | Path) -> Iterable[Path]:
    root = Path(packages_dir)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.zip") if path.is_file())


def validate_package_collection(packages_dir: str | Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for archive_path in iter_archives(packages_dir):
        result = validate_archive(archive_path)
        for package in result["packages"]:
            key = (package["material_id"], package["revision_id"])
            if key in seen:
                raise ValueError("duplicate material_id + revision_id")
            seen.add(key)
            entries.append({"archive": str(archive_path), **package})
    return entries


def build_package_from_source(source_dir: Path, output_root: Path, channel: str) -> Path:
    material_path = source_dir / "material.json"
    stage_path = source_dir / "stage_A_parameters.json"
    material_payload = material_path.read_bytes()
    stage_payload = stage_path.read_bytes()
    json.loads(material_payload.decode("utf-8"))
    json.loads(stage_payload.decode("utf-8"))
    material_hash = sha256_bytes(material_payload)
    stage_hash = sha256_bytes(stage_payload)
    content_hash = sha256_bytes(
        f"material.json:{material_hash}\nstage_A_parameters.json:{stage_hash}".encode(
            "utf-8"
        )
    )
    local_directory = "/".join(source_dir.relative_to(source_dir.parents[2]).parts[1:])
    material_id = f"mat_{sha256_bytes(local_directory.encode('utf-8'))[:26]}"
    revision_id = f"rev_{content_hash[:26]}"
    material_zip_path = f"materials/{local_directory}/material.json"
    stage_zip_path = f"materials/{local_directory}/stage_A_parameters.json"
    manifest = {
        "kind": "lumina_material_bundle",
        "schema_version": "2.0",
        "packages": [
            {
                "material_id": material_id,
                "revision_id": revision_id,
                "content_hash": f"sha256:{content_hash}",
                "channel": channel,
                "visibility": channel,
                "local_directory": local_directory,
                "display": {},
                "files": [
                    {
                        "path": material_zip_path,
                        "role": "material_archive",
                        "sha256": material_hash,
                        "bytes": len(material_payload),
                        "required": True,
                    },
                    {
                        "path": stage_zip_path,
                        "role": "stage_a_parameters",
                        "sha256": stage_hash,
                        "bytes": len(stage_payload),
                        "required": True,
                    },
                ],
            }
        ],
    }
    output_path = output_root / channel / material_id / f"{revision_id}-{content_hash[:12]}.zip"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(material_zip_path, material_payload)
        archive.writestr(stage_zip_path, stage_payload)
        archive.writestr(MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
    validate_archive(output_path)
    return output_path


def build_seed(packages_dir: str | Path, channel: str, output_path: str | Path) -> Path:
    if channel != "official":
        raise ValueError("distribution seed must be official-only")
    archives = [
        path for path in iter_archives(Path(packages_dir) / channel)
    ]
    if not archives:
        raise ValueError("no official packages found")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_packages: list[dict[str, Any]] = []
    written_paths: set[str] = set()
    seen_revisions: set[tuple[str, str]] = set()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for archive_path in archives:
            result = validate_archive(archive_path)
            for package in result["packages"]:
                key = (package["material_id"], package["revision_id"])
                if key in seen_revisions:
                    raise ValueError("duplicate material_id + revision_id")
                seen_revisions.add(key)
                if str(package.get("channel")) != "official":
                    raise ValueError("seed package is not official")
                with zipfile.ZipFile(archive_path, "r") as source:
                    for record in package["files"]:
                        file_path = safe_zip_path(str(record["path"]))
                        if file_path in written_paths:
                            raise ValueError(f"duplicate seed file path: {file_path}")
                        written_paths.add(file_path)
                        target.writestr(file_path, source.read(file_path))
                manifest_packages.append(package)
        target.writestr(
            MANIFEST_NAME,
            json.dumps(
                {
                    "kind": "lumina_material_bundle",
                    "schema_version": "2.0",
                    "packages": manifest_packages,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    validate_archive(output)
    return output
