import subprocess
import logging
import re
from typing import Sequence

logger = logging.getLogger(__name__)
_MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")


def _run(args: Sequence[str], ignore_errors: bool = False):
    cmd = " ".join(args)
    logger.debug("Running: %s", cmd)
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.error("Command failed: %s\nstderr: %s", cmd, stderr)
        if not ignore_errors:
            raise RuntimeError(stderr or f"command failed: {cmd}")
    return result


def _normalize_mac(mac: str) -> str:
    normalized = mac.lower().strip()
    if not _MAC_RE.fullmatch(normalized):
        raise ValueError("Invalid MAC address format")
    return normalized


def _validate_mark_id(mark_id: int):
    if mark_id <= 0:
        raise ValueError("mark_id must be > 0")


def add_device_mark(mac: str, mark_id: int):
    """Mark packets from a MAC address with nfmark via ebtables."""
    mac = _normalize_mac(mac)
    _validate_mark_id(mark_id)
    _run(
        [
            "ebtables",
            "-A",
            "FORWARD",
            "--src",
            mac,
            "-j",
            "mark",
            "--mark-set",
            str(mark_id),
            "--mark-target",
            "CONTINUE",
        ]
    )
    logger.info("ebtables: added mark %d for MAC %s", mark_id, mac)


def remove_device_mark(mac: str, mark_id: int):
    """Remove MAC → nfmark rule from ebtables."""
    mac = _normalize_mac(mac)
    _validate_mark_id(mark_id)
    _run(
        [
            "ebtables",
            "-D",
            "FORWARD",
            "--src",
            mac,
            "-j",
            "mark",
            "--mark-set",
            str(mark_id),
            "--mark-target",
            "CONTINUE",
        ],
        ignore_errors=True,
    )
    logger.info("ebtables: removed mark %d for MAC %s", mark_id, mac)
