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


def add_device_mark(mac: str, mark_id: int):
    """Mark packets from a MAC address with nfmark via ebtables."""
    mac = mac.lower()
    _run(
        f"ebtables -A FORWARD --src {mac} -j mark --mark-set {mark_id} --mark-target CONTINUE"
    )
    logger.info("ebtables: added mark %d for MAC %s", mark_id, mac)


def remove_device_mark(mac: str, mark_id: int):
    """Remove MAC → nfmark rule from ebtables."""
    mac = mac.lower()
    _run(
        f"ebtables -D FORWARD --src {mac} -j mark --mark-set {mark_id} --mark-target CONTINUE"
    )
    logger.info("ebtables: removed mark %d for MAC %s", mark_id, mac)
