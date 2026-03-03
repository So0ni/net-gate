import subprocess
import logging
from typing import Sequence

from config import settings

logger = logging.getLogger(__name__)

# Bandwidth headroom: HTB rate uses bandwidth_kbps, ceil allows bursting
_DEFAULT_CEIL_KBPS = 1_000_000  # 1 Gbit fallback


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


def apply_profile(
    mark_id: int,
    latency_ms: int,
    jitter_ms: int,
    loss_percent: float,
    bandwidth_kbps: int,
):
    """
    Create/replace HTB class + netem qdisc for a device.

    Class ID: 1:<mark_id>
    Leaf qdisc handle: <mark_id>:
    """
    _validate_mark_id(mark_id)
    iface = settings.interface
    class_id = f"1:{mark_id}"
    handle = f"{mark_id}:"

    # Remove existing class+qdisc if any
    remove_profile(mark_id)

    # Bandwidth: 0 means unlimited → use ceiling
    rate = f"{bandwidth_kbps}kbit" if bandwidth_kbps > 0 else f"{_DEFAULT_CEIL_KBPS}kbit"

    # HTB class
    _run(
        [
            "tc",
            "class",
            "add",
            "dev",
            iface,
            "parent",
            "1:",
            "classid",
            class_id,
            "htb",
            "rate",
            rate,
            "ceil",
            f"{_DEFAULT_CEIL_KBPS}kbit",
        ]
    )

    # Build netem args
    netem_args = []
    if latency_ms > 0:
        netem_args.append(f"delay {latency_ms}ms {jitter_ms}ms")
    if loss_percent >= 100:
        netem_args.append("loss 100%")
    elif loss_percent > 0:
        netem_args.append(f"loss {loss_percent}%")

    if netem_args:
        args = [
            "tc",
            "qdisc",
            "add",
            "dev",
            iface,
            "parent",
            class_id,
            "handle",
            handle,
            "netem",
        ]
        for entry in netem_args:
            args.extend(entry.split())
        _run(args)

    logger.info(
        "tc: applied profile to mark %d (latency=%dms jitter=%dms loss=%.1f%% bw=%s)",
        mark_id, latency_ms, jitter_ms, loss_percent, rate,
    )


def remove_profile(mark_id: int):
    """Remove HTB class and netem qdisc for a device (ignore errors if not present)."""
    _validate_mark_id(mark_id)
    iface = settings.interface
    class_id = f"1:{mark_id}"
    handle = f"{mark_id}:"
    _run(
        [
            "tc",
            "qdisc",
            "del",
            "dev",
            iface,
            "parent",
            class_id,
            "handle",
            handle,
        ],
        ignore_errors=True,
    )
    _run(["tc", "class", "del", "dev", iface, "classid", class_id], ignore_errors=True)
    logger.info("tc: removed profile for mark %d", mark_id)
