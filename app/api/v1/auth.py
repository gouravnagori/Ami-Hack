from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Role, settings
from app.core.deps import get_current_user, get_db
from app.core.errors import AppException, ErrorCode, ForbiddenException, UnauthenticatedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    mask_phone,
    verify_password,
)
from app.db.models.donor import Donor
from app.db.models.driver import Driver
from app.db.models.recipient import RecipientOrg
from app.db.models.user import User
from app.schemas.auth import (
    DemoLoginRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
)
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id), user.role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        role=user.role,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check if phone or email already taken
    stmt = select(User).where(
        or_(
            User.phone == req.phone,
            User.email == str(req.email) if req.email else False,
        )
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise AppException(
            code=ErrorCode.VALIDATION_ERROR,
            message="An account with this phone number or email already exists.",
            status_code=status.HTTP_409_CONFLICT,
        )

    # Create User
    user = User(
        role=req.role,
        name=req.name,
        phone=req.phone,
        email=str(req.email) if req.email else None,
        password_hash=hash_password(req.password),
        locale=req.locale,
        city=req.city,
        avatar_url=req.avatar_url,
    )
    db.add(user)
    await db.flush()

    # Create associated profile
    profile_data = req.profile or {}
    if req.role == Role.DONOR:
        donor = Donor(
            user_id=user.id,
            org_name=profile_data.get("org_name", req.name),
            kind=profile_data.get("kind", "restaurant"),
            address=profile_data.get("address", "New Delhi"),
            lat=float(profile_data.get("lat", settings.SEED_CENTER_LAT)),
            lng=float(profile_data.get("lng", settings.SEED_CENTER_LNG)),
            fssai_no=profile_data.get("fssai_no"),
            default_pickup_window=profile_data.get("default_pickup_window"),
            pickup_address=profile_data.get("pickup_address"),
            food_category=profile_data.get("food_category"),
            contact_person=profile_data.get("contact_person"),
            operating_hours=profile_data.get("operating_hours"),
        )
        db.add(donor)
    elif req.role == Role.RECIPIENT:
        recipient = RecipientOrg(
            user_id=user.id,
            name=profile_data.get("name", req.name),
            address=profile_data.get("address", "New Delhi"),
            lat=float(profile_data.get("lat", settings.SEED_CENTER_LAT)),
            lng=float(profile_data.get("lng", settings.SEED_CENTER_LNG)),
            fssai_reg_no=profile_data.get("fssai_reg_no"),
            accepts_diets=profile_data.get("accepts_diets", ["veg", "egg", "non_veg"]),
            accepts_storage=profile_data.get("accepts_storage", ["ambient", "hot", "cold"]),
            cold_max_units=int(profile_data.get("cold_max_units", 20)),
            service_rate_per_hour=float(profile_data.get("service_rate_per_hour", 30.0)),
            need_level=float(profile_data.get("need_level", 0.7)),
            contact_person=profile_data.get("contact_person"),
            contact_phone=profile_data.get("contact_phone"),
            max_capacity_portions=int(profile_data.get("max_capacity_portions", 150)),
            food_restrictions=profile_data.get("food_restrictions"),
            receiving_hours=profile_data.get("receiving_hours"),
        )
        db.add(recipient)
    elif req.role == Role.DRIVER:
        driver = Driver(
            user_id=user.id,
            vehicle_type=profile_data.get("vehicle_type", "scooter"),
            capacity_portions=int(profile_data.get("capacity_portions", 60)),
            has_cold_box=bool(profile_data.get("has_cold_box", False)),
            lat=float(profile_data.get("lat", settings.SEED_CENTER_LAT)),
            lng=float(profile_data.get("lng", settings.SEED_CENTER_LNG)),
            vehicle_number=profile_data.get("vehicle_number"),
            operating_area=profile_data.get("operating_area"),
        )
        db.add(driver)

    await db.commit()
    await db.refresh(user)

    return build_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(User).where(
        or_(
            User.phone == req.phone_or_email,
            User.email == req.phone_or_email,
        )
    )
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise UnauthenticatedException(
            "Invalid credentials. Please verify your phone/email and password."
        )

    if not user.is_active:
        raise ForbiddenException("Account is currently suspended.")

    return build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: TokenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        payload = decode_token(req.refresh_token)
    except Exception:
        raise UnauthenticatedException("Refresh token is invalid or expired.") from None

    if payload.get("type") != "refresh":
        raise UnauthenticatedException("Invalid token type: refresh token expected.")

    import uuid

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthenticatedException("Invalid token payload: missing sub.")

    user = (
        await db.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthenticatedException("User account is inactive or no longer exists.")

    return build_token_response(user)


@router.post("/demo", response_model=TokenResponse)
async def demo_login(
    req: DemoLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not settings.DEMO_MODE:
        raise ForbiddenException("Demo mode is disabled on this server.")

    # Find or create a demo user for this role
    demo_phone = f"+91999900000{['donor', 'recipient', 'driver', 'admin'].index(req.role)}"
    stmt = select(User).where(User.phone == demo_phone)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        user = User(
            role=req.role,
            name=f"Demo {req.role.capitalize()}",
            phone=demo_phone,
            email=f"demo_{req.role}@goldenhour.local",
            password_hash=hash_password("DemoPassword123!"),
            locale="en",
        )
        db.add(user)
        await db.flush()

        # Seed profile for demo user
        if req.role == Role.DONOR:
            donor = Donor(
                user_id=user.id,
                org_name="Spice Court Kitchen (Demo)",
                kind="restaurant",
                address="Connaught Place, New Delhi",
                lat=settings.SEED_CENTER_LAT,
                lng=settings.SEED_CENTER_LNG,
            )
            db.add(donor)
        elif req.role == Role.RECIPIENT:
            recipient = RecipientOrg(
                user_id=user.id,
                name="Asha Shelter Home (Demo)",
                address="Pahar Ganj, New Delhi",
                lat=settings.SEED_CENTER_LAT + 0.01,
                lng=settings.SEED_CENTER_LNG + 0.01,
                accepts_diets=["veg", "egg", "non_veg"],
                accepts_storage=["ambient", "hot", "cold"],
                cold_max_units=25,
                service_rate_per_hour=35.0,
            )
            db.add(recipient)
        elif req.role == Role.DRIVER:
            driver = Driver(
                user_id=user.id,
                vehicle_type="scooter",
                capacity_portions=80,
                has_cold_box=True,
                status="available",
                lat=settings.SEED_CENTER_LAT + 0.005,
                lng=settings.SEED_CENTER_LNG + 0.005,
            )
            db.add(driver)

        await db.commit()
        await db.refresh(user)

    return build_token_response(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    profile_dict = None
    if current_user.role == Role.DONOR and current_user.donor_profile:
        profile_dict = {
            "org_name": current_user.donor_profile.org_name,
            "kind": current_user.donor_profile.kind,
            "address": current_user.donor_profile.address,
            "lat": current_user.donor_profile.lat,
            "lng": current_user.donor_profile.lng,
            "fssai_no": current_user.donor_profile.fssai_no,
            "default_pickup_window": current_user.donor_profile.default_pickup_window,
            "pickup_address": current_user.donor_profile.pickup_address,
            "food_category": current_user.donor_profile.food_category,
            "contact_person": current_user.donor_profile.contact_person,
            "operating_hours": current_user.donor_profile.operating_hours,
        }
    elif current_user.role == Role.RECIPIENT and current_user.recipient_profile:
        profile_dict = {
            "name": current_user.recipient_profile.name,
            "address": current_user.recipient_profile.address,
            "lat": current_user.recipient_profile.lat,
            "lng": current_user.recipient_profile.lng,
            "accepts_diets": current_user.recipient_profile.accepts_diets,
            "cold_max_units": current_user.recipient_profile.cold_max_units,
            "fssai_reg_no": current_user.recipient_profile.fssai_reg_no,
            "contact_person": current_user.recipient_profile.contact_person,
            "contact_phone": current_user.recipient_profile.contact_phone,
            "max_capacity_portions": current_user.recipient_profile.max_capacity_portions,
            "food_restrictions": current_user.recipient_profile.food_restrictions,
            "receiving_hours": current_user.recipient_profile.receiving_hours,
        }
    elif current_user.role == Role.DRIVER and current_user.driver_profile:
        profile_dict = {
            "vehicle_type": current_user.driver_profile.vehicle_type,
            "capacity_portions": current_user.driver_profile.capacity_portions,
            "has_cold_box": current_user.driver_profile.has_cold_box,
            "status": current_user.driver_profile.status,
            "vehicle_number": current_user.driver_profile.vehicle_number,
            "operating_area": current_user.driver_profile.operating_area,
        }

    return UserResponse(
        id=current_user.id,
        role=current_user.role,
        name=current_user.name,
        phone=current_user.phone,
        phone_masked=mask_phone(current_user.phone),
        email=current_user.email,
        is_active=current_user.is_active,
        locale=current_user.locale,
        city=current_user.city,
        avatar_url=current_user.avatar_url,
        profile=profile_dict,
    )

@router.put("/me", response_model=UserResponse)
async def update_me(
    req: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Update base user fields
    if req.name is not None:
        current_user.name = req.name
    if req.email is not None:
        current_user.email = str(req.email)
    if req.city is not None:
        current_user.city = req.city
    if req.avatar_url is not None:
        current_user.avatar_url = req.avatar_url

    # Update profile fields
    if req.profile:
        if current_user.role == Role.DONOR and current_user.donor_profile:
            for k, v in req.profile.items():
                if hasattr(current_user.donor_profile, k):
                    setattr(current_user.donor_profile, k, v)
        elif current_user.role == Role.RECIPIENT and current_user.recipient_profile:
            for k, v in req.profile.items():
                if hasattr(current_user.recipient_profile, k):
                    setattr(current_user.recipient_profile, k, v)
        elif current_user.role == Role.DRIVER and current_user.driver_profile:
            for k, v in req.profile.items():
                if hasattr(current_user.driver_profile, k):
                    setattr(current_user.driver_profile, k, v)

    await db.commit()
    await db.refresh(current_user)

    return await get_me(current_user=current_user)
