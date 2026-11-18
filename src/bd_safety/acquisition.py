"""Pinned original-source acquisition with byte-preserving extraction."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile

from .config import (
    DOI,
    DOWNLOAD,
    EXTERNAL,
    FILE_ID,
    INVENTORY,
    MEMBER,
    PUBLISHED_SHA256,
    RAW,
    REPORTS,
    SOURCE,
    WORKBOOK,
)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(value, indent=2, allow_nan=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def acquire(archive=None):
    for directory in [RAW, EXTERNAL, REPORTS]:
        directory.mkdir(parents=True, exist_ok=True)
    destination = EXTERNAL / "Accident_Dataset final.zip"
    if archive is None and not destination.exists():
        with tempfile.NamedTemporaryFile(
            dir=EXTERNAL, suffix=".part", delete=False
        ) as temp:
            temporary = Path(temp.name)
        try:
            request = urllib.request.Request(
                DOWNLOAD,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; DataAnalystPortfolio/1.0)",
                    "Accept": "application/zip,application/octet-stream,*/*",
                },
            )
            with (
                urllib.request.urlopen(request, timeout=90) as response,
                temporary.open("wb") as out,
            ):
                shutil.copyfileobj(response, out)
            if digest(temporary) != PUBLISHED_SHA256:
                raise ValueError(
                    "Download differs from the publisher's pinned v2 checksum; do not substitute another release"
                )
            temporary.replace(destination)
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Original Mendeley download failed: {exc}. Download the listed "
                f"Accident_Dataset final.zip from {SOURCE} and pass --archive."
            ) from exc
        finally:
            temporary.unlink(missing_ok=True)
    archive = Path(archive).resolve() if archive else destination.resolve()
    if digest(archive) != PUBLISHED_SHA256:
        raise ValueError(
            "Archive SHA-256 differs from Mendeley v2's published checksum"
        )
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise ValueError("Archive CRC check failed")
        files = [info for info in zipped.infolist() if not info.is_dir()]
        if (
            len(files) != 1
            or files[0].filename != MEMBER
            or files[0].file_size > 50_000_000
        ):
            raise ValueError("Unexpected source archive contents")
        payload = zipped.read(MEMBER)
        expected = hashlib.sha256(payload).hexdigest()
        if WORKBOOK.exists() and digest(WORKBOOK) != expected:
            raise ValueError("Existing raw workbook differs; refusing to overwrite")
        if not WORKBOOK.exists():
            with WORKBOOK.open("xb") as out:
                out.write(payload)
    if destination.exists() and digest(destination) != PUBLISHED_SHA256:
        raise ValueError("Existing source archive changed")
    if not destination.exists():
        with archive.open("rb") as inp, destination.open("xb") as out:
            shutil.copyfileobj(inp, out)
    path = REPORTS / "source_manifest.json"
    if path.exists():
        verify_raw()
        return json.loads(path.read_text())
    manifest = {
        "source_url": SOURCE,
        "doi": DOI,
        "dataset_version": 2,
        "authors": ["Fernaz Nur", "Arafat Sahin Afridi"],
        "license": "CC BY 4.0",
        "published_date": "2025-10-17",
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_id": FILE_ID,
        "inventory_endpoint": INVENTORY,
        "download_url": DOWNLOAD,
        "archive_sha256": PUBLISHED_SHA256,
        "workbook_sha256": expected,
        "archive_member": MEMBER,
        "workbook_bytes": len(payload),
        "publisher_claimed_records": 49566,
        "publisher_claimed_coverage": "2007–2024",
        "publisher_claimed_sources": {
            "ARI": "2007–2021",
            "BRTA": "2024",
            "DMP": "2020–2024",
            "MP Unit": "2020–2024",
            "Field forms": "Not specified",
        },
        "source_claims_verified_against_institutional_records": False,
    }
    write_json(path, manifest)
    verify_raw()
    return manifest


def verify_raw():
    path = REPORTS / "source_manifest.json"
    if not path.exists():
        raise FileNotFoundError("Run acquire first; no source manifest exists")
    manifest = json.loads(path.read_text())
    if digest(WORKBOOK) != manifest["workbook_sha256"]:
        raise ValueError("Raw workbook checksum changed")
    if digest(EXTERNAL / "Accident_Dataset final.zip") != PUBLISHED_SHA256:
        raise ValueError("Original archive checksum changed")
    return True
