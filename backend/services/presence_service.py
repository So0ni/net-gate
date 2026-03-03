"""
presence_service.py

Tracks device online status using ARP/neighbor table snapshots and
broadcasts status changes over WebSocket.
"""
import asyncio
import logging
import re
import subprocess
import threading
from typing import Sequence

from sqlalchemy.orm import Session

from api.ws import broadcast
from config import settings
from db import engine
from models.device import Device

logger = logging.getLogger(__name__)

_MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")
_OFFLINE_STATES = {"FAILED", "INCOMPLETE"}
_status_lock = threading.Lock()
_status_cache: dict[str, bool] = {}


def _run(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    cmd = " ".join(args)
    logger.debug("Running: %s", cmd)
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Command failed: %s\nstderr: %s", cmd, result.stderr.strip())
        raise RuntimeError(result.stderr.strip() or f"command failed: {cmd}")
    return result


def _read_online_macs() -> set[str]:
    """
    Parse `ip neigh` output and return currently online MAC addresses.
    """
    try:
        result = _run(["ip", "neigh", "show", "dev", settings.interface])
    except Exception:
        logger.warning("Failed to read neighbor table on interface %s", settings.interface)
        return set()
    online: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if "lladdr" not in parts:
            continue
        idx = parts.index("lladdr")
        if idx + 1 >= len(parts):
            continue

        mac = parts[idx + 1].lower()
        if not _MAC_RE.fullmatch(mac):
            continue

        state = parts[-1].upper() if parts else ""
        if state in _OFFLINE_STATES:
            continue
        online.add(mac)
    return online


def refresh_presence_cache(session: Session) -> list[tuple[str, bool]]:
    """
    Refresh the in-memory online cache from neighbor table + registered devices.
    Returns changed items as (mac, online).
    """
    device_macs = [row[0].lower() for row in session.query(Device.mac_address).all()]
    online_macs = _read_online_macs()
    changed: list[tuple[str, bool]] = []
    device_set = set(device_macs)

    with _status_lock:
        existing = set(_status_cache.keys())
        for mac in device_macs:
            online = mac in online_macs
            if _status_cache.get(mac) != online:
                changed.append((mac, online))
            _status_cache[mac] = online

        for stale in existing - device_set:
            _status_cache.pop(stale, None)

    return changed


def get_online(mac_address: str) -> bool:
    mac = mac_address.lower()
    with _status_lock:
        return _status_cache.get(mac, False)


def forget_device(mac_address: str):
    mac = mac_address.lower()
    with _status_lock:
        _status_cache.pop(mac, None)


async def monitor_presence(interval_seconds: int = 5):
    """
    Poll neighbor table periodically and broadcast device online/offline changes.
    """
    while True:
        try:
            with Session(engine) as session:
                changes = refresh_presence_cache(session)
            for mac, online in changes:
                await broadcast("device_status_changed", {"mac_address": mac, "online": online})
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Presence monitor iteration failed")

        await asyncio.sleep(interval_seconds)
