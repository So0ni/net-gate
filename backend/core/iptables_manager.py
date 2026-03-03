import subprocess
import logging
from typing import Sequence

from config import settings

logger = logging.getLogger(__name__)


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


def _validate_mark_id(mark_id: int):
    if mark_id <= 0:
        raise ValueError("mark_id must be > 0")


def add_mark_to_class(mark_id: int):
    """Route packets with nfmark → tc class 1:<mark_id> via iptables CLASSIFY."""
    _validate_mark_id(mark_id)
    iface = settings.interface
    _run(
        [
            "iptables",
            "-t",
            "mangle",
            "-A",
            "POSTROUTING",
            "-o",
            iface,
            "-m",
            "mark",
            "--mark",
            str(mark_id),
            "-j",
            "CLASSIFY",
            "--set-class",
            f"1:{mark_id}",
        ]
    )
    logger.info("iptables: mark %d → class 1:%d", mark_id, mark_id)


def remove_mark_to_class(mark_id: int):
    """Remove iptables CLASSIFY rule for the given mark."""
    _validate_mark_id(mark_id)
    iface = settings.interface
    _run(
        [
            "iptables",
            "-t",
            "mangle",
            "-D",
            "POSTROUTING",
            "-o",
            iface,
            "-m",
            "mark",
            "--mark",
            str(mark_id),
            "-j",
            "CLASSIFY",
            "--set-class",
            f"1:{mark_id}",
        ],
        ignore_errors=True,
    )
    logger.info("iptables: removed mark %d rule", mark_id)
