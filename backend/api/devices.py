from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.ws import broadcast
from db import get_session
from models.device import Device
from models.profile import Profile
from schemas.device import DeviceCreate, DeviceOut, DeviceUpdate
from services import policy_service

router = APIRouter(prefix="/devices", tags=["devices"])


def _next_mark_id(session: Session) -> int:
    max_mark = session.query(Device.mark_id).order_by(Device.mark_id.desc()).first()
    return (max_mark[0] + 1) if max_mark else 1


@router.get("", response_model=list[DeviceOut])
def list_devices(session: Session = Depends(get_session)):
    return session.query(Device).all()


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
    session.commit()
    session.refresh(device)

    policy_service.register_device_rules(device)
    await broadcast("device_updated", DeviceOut.model_validate(device).model_dump())
    return device


@router.patch("/{mac}", response_model=DeviceOut)
async def update_device(mac: str, body: DeviceUpdate, session: Session = Depends(get_session)):
    device = session.get(Device, mac.lower())
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if body.alias is not None:
        device.alias = body.alias
    if body.ip_address is not None:
        device.ip_address = body.ip_address

    if body.profile_id is not None:
        profile = session.get(Profile, body.profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        device.profile_id = body.profile_id
        policy_service.apply_device_policy(device, profile)

    session.commit()
    session.refresh(device)
    await broadcast("device_updated", DeviceOut.model_validate(device).model_dump())
    return device


@router.delete("/{mac}", status_code=204)
async def delete_device(mac: str, session: Session = Depends(get_session)):
    device = session.get(Device, mac.lower())
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    policy_service.remove_device_policy(device)
    session.delete(device)
    session.commit()
    await broadcast("device_deleted", {"mac_address": mac.lower()})
