"""
Golden Hour Intelligence Adapter — mapper.py

Maps between Ami-Hack domain models and Golden Hour Intelligence domain models.
Handles all field name, unit, and enum conversions at the integration boundary.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add Golden Hour intelligence engine to path
_GH_ROOT = Path(__file__).resolve().parents[4]  # x:\Golden Hour
if str(_GH_ROOT) not in sys.path:
    sys.path.insert(0, str(_GH_ROOT))

from food_rescue_engine.domain.donation import Donation as GHDonation
from food_rescue_engine.domain.driver import Driver as GHDriver
from food_rescue_engine.domain.enums import (
    DietType as GHDietType,
    DonationStatus as GHDonationStatus,
    DriverStatus as GHDriverStatus,
    FoodCategory as GHFoodCategory,
    PackagingType as GHPackagingType,
    StorageRequirement as GHStorageRequirement,
    TemperatureRequirement as GHTempRequirement,
    VehicleType as GHVehicleType,
)
from food_rescue_engine.domain.recipient import Recipient as GHRecipient
from food_rescue_engine.domain.vehicle import Vehicle as GHVehicle

from app.core.config import (
    DietType as AmiDietType,
    DonationStatus as AmiDonationStatus,
    DriverStatus as AmiDriverStatus,
    StorageCondition as AmiStorageCondition,
    VehicleType as AmiVehicleType,
)


# ── Diet Type Mapping ──

_DIET_MAP: dict[str, GHDietType] = {
    AmiDietType.VEG: GHDietType.VEGETARIAN,
    AmiDietType.EGG: GHDietType.OMNIVORE,       # egg = omnivore (closest)
    AmiDietType.NON_VEG: GHDietType.OMNIVORE,
}

_DIET_REVERSE: dict[str, str] = {
    GHDietType.VEGETARIAN: AmiDietType.VEG,
    GHDietType.VEGAN: AmiDietType.VEG,
    GHDietType.OMNIVORE: AmiDietType.NON_VEG,
    GHDietType.HALAL: AmiDietType.NON_VEG,
    GHDietType.KOSHER: AmiDietType.NON_VEG,
    GHDietType.GLUTEN_FREE: AmiDietType.VEG,
    GHDietType.NUT_FREE: AmiDietType.VEG,
}


def map_diet_to_gh(ami_diet: str) -> GHDietType:
    return _DIET_MAP.get(ami_diet, GHDietType.OMNIVORE)


def map_diet_from_gh(gh_diet: str) -> str:
    return _DIET_REVERSE.get(gh_diet, AmiDietType.NON_VEG)


# ── Storage / Temperature Mapping ──

_STORAGE_TO_TEMP: dict[str, GHTempRequirement] = {
    AmiStorageCondition.AMBIENT: GHTempRequirement.AMBIENT,
    AmiStorageCondition.HOT: GHTempRequirement.HOT_HOLDING,
    AmiStorageCondition.COLD: GHTempRequirement.REFRIGERATED,
}


def map_storage_to_temp(ami_storage: str) -> GHTempRequirement:
    return _STORAGE_TO_TEMP.get(ami_storage, GHTempRequirement.AMBIENT)


def map_storage_to_storage_req(ami_storage: str) -> GHStorageRequirement:
    if ami_storage == AmiStorageCondition.COLD:
        return GHStorageRequirement.WALK_IN_COOLER
    return GHStorageRequirement.DRY_PANTRY


# ── Donation Status Mapping ──

_DONATION_STATUS_MAP: dict[str, GHDonationStatus] = {
    AmiDonationStatus.DRAFT: GHDonationStatus.AVAILABLE,
    AmiDonationStatus.POSTED: GHDonationStatus.AVAILABLE,
    AmiDonationStatus.MATCHING: GHDonationStatus.AVAILABLE,
    AmiDonationStatus.PARTIALLY_MATCHED: GHDonationStatus.PARTIALLY_ALLOCATED,
    AmiDonationStatus.MATCHED: GHDonationStatus.ASSIGNED,
    AmiDonationStatus.IN_TRANSIT: GHDonationStatus.PICKED_UP,
    AmiDonationStatus.DELIVERED: GHDonationStatus.DELIVERED,
    AmiDonationStatus.EXPIRED: GHDonationStatus.EXPIRED,
    AmiDonationStatus.FALLBACK: GHDonationStatus.AVAILABLE,
    AmiDonationStatus.CANCELLED: GHDonationStatus.CANCELLED,
}


def map_donation_status_to_gh(ami_status: str) -> GHDonationStatus:
    return _DONATION_STATUS_MAP.get(ami_status, GHDonationStatus.AVAILABLE)


# ── Driver Status Mapping ──

_DRIVER_STATUS_MAP: dict[str, GHDriverStatus] = {
    AmiDriverStatus.OFFLINE: GHDriverStatus.OFFLINE,
    AmiDriverStatus.AVAILABLE: GHDriverStatus.AVAILABLE,
    AmiDriverStatus.ON_TASK: GHDriverStatus.ASSIGNED,
    AmiDriverStatus.STALE: GHDriverStatus.OFFLINE,
}


def map_driver_status_to_gh(ami_status: str) -> GHDriverStatus:
    return _DRIVER_STATUS_MAP.get(ami_status, GHDriverStatus.OFFLINE)


# ── Vehicle Type Mapping ──

_VEHICLE_MAP: dict[str, GHVehicleType] = {
    AmiVehicleType.BICYCLE: GHVehicleType.BICYCLE_CARGO,
    AmiVehicleType.SCOOTER: GHVehicleType.SEDAN,
    AmiVehicleType.E_RICKSHAW: GHVehicleType.SUV,
    AmiVehicleType.VAN: GHVehicleType.VAN,
}

# Capacity in kg by Ami-Hack vehicle type (using PORTION_KG=0.4)
_VEHICLE_CAPACITY_KG: dict[str, float] = {
    AmiVehicleType.BICYCLE: 10.0,
    AmiVehicleType.SCOOTER: 20.0,
    AmiVehicleType.E_RICKSHAW: 40.0,
    AmiVehicleType.VAN: 100.0,
}


# ── Entity Mappers ──

def map_donation_to_gh(
    donation,          # Ami-Hack Donation ORM model
    items: list,       # Ami-Hack DonationItem ORM models
    portion_kg: float = 0.4,
) -> GHDonation:
    """Convert an Ami-Hack Donation + DonationItems to a Golden Hour Donation."""
    # Calculate actual weight from items if available, fall back to portion estimate
    total_weight_kg = sum(
        (item.weight_kg or 0.0) for item in items
    )
    if total_weight_kg <= 0:
        total_weight_kg = donation.total_portions * portion_kg

    # Map food category from storage/category
    food_cat = GHFoodCategory.PREPARED_MEALS
    if hasattr(donation, "category"):
        cat = donation.category or "cooked_meals"
        _CAT_MAP = {
            "cooked_meals": GHFoodCategory.PREPARED_MEALS,
            "produce": GHFoodCategory.PRODUCE,
            "bakery": GHFoodCategory.BAKERY,
            "dairy": GHFoodCategory.DAIRY,
            "packaged": GHFoodCategory.PACKAGED_NON_PERISHABLE,
        }
        food_cat = _CAT_MAP.get(cat, GHFoodCategory.PREPARED_MEALS)

    now = datetime.now(timezone.utc)

    return GHDonation(
        donation_id=str(donation.id),
        donor_id=str(donation.donor_id),
        food_category=food_cat,
        diet_type=map_diet_to_gh(donation.diet),
        quantity=total_weight_kg,
        unit="kg",
        estimated_meals=donation.total_portions,
        temperature_requirement=map_storage_to_temp(donation.storage),
        storage_requirement=map_storage_to_storage_req(donation.storage),
        latitude=donation.pickup_lat,
        longitude=donation.pickup_lng,
        created_at=donation.created_at or now,
        available_from=donation.pickup_window_start,
        pickup_deadline=donation.pickup_window_end,
        safe_until=donation.safe_until,
        status=map_donation_status_to_gh(donation.status),
    )


def map_driver_to_gh(
    driver,   # Ami-Hack Driver ORM model
    shift_hours: float = 8.0,
) -> Optional[GHDriver]:
    """Convert an Ami-Hack Driver to a Golden Hour Driver."""
    if driver.lat is None or driver.lng is None:
        return None

    now = datetime.now(timezone.utc)
    from datetime import timedelta
    available_until = now + timedelta(hours=shift_hours)
    if driver.shift_started_at:
        available_until = driver.shift_started_at + timedelta(hours=shift_hours)

    vehicle_type = _VEHICLE_MAP.get(driver.vehicle_type, GHVehicleType.SEDAN)
    capacity_kg = _VEHICLE_CAPACITY_KG.get(driver.vehicle_type, 20.0)

    vehicle = GHVehicle(
        vehicle_id=str(driver.id),
        vehicle_type=vehicle_type,
        capacity_kg=capacity_kg,
        has_refrigeration=driver.has_cold_box,
    )

    return GHDriver(
        driver_id=str(driver.id),
        vehicle=vehicle,
        current_latitude=driver.lat,
        current_longitude=driver.lng,
        status=map_driver_status_to_gh(driver.status),
        available_from=driver.shift_started_at or now,
        available_until=available_until,
        current_load_kg=0.0,
        assigned_load_kg=0.0,
        historical_acceptance_rate=driver.accept_rate_ewma,
    )


def map_recipient_to_gh(
    org,   # Ami-Hack RecipientOrg ORM model
    portion_kg: float = 0.4,
) -> GHRecipient:
    """Convert an Ami-Hack RecipientOrg to a Golden Hour Recipient."""
    # Map diet types
    accepted_diets = set()
    for d in (org.accepts_diets or []):
        accepted_diets.add(map_diet_to_gh(d))

    # Map food categories (accept all by default)
    accepted_cats = {
        GHFoodCategory.PREPARED_MEALS,
        GHFoodCategory.PRODUCE,
        GHFoodCategory.BAKERY,
        GHFoodCategory.PACKAGED_NON_PERISHABLE,
    }

    # Map temperature support from storage acceptance
    supported_temps = set()
    for s in (org.accepts_storage or []):
        supported_temps.add(map_storage_to_temp(s))

    supported_storages = set()
    for s in (org.accepts_storage or []):
        supported_storages.add(map_storage_to_storage_req(s))

    return GHRecipient(
        recipient_id=str(org.id),
        name=org.name,
        latitude=org.lat,
        longitude=org.lng,
        total_capacity=org.max_capacity_portions * portion_kg,
        current_occupancy=0.0,  # Would need to query current stock
        accepted_food_categories=accepted_cats,
        accepted_diet_types=accepted_diets,
        accepted_packaging_types={GHPackagingType.BOXES, GHPackagingType.BULK_TRAYS, GHPackagingType.INDIVIDUAL_CONTAINERS},
        supported_temperatures=supported_temps,
        supported_storages=supported_storages,
        historical_acceptance_rate=org.reliability_ewma,
        operating_start=org.receiving_hours.split("-")[0].strip() if org.receiving_hours and "-" in org.receiving_hours else "08:00",
        operating_end=org.receiving_hours.split("-")[1].strip() if org.receiving_hours and "-" in org.receiving_hours else "20:00",
    )


# ── Unit Conversions ──

def metres_to_km(m: float) -> float:
    return m / 1000.0


def km_to_metres(km: float) -> float:
    return km * 1000.0


def seconds_to_minutes(s: float) -> float:
    return s / 60.0


def minutes_to_seconds(m: float) -> float:
    return m * 60.0
