from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_session
from models.device import Device
from models.profile import Profile
from schemas.profile import ProfileCreate, ProfileOut, ProfileUpdate
from services import policy_service

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileOut])
def list_profiles(session: Session = Depends(get_session)):
    return session.query(Profile).all()


@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(body: ProfileCreate, session: Session = Depends(get_session)):
    profile = Profile(**body.model_dump(), is_builtin=False)
    try:
        session.add(profile)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create profile") from exc

    session.refresh(profile)
    return profile


@router.patch("/{profile_id}", response_model=ProfileOut)
def update_profile(
    profile_id: int, body: ProfileUpdate, session: Session = Depends(get_session)
):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.is_builtin:
        raise HTTPException(
            status_code=403, detail="Built-in profiles cannot be modified"
        )

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    try:
        # Re-apply tc rules for all devices currently using this profile
        bound_devices = (
            session.query(Device).filter(Device.profile_id == profile_id).all()
        )
        for device in bound_devices:
            policy_service.apply_device_policy(device, profile)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to update profile policy"
        ) from exc

    session.refresh(profile)
    return profile


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, session: Session = Depends(get_session)):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.is_builtin:
        raise HTTPException(
            status_code=403, detail="Built-in profiles cannot be deleted"
        )

    try:
        # Clear profile binding and remove tc rules for affected devices
        bound_devices = (
            session.query(Device).filter(Device.profile_id == profile_id).all()
        )
        for device in bound_devices:
            policy_service.remove_device_policy(device)
            device.profile_id = None
            # Re-register base ebtables/iptables rules without any tc profile
            policy_service.register_device_rules(device)

        session.delete(profile)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete profile") from exc
