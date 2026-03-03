import subprocess
import logging

from config import settings

logger = logging.getLogger(__name__)


def _run(cmd: str):
    logger.debug("Running: %s", cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Command failed: %s\nstderr: %s", cmd, result.stderr)
    return result


def init_gateway():
    """Enable IP forwarding and set up the root tc qdisc (HTB)."""
    _run("sysctl -w net.ipv4.ip_forward=1")
    iface = settings.interface
    # Remove existing root qdisc (ignore errors if none exists)
    _run(f"tc qdisc del dev {iface} root 2>/dev/null || true")
    # Add HTB root qdisc
    _run(f"tc qdisc add dev {iface} root handle 1: htb default 9999")
    # Default class: full speed (unthrottled for unmanaged devices)
    _run(f"tc class add dev {iface} parent 1: classid 1:9999 htb rate 1000mbit")
    logger.info("Gateway initialized on interface %s", iface)


def teardown_gateway():
    """Remove root qdisc on shutdown."""
    iface = settings.interface
    _run(f"tc qdisc del dev {iface} root 2>/dev/null || true")
    logger.info("Gateway torn down on interface %s", iface)
