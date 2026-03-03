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


def add_mark_to_class(mark_id: int):
    """Route packets with nfmark → tc class 1:<mark_id> via iptables CLASSIFY."""
    iface = settings.interface
    _run(
        f"iptables -t mangle -A POSTROUTING -o {iface} "
        f"-m mark --mark {mark_id} "
        f"-j CLASSIFY --set-class 1:{mark_id}"
    )
    logger.info("iptables: mark %d → class 1:%d", mark_id, mark_id)


def remove_mark_to_class(mark_id: int):
    """Remove iptables CLASSIFY rule for the given mark."""
    iface = settings.interface
    _run(
        f"iptables -t mangle -D POSTROUTING -o {iface} "
        f"-m mark --mark {mark_id} "
        f"-j CLASSIFY --set-class 1:{mark_id}"
    )
    logger.info("iptables: removed mark %d rule", mark_id)
