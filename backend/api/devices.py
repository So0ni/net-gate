import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.ws import broadcast
from db import get_session
from models.device import Device
from models.profile import Profile
from schemas.device import DeviceCreate, DeviceOut, DeviceUpdate
from services import policy_service, presence_service

router = APIRouter(prefix="/devices", tags=["devices"])
_MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")


def _next_mark_id(session: Session) -> int:
    max_mark = session.query(Device.mark_id).order_by(Device.mark_id.desc()).first()
    return (max_mark[0] + 1) if max_mark else 1


def _normalize_mac_or_422(mac: str) -> str:
    normalized = mac.lower().strip()
    if not _MAC_RE.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Invalid MAC address format")
    return normalized


def _to_device_out(device: Device) -> DeviceOut:
    payload = DeviceOut.model_validate(device)
    return payload.model_copy(update={"online": presence_service.get_online(device.mac_address)})


@router.get("", response_model=list[DeviceOut])
def list_devices(session: Session = Depends(get_session)):
    presence_service.refresh_presence_cache(session)
    devices = session.query(Device).all()
    return [_to_device_out(device) for device in devices]


@router.post("", response_model=DeviceOut, status_code=201)
async def create_device(body: DeviceCreate, session: Session = Depends(get_session)):
    if session.get(Device, body.mac_address):
        raise HTTPException(status_code=409, detail="Device already registered")

    mark_id = _next_mark_id(session)
    device = Device(
        mac_address=body.mac_address,
        alias=body.alias,
        ip_address=body.ip_address,
        mark_id=mark_id,
    )
    session.add(device)
    try:
        session.flush()
        policy_service.register_device_rules(device)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to program gateway rules") from exc

    session.refresh(device)
    output = _to_device_out(device)
    await broadcast("device_updated", output.model_dump())
    return output


@router.patch("/{mac}", response_model=DeviceOut)
async def update_device(mac: str, body: DeviceUpdate, session: Session = Depends(get_session)):
    normalized_mac = _normalize_mac_or_422(mac)
    device = session.get(Device, normalized_mac)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if body.alias is not None:
        device.alias = body.alias
    if body.ip_address is not None:
        device.ip_address = body.ip_address

    profile_to_apply: Profile | None = None
    if body.profile_id is not None:
        profile_to_apply = session.get(Profile, body.profile_id)
        if not profile_to_apply:
            raise HTTPException(status_code=404, detail="Profile not found")
        device.profile_id = body.profile_id

    try:
        if profile_to_apply is not None:
            policy_service.apply_device_policy(device, profile_to_apply)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to apply policy") from exc

    session.refresh(device)
    output = _to_device_out(device)
    await broadcast("device_updated", output.model_dump())
    return output


@router.delete("/{mac}", status_code=204)
async def delete_device(mac: str, session: Session = Depends(get_session)):
    normalized_mac = _normalize_mac_or_422(mac)
    device = session.get(Device, normalized_mac)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        policy_service.remove_device_policy(device)
        session.delete(device)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove device policy") from exc

    presence_service.forget_device(normalized_mac)
    await broadcast("device_deleted", {"mac_address": normalized_mac})
