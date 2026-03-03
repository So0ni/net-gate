import subprocess
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

# Bandwidth headroom: HTB rate uses bandwidth_kbps, ceil allows bursting
_DEFAULT_CEIL_KBPS = 1_000_000  # 1 Gbit fallback


def _run(cmd: str):
    logger.debug("Running: %s", cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Command failed: %s\nstderr: %s", cmd, result.stderr)
    return result


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
    iface = settings.interface
    class_id = f"1:{mark_id}"
    handle = f"{mark_id}:"

    # Remove existing class+qdisc if any
    remove_profile(mark_id)

    # Bandwidth: 0 means unlimited → use ceiling
    rate = f"{bandwidth_kbps}kbit" if bandwidth_kbps > 0 else f"{_DEFAULT_CEIL_KBPS}kbit"

    # HTB class
    _run(
        f"tc class add dev {iface} parent 1: classid {class_id} "
        f"htb rate {rate} ceil {_DEFAULT_CEIL_KBPS}kbit"
    )

    # Build netem args
    netem_args = []
    if latency_ms > 0:
        netem_args.append(f"delay {latency_ms}ms {jitter_ms}ms")
    if loss_percent >= 100:
        netem_args.append("loss 100%")
    elif loss_percent > 0:
        netem_args.append(f"loss {loss_percent}%")

    netem_str = " ".join(netem_args) if netem_args else ""
    _run(
        f"tc qdisc add dev {iface} parent {class_id} handle {handle} netem {netem_str}"
    )

    logger.info(
        "tc: applied profile to mark %d (latency=%dms jitter=%dms loss=%.1f%% bw=%s)",
        mark_id, latency_ms, jitter_ms, loss_percent, rate,
    )


def remove_profile(mark_id: int):
    """Remove HTB class and netem qdisc for a device (ignore errors if not present)."""
    iface = settings.interface
    class_id = f"1:{mark_id}"
    handle = f"{mark_id}:"
    _run(f"tc qdisc del dev {iface} parent {class_id} handle {handle} 2>/dev/null || true")
    _run(f"tc class del dev {iface} classid {class_id} 2>/dev/null || true")
    logger.info("tc: removed profile for mark %d", mark_id)
