from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_session
from models.profile import Profile
from schemas.profile import ProfileCreate, ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileOut])
def list_profiles(session: Session = Depends(get_session)):
    return session.query(Profile).all()


@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(body: ProfileCreate, session: Session = Depends(get_session)):
    profile = Profile(**body.model_dump(), is_builtin=False)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.patch("/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: int, body: ProfileUpdate, session: Session = Depends(get_session)):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.is_builtin:
        raise HTTPException(status_code=403, detail="Built-in profiles cannot be modified")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    session.commit()
    session.refresh(profile)
    return profile


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, session: Session = Depends(get_session)):
    profile = session.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if profile.is_builtin:
        raise HTTPException(status_code=403, detail="Built-in profiles cannot be deleted")

    session.delete(profile)
    session.commit()
