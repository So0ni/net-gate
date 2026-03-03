"""
policy_service.py

Orchestrates the binding between a Device and a Profile,
coordinating ebtables / iptables / tc operations.
"""
import logging
from sqlalchemy.orm import Session

from models.device import Device
from models.profile import Profile
from core import tc_manager, ebtables_manager, iptables_manager

logger = logging.getLogger(__name__)


def apply_device_policy(device: Device, profile: Profile):
    """Apply a profile's network rules for a device."""
    tc_manager.apply_profile(
        mark_id=device.mark_id,
        latency_ms=profile.latency_ms,
        jitter_ms=profile.jitter_ms,
        loss_percent=profile.loss_percent,
        bandwidth_kbps=profile.bandwidth_kbps,
    )
    logger.info("Policy applied: device=%s profile=%s", device.mac_address, profile.name)


def remove_device_policy(device: Device):
    """Remove all network rules for a device."""
    ebtables_manager.remove_device_mark(device.mac_address, device.mark_id)
    iptables_manager.remove_mark_to_class(device.mark_id)
    tc_manager.remove_profile(device.mark_id)
    logger.info("Policy removed: device=%s", device.mac_address)


def register_device_rules(device: Device):
    """Set up ebtables + iptables rules for a newly registered device."""
    try:
        ebtables_manager.add_device_mark(device.mac_address, device.mark_id)
        iptables_manager.add_mark_to_class(device.mark_id)
    except Exception:
        # Best-effort rollback if one of the steps failed.
        ebtables_manager.remove_device_mark(device.mac_address, device.mark_id)
        iptables_manager.remove_mark_to_class(device.mark_id)
        raise
    logger.info("Rules registered: device=%s mark=%d", device.mac_address, device.mark_id)


def restore_all_policies(session: Session):
    """Called on startup to re-apply all persisted policies.

    Cleans up any stale rules first (idempotent delete), then re-adds them
    to avoid duplicate ebtables/iptables entries if the container was not
    shut down cleanly.
    """
    devices = session.query(Device).all()
    for device in devices:
        try:
            # Remove potentially stale rules before re-adding (ignore errors)
            ebtables_manager.remove_device_mark(device.mac_address, device.mark_id)
            iptables_manager.remove_mark_to_class(device.mark_id)
            # Re-register clean rules
            register_device_rules(device)
            if device.profile_id:
                profile = session.get(Profile, device.profile_id)
                if profile:
                    apply_device_policy(device, profile)
        except Exception:
            logger.exception("Failed to restore policy for device=%s", device.mac_address)
    logger.info("Restored policies for %d device(s)", len(devices))
