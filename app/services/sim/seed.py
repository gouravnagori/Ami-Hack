import asyncio
import math
import random
from datetime import UTC, datetime, time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Role, StorageCondition, VehicleType, settings
from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password
from app.db.base import Base
from app.db.models.capacity import CapacityWindow
from app.db.models.donor import Donor
from app.db.models.driver import Driver
from app.db.models.idempotency import IdempotencyRecord
from app.db.models.recipient import RecipientOrg
from app.db.models.safety_rules import FoodSafetyRule
from app.db.models.user import User
from app.db.session import async_session_maker, engine

setup_logging()
logger = get_logger("services.seed")


def random_offset_coords(lat: float, lng: float, radius_km: float) -> tuple[float, float]:
    """Generates coordinates within a given radius in kilometers using polar offset."""
    r = radius_km / 111.0 * math.sqrt(random.random())
    theta = random.random() * 2 * math.pi
    new_lat = lat + r * math.cos(theta)
    new_lng = lng + r * math.sin(theta) / math.cos(math.radians(lat))
    return round(new_lat, 5), round(new_lng, 5)


async def seed_food_safety_rules(db: AsyncSession) -> None:
    rules = [
        FoodSafetyRule(
            storage=StorageCondition.HOT,
            category="cooked_meals",
            max_hours=4.0,  # Hot cooked food: 4 hours
            transit_cap_minutes=45,
            handling_buffer_minutes=15,
        ),
        FoodSafetyRule(
            storage=StorageCondition.COLD,
            category="dairy_sweets",
            max_hours=3.0,  # Cold dairy / sweets: 3 hours
            transit_cap_minutes=40,
            handling_buffer_minutes=15,
        ),
        FoodSafetyRule(
            storage=StorageCondition.COLD,
            category="cold_meals",
            max_hours=6.0,
            transit_cap_minutes=60,
            handling_buffer_minutes=20,
        ),
        FoodSafetyRule(
            storage=StorageCondition.AMBIENT,
            category="packaged_bakery",
            max_hours=24.0,  # Packaged / ambient goods: 24 hours
            transit_cap_minutes=90,
            handling_buffer_minutes=30,
        ),
    ]
    for rule in rules:
        stmt = select(FoodSafetyRule).where(
            FoodSafetyRule.storage == rule.storage,
            FoodSafetyRule.category == rule.category,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if not existing:
            db.add(rule)
    await db.flush()
    logger.info("seeded_food_safety_rules", count=len(rules))


async def seed_demo_users(db: AsyncSession) -> None:
    roles = [
        (Role.DONOR, "Demo Donor", "+919999000000", "demo_donor@goldenhour.local"),
        (Role.RECIPIENT, "Demo Recipient", "+919999000001", "demo_recipient@goldenhour.local"),
        (Role.DRIVER, "Demo Driver", "+919999000002", "demo_driver@goldenhour.local"),
        (Role.ADMIN, "Demo Admin", "+919999000003", "demo_admin@goldenhour.local"),
    ]
    for role, name, phone, email in roles:
        stmt = select(User).where(User.phone == phone)
        user = (await db.execute(stmt)).scalar_one_or_none()
        if not user:
            user = User(
                role=role,
                name=name,
                phone=phone,
                email=email,
                password_hash=hash_password("DemoPassword123!"),
                is_active=True,
            )
            db.add(user)
            await db.flush()

            if role == Role.DONOR:
                donor = Donor(
                    user_id=user.id,
                    org_name="Spice Court Kitchen (Demo)",
                    kind="restaurant",
                    address="Connaught Place, New Delhi",
                    lat=settings.SEED_CENTER_LAT,
                    lng=settings.SEED_CENTER_LNG,
                    fssai_no="FSSAI-12345678901234",
                )
                db.add(donor)
            elif role == Role.RECIPIENT:
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
                    need_level=0.8,
                )
                db.add(recipient)
                await db.flush()
                # Default daily window
                window = CapacityWindow(
                    org_id=recipient.id,
                    start_time=time(8, 0),
                    end_time=time(23, 0),
                    max_portions=150,
                )
                db.add(window)
            elif role == Role.DRIVER:
                driver = Driver(
                    user_id=user.id,
                    vehicle_type=VehicleType.SCOOTER,
                    capacity_portions=80,
                    has_cold_box=True,
                    status="available",
                    lat=settings.SEED_CENTER_LAT + 0.005,
                    lng=settings.SEED_CENTER_LNG + 0.005,
                )
                db.add(driver)
    await db.flush()
    logger.info("seeded_demo_users")


async def seed_donors(db: AsyncSession, count: int = 12) -> None:
    kinds = ["restaurant", "caterer", "hostel_mess", "event", "grocer"]
    names = [
        "Haveli Banquet",
        "Saffron Dine",
        "Grand Kitchens",
        "Campus North Mess",
        "Royal Feast Caterers",
        "Urban Grocers",
        "Bukhara Delights",
        "Punjab Grill Express",
        "Green Valley Hotel",
        "Taj City Mess",
        "Blue Sapphire Catering",
        "Annapurna Meals",
    ]
    for i in range(count):
        phone = f"+9198110{i:05d}"
        if (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none():
            continue
        user = User(
            role=Role.DONOR,
            name=names[i % len(names)],
            phone=phone,
            email=f"donor_{i + 1}@goldenhour.local",
            password_hash=hash_password("Password123!"),
        )
        db.add(user)
        await db.flush()

        lat, lng = random_offset_coords(
            settings.SEED_CENTER_LAT, settings.SEED_CENTER_LNG, settings.SEED_RADIUS_KM
        )
        donor = Donor(
            user_id=user.id,
            org_name=user.name,
            kind=kinds[i % len(kinds)],
            address=f"Location #{i + 1}, Delhi NCR",
            lat=lat,
            lng=lng,
            fssai_no=f"FSSAI-1100{i:010d}",
        )
        db.add(donor)
    await db.flush()
    logger.info("seeded_donors", count=count)


async def seed_recipient_orgs(db: AsyncSession, count: int = 25) -> None:
    shelter_names = [
        "Asha Kuteer Shelter",
        "Prerna Children Home",
        "Seva Rasoi Foundation",
        "Mother Teresa Home",
        "Sankalp Food Shelter",
        "Umeed NGO Kitchen",
        "Shanti Niwas Elders Care",
        "Apna Ghar Shelter",
        "Samarpan Seva Trust",
        "Vatsalya Children Home",
        "Jan Kalyan Sanstha",
        "Navjeevan Food Bank",
        "Sahara Shelter",
        "Karuna Orphanage",
        "Bhavishya Children Home",
        "Divya Jyoti Kitchen",
        "Sewa Bharti Center",
        "Aastha Elders Home",
        "Sneha Deep Ashram",
        "Manav Seva Kendra",
        "Lok Kalyan Samiti",
        "Adarsh Bal Griha",
        "Mukti Foundation",
        "Anand Niketan",
        "Udayan Care Shelter",
    ]
    for i in range(count):
        phone = f"+9198220{i:05d}"
        if (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none():
            continue
        user = User(
            role=Role.RECIPIENT,
            name=shelter_names[i % len(shelter_names)],
            phone=phone,
            email=f"recipient_{i + 1}@goldenhour.local",
            password_hash=hash_password("Password123!"),
        )
        db.add(user)
        await db.flush()

        lat, lng = random_offset_coords(
            settings.SEED_CENTER_LAT, settings.SEED_CENTER_LNG, settings.SEED_RADIUS_KM
        )
        # Varied diets: 1/3 pure veg, 1/3 veg+egg, 1/3 all
        diets = (
            ["veg"] if i % 3 == 0 else (["veg", "egg"] if i % 3 == 1 else ["veg", "egg", "non_veg"])
        )
        # Varied cold storage: every 2nd or 3rd org has cold storage
        has_cold = i % 2 == 0
        storage = ["ambient", "hot"] + (["cold"] if has_cold else [])
        cold_units = random.choice([15, 25, 40, 60]) if has_cold else 0
        service_rate = random.choice([20.0, 30.0, 45.0, 60.0])
        need_level = round(random.uniform(0.4, 0.95), 2)

        org = RecipientOrg(
            user_id=user.id,
            name=user.name,
            address=f"Shelter Complex #{i + 1}, Delhi NCR",
            lat=lat,
            lng=lng,
            fssai_reg_no=f"REG-2200{i:010d}",
            verified_at=datetime.now(UTC),
            accepts_diets=diets,
            accepts_storage=storage,
            cold_max_units=cold_units,
            service_rate_per_hour=service_rate,
            need_level=need_level,
        )
        db.add(org)
        await db.flush()

        # Add daily capacity window
        window = CapacityWindow(
            org_id=org.id,
            start_time=time(9, 0),
            end_time=time(23, 0),
            max_portions=random.choice([80, 120, 150, 250, 300]),
        )
        db.add(window)
    await db.flush()
    logger.info("seeded_recipient_orgs", count=count)


async def seed_drivers(db: AsyncSession, count: int = 10) -> None:
    vehicles = [
        VehicleType.SCOOTER,
        VehicleType.BICYCLE,
        VehicleType.E_RICKSHAW,
        VehicleType.VAN,
    ]
    driver_names = [
        "Ramesh Kumar",
        "Vikram Singh",
        "Amit Sharma",
        "Suresh Patel",
        "Deepak Verma",
        "Manoj Yadav",
        "Sunil Gujjar",
        "Kavita Devi",
        "Pooja Rani",
        "Rahul Mishra",
    ]
    for i in range(count):
        phone = f"+9198330{i:05d}"
        if (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none():
            continue
        user = User(
            role=Role.DRIVER,
            name=driver_names[i % len(driver_names)],
            phone=phone,
            email=f"driver_{i + 1}@goldenhour.local",
            password_hash=hash_password("Password123!"),
        )
        db.add(user)
        await db.flush()

        v_type = vehicles[i % len(vehicles)]
        # 3 with cold boxes as specified in prompt Section 9
        has_cold = i in [0, 4, 7]
        caps = {
            VehicleType.BICYCLE: 25,
            VehicleType.SCOOTER: 60,
            VehicleType.E_RICKSHAW: 120,
            VehicleType.VAN: 250,
        }

        lat, lng = random_offset_coords(
            settings.SEED_CENTER_LAT, settings.SEED_CENTER_LNG, settings.SEED_RADIUS_KM
        )
        driver = Driver(
            user_id=user.id,
            vehicle_type=v_type,
            capacity_portions=caps[v_type],
            has_cold_box=has_cold,
            status="available" if i < 7 else "offline",
            lat=lat,
            lng=lng,
            last_ping_at=datetime.now(UTC),
        )
        db.add(driver)
    await db.flush()
    logger.info("seeded_drivers", count=count)


async def run_seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        await db.execute(delete(IdempotencyRecord))
        await seed_food_safety_rules(db)
        await seed_demo_users(db)
        await seed_donors(db, count=12)
        await seed_recipient_orgs(db, count=25)
        await seed_drivers(db, count=10)
        await db.commit()
    logger.info("seed_complete_successfully")


if __name__ == "__main__":
    asyncio.run(run_seed())
