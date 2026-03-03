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


def init_gateway():
    """Enable IP forwarding and set up the root tc qdisc (HTB)."""
    _run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
    iface = settings.interface
    # Remove existing root qdisc (ignore errors if none exists)
    _run(["tc", "qdisc", "del", "dev", iface, "root"], ignore_errors=True)
    # Add HTB root qdisc
    _run(["tc", "qdisc", "add", "dev", iface, "root", "handle", "1:", "htb", "default", "9999"])
    # Default class: full speed (unthrottled for unmanaged devices)
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
            "1:9999",
            "htb",
            "rate",
            "1000mbit",
        ]
    )
    logger.info("Gateway initialized on interface %s", iface)


def teardown_gateway():
    """Remove root qdisc on shutdown."""
    iface = settings.interface
    _run(["tc", "qdisc", "del", "dev", iface, "root"], ignore_errors=True)
    logger.info("Gateway torn down on interface %s", iface)
