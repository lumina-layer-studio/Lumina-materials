"""Build and validate Lumina LUT package archives."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable

MANIFEST_NAME = "lumina_lut_bundle.json"
SEED_MANIFEST_NAME = "lumina_lut_seed.json"
LUT_REQUIRED_ROLE = "lut_file"
LUT_FILE_EXTENSIONS = frozenset({".json", ".npy", ".npz", ".msgpack"})
LOCAL_ONLY_SEGMENTS = frozenset({"_solver_cache"})
LOCAL_ONLY_FILENAMES = frozenset({"usage_stats.json"})
PACKAGE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


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
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    filename = PurePosixPath(path).name.casefold()
    return (
        any(part in LOCAL_ONLY_SEGMENTS for part in parts)
        or filename in LOCAL_ONLY_FILENAMES
    )


def _normalize_package_id(value: Any, field_name: str) -> str:
    package_id = str(value or "").strip()
    if not PACKAGE_ID_PATTERN.fullmatch(package_id):
        raise ValueError(f"{field_name} is invalid")
    return package_id


def _normalize_content_hash(value: Any) -> str:
    content_hash = str(value or "").strip().lower()
    if content_hash.startswith("sha256:"):
        content_hash = content_hash.split(":", 1)[1]
    if not re.fullmatch(r"[0-9a-f]{64}", content_hash):
        raise ValueError("content_hash must be sha256")
    return f"sha256:{content_hash}"


def _lut_content_hash_from_file_record(file_record: dict[str, Any]) -> str:
    logical_path = PurePosixPath(safe_zip_path(str(file_record.get("path") or ""))).name
    digest = sha256_bytes(f"{logical_path}:{file_record['sha256']}".encode("utf-8"))
    return f"sha256:{digest}"


def _writestr(
    archive: zipfile.ZipFile,
    name: str,
    payload: bytes | str,
    *,
    compression: int = zipfile.ZIP_DEFLATED,
) -> None:
    info = zipfile.ZipInfo(safe_zip_path(name), ZIP_TIMESTAMP)
    info.compress_type = compression
    info.external_attr = 0o100644 << 16
    archive.writestr(info, payload)


def _read_lut_manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    try:
        manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
    except KeyError as exc:
        raise ValueError("LUT manifest is missing") from exc
    except UnicodeDecodeError as exc:
        raise ValueError("LUT manifest must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("LUT manifest must be valid JSON") from exc
    if not isinstance(manifest, dict):
        raise ValueError("LUT manifest must be an object")
    if manifest.get("kind") not in (None, "lumina_lut_bundle"):
        raise ValueError("LUT manifest kind is invalid")
    if "luts" in manifest or "packages" in manifest:
        raw_luts = manifest.get("luts", manifest.get("packages"))
        if not isinstance(raw_luts, list) or len(raw_luts) != 1:
            raise ValueError("LUT manifest must contain exactly one LUT")
        raw_lut = raw_luts[0]
        if not isinstance(raw_lut, dict):
            raise ValueError("LUT manifest entry must be an object")
        return raw_lut
    return manifest


def validate_lut_archive(archive_path: str | Path) -> dict[str, Any]:
    path = Path(archive_path)
    package_sha256 = sha256_file(path)
    package_bytes = path.stat().st_size
    with zipfile.ZipFile(path, "r") as archive:
        names: set[str] = set()
        folded_names: set[str] = set()
        payload_names: set[str] = set()
        for info in archive.infolist():
            safe_name = safe_zip_path(info.filename)
            lowered = safe_name.casefold()
            if lowered in folded_names:
                raise ValueError(f"duplicate ZIP path: {safe_name}")
            folded_names.add(lowered)
            names.add(safe_name)
            if is_local_only(safe_name):
                raise ValueError(f"local-only file cannot be packaged: {safe_name}")
            if safe_name != MANIFEST_NAME:
                payload_names.add(lowered)

        raw_lut = _read_lut_manifest(archive)
        for field_name in (
            "lut_id",
            "revision_id",
            "content_hash",
            "display",
            "compatibility",
            "files",
        ):
            if field_name not in raw_lut:
                raise ValueError(f"LUT manifest field is missing: {field_name}")

        lut_id = _normalize_package_id(raw_lut.get("lut_id"), "lut_id")
        revision_id = _normalize_package_id(raw_lut.get("revision_id"), "revision_id")
        display = raw_lut.get("display")
        compatibility = raw_lut.get("compatibility")
        files = raw_lut.get("files")
        if not isinstance(display, dict):
            raise ValueError("display must be an object")
        if not isinstance(compatibility, dict):
            raise ValueError("compatibility must be an object")
        if not isinstance(files, list):
            raise ValueError("LUT files must be a list")

        normalized_files: list[dict[str, Any]] = []
        lut_file_count = 0
        for record in files:
            if not isinstance(record, dict):
                raise ValueError("file record must be an object")
            file_path = safe_zip_path(str(record.get("path") or ""))
            if file_path.casefold() not in folded_names:
                raise ValueError(f"file record is missing from ZIP: {file_path}")
            if file_path not in names:
                raise ValueError(f"file record path case mismatch: {file_path}")
            if PurePosixPath(file_path).suffix.casefold() not in LUT_FILE_EXTENSIONS:
                raise ValueError(f"LUT file extension is not supported: {file_path}")
            role = str(record.get("role") or "")
            if role == LUT_REQUIRED_ROLE:
                lut_file_count += 1
            payload = archive.read(file_path)
            if sha256_bytes(payload) != str(record.get("sha256") or "").lower():
                raise ValueError(f"hash mismatch: {file_path}")
            if len(payload) != int(record.get("bytes") or -1):
                raise ValueError(f"byte count mismatch: {file_path}")
            if record.get("content_hash") is not None:
                file_content_hash = _normalize_content_hash(record.get("content_hash"))
                if file_content_hash != f"sha256:{sha256_bytes(payload)}":
                    raise ValueError(f"file content_hash mismatch: {file_path}")
            normalized_record = dict(record)
            normalized_record["path"] = file_path
            normalized_files.append(normalized_record)

        if lut_file_count != 1:
            raise ValueError("manifest files must contain exactly one lut_file")
        declared_names = {str(record.get("path") or "").casefold() for record in normalized_files}
        undeclared_names = sorted(payload_names - declared_names)
        if undeclared_names:
            raise ValueError(f"ZIP file is not declared in LUT manifest: {undeclared_names[0]}")

        lut_file = next(
            record for record in normalized_files if record.get("role") == LUT_REQUIRED_ROLE
        )
        expected_content_hash = _normalize_content_hash(raw_lut.get("content_hash"))
        actual_content_hash = _lut_content_hash_from_file_record(lut_file)
        if expected_content_hash != actual_content_hash:
            raise ValueError("content_hash mismatch")

        local_path = safe_zip_path(str(raw_lut.get("local_path") or lut_file["path"]))
        if PurePosixPath(local_path).suffix.casefold() not in LUT_FILE_EXTENSIONS:
            raise ValueError("local_path extension is not supported")
        normalized_lut = dict(raw_lut)
        normalized_lut["lut_id"] = lut_id
        normalized_lut["revision_id"] = revision_id
        normalized_lut["content_hash"] = expected_content_hash
        normalized_lut["display"] = display
        normalized_lut["compatibility"] = compatibility
        normalized_lut["files"] = normalized_files
        normalized_lut["local_path"] = local_path

    return {
        "package_sha256": package_sha256,
        "package_bytes": package_bytes,
        "lut": normalized_lut,
    }


def iter_lut_archives(packages_dir: str | Path) -> Iterable[Path]:
    root = Path(packages_dir)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.zip") if path.is_file())


def validate_lut_package_collection(packages_dir: str | Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for archive_path in iter_lut_archives(packages_dir):
        result = validate_lut_archive(archive_path)
        lut = result["lut"]
        key = (lut["lut_id"], lut["revision_id"])
        if key in seen:
            raise ValueError("duplicate lut_id + revision_id")
        seen.add(key)
        entries.append(
            {
                "archive": str(archive_path),
                "package_sha256": result["package_sha256"],
                "package_bytes": result["package_bytes"],
                **lut,
            }
        )
    return entries


def _source_local_path(source_file: Path, source_root: Path, channel: str) -> str:
    relative = source_file.relative_to(source_root / channel)
    return safe_zip_path(relative.as_posix())


def _stable_lut_id(local_path: str) -> str:
    return f"lut_{sha256_bytes(local_path.casefold().encode('utf-8'))[:26]}"


def _revision_id(local_path: str, content_hash: str, display: dict[str, Any]) -> str:
    revision_payload = json.dumps(
        {
            "content_hash": content_hash,
            "display": display,
            "local_path": local_path,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"rev_{sha256_bytes(revision_payload)[:26]}"


def _infer_color_mode(local_path: str) -> str:
    lowered = local_path.casefold()
    if "8色" in local_path or "8color" in lowered:
        return "8-color"
    if "6色" in local_path or "cmywgk" in lowered or "rybwgk" in lowered:
        return "6-color"
    if "5色" in local_path or "5color" in lowered:
        return "5-color"
    if (
        "4色" in local_path
        or "cmyw" in lowered
        or "cmyk" in lowered
        or "rybw" in lowered
    ):
        return "4-color"
    if "2色" in local_path or "bw" in lowered:
        return "2-color"
    return "unknown"


def _infer_display(local_path: str) -> dict[str, Any]:
    path = PurePosixPath(local_path)
    manufacturer = path.parts[0] if len(path.parts) > 1 else "Lumina"
    stem = path.stem
    if stem == "lumina_lut" and len(path.parts) > 1:
        stem = " / ".join(path.parts[:-1])
    return {
        "name": stem,
        "manufacturer": manufacturer,
    }


def _infer_compatibility(local_path: str, source_file: Path) -> dict[str, Any]:
    return {
        "color_mode": _infer_color_mode(local_path),
        "file_format": source_file.suffix.lower().lstrip("."),
        "source": "lut-preset",
        "supports_multi_select": True,
    }


def build_lut_package_from_source(
    source_file: Path,
    output_root: Path,
    channel: str,
    *,
    source_root: Path,
) -> Path:
    if source_file.suffix.lower() not in LUT_FILE_EXTENSIONS:
        raise ValueError(f"unsupported LUT extension: {source_file}")
    local_path = _source_local_path(source_file, source_root, channel)
    payload = source_file.read_bytes()
    lut_sha = sha256_bytes(payload)
    zip_lut_path = f"luts/{local_path}"
    file_record = {
        "path": zip_lut_path,
        "role": LUT_REQUIRED_ROLE,
        "sha256": lut_sha,
        "bytes": len(payload),
        "content_hash": f"sha256:{lut_sha}",
        "required": True,
    }
    content_hash = _lut_content_hash_from_file_record(file_record)
    display = _infer_display(local_path)
    manifest = {
        "kind": "lumina_lut_bundle",
        "schema_version": "1.0",
        "lut_id": _stable_lut_id(local_path),
        "revision_id": _revision_id(local_path, content_hash, display),
        "content_hash": content_hash,
        "channel": channel,
        "visibility": channel,
        "local_path": local_path,
        "display": display,
        "compatibility": _infer_compatibility(local_path, source_file),
        "files": [file_record],
    }
    output_path = (
        output_root
        / channel
        / manifest["lut_id"]
        / f"{manifest['revision_id']}-{content_hash.split(':', 1)[1][:12]}.zip"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w") as archive:
        _writestr(archive, zip_lut_path, payload)
        _writestr(
            archive,
            MANIFEST_NAME,
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        )
    validate_lut_archive(output_path)
    return output_path


def build_lut_seed(packages_dir: str | Path, channel: str, output_path: str | Path) -> Path:
    if channel != "official":
        raise ValueError("LUT distribution seed must be official-only")
    archives = list(iter_lut_archives(Path(packages_dir) / channel))
    if not archives:
        raise ValueError("no official LUT packages found")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    package_records: list[dict[str, Any]] = []
    written_paths: set[str] = set()
    seen_revisions: set[tuple[str, str]] = set()
    with zipfile.ZipFile(output, "w") as target:
        for archive_path in archives:
            result = validate_lut_archive(archive_path)
            lut = result["lut"]
            key = (lut["lut_id"], lut["revision_id"])
            if key in seen_revisions:
                raise ValueError("duplicate lut_id + revision_id")
            seen_revisions.add(key)
            if str(lut.get("channel")) != "official":
                raise ValueError("seed package is not official")
            package_path = safe_zip_path(
                f"lut-packages/{channel}/{lut['lut_id']}/{archive_path.name}"
            )
            if package_path in written_paths:
                raise ValueError(f"duplicate seed file path: {package_path}")
            written_paths.add(package_path)
            package_payload = archive_path.read_bytes()
            _writestr(target, package_path, package_payload)
            package_records.append(
                {
                    "path": package_path,
                    "lut_id": lut["lut_id"],
                    "revision_id": lut["revision_id"],
                    "content_hash": lut["content_hash"],
                    "channel": lut["channel"],
                    "local_path": lut["local_path"],
                    "package_sha256": result["package_sha256"],
                    "package_bytes": result["package_bytes"],
                }
            )
        _writestr(
            target,
            SEED_MANIFEST_NAME,
            json.dumps(
                {
                    "kind": "lumina_lut_seed",
                    "schema_version": "1.0",
                    "packages": package_records,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
        )
    validate_lut_seed_archive(output)
    return output


def validate_lut_seed_archive(archive_path: str | Path) -> dict[str, Any]:
    path = Path(archive_path)
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
            manifest = json.loads(archive.read(SEED_MANIFEST_NAME).decode("utf-8"))
        except KeyError as exc:
            raise ValueError("LUT seed manifest is missing") from exc
        except UnicodeDecodeError as exc:
            raise ValueError("LUT seed manifest must be UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("LUT seed manifest must be valid JSON") from exc
        if not isinstance(manifest, dict):
            raise ValueError("LUT seed manifest must be an object")
        if manifest.get("kind") != "lumina_lut_seed":
            raise ValueError("LUT seed manifest kind is invalid")
        packages = manifest.get("packages")
        if not isinstance(packages, list) or not packages:
            raise ValueError("LUT seed packages must be a non-empty list")
        normalized_packages: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for package in packages:
                if not isinstance(package, dict):
                    raise ValueError("LUT seed package must be an object")
                package_path = safe_zip_path(str(package.get("path") or ""))
                if package_path.casefold() not in names:
                    raise ValueError(f"LUT seed package is missing: {package_path}")
                payload = archive.read(package_path)
                if sha256_bytes(payload) != str(package.get("package_sha256") or "").lower():
                    raise ValueError(f"LUT seed package hash mismatch: {package_path}")
                if len(payload) != int(package.get("package_bytes") or -1):
                    raise ValueError(f"LUT seed package byte count mismatch: {package_path}")
                temp_package = temp_root / PurePosixPath(package_path).name
                temp_package.write_bytes(payload)
                result = validate_lut_archive(temp_package)
                lut = result["lut"]
                key = (lut["lut_id"], lut["revision_id"])
                if key in seen:
                    raise ValueError("duplicate lut_id + revision_id")
                seen.add(key)
                if lut["lut_id"] != package.get("lut_id"):
                    raise ValueError("LUT seed lut_id mismatch")
                if lut["revision_id"] != package.get("revision_id"):
                    raise ValueError("LUT seed revision_id mismatch")
                if lut["content_hash"] != package.get("content_hash"):
                    raise ValueError("LUT seed content_hash mismatch")
                if str(lut.get("channel")) != "official":
                    raise ValueError("LUT seed package is not official")
                normalized_packages.append(package)
    return {
        "package_sha256": sha256_file(path),
        "package_bytes": path.stat().st_size,
        "packages": normalized_packages,
    }
