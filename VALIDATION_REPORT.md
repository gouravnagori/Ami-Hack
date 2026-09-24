# RescueOS / GoldenHour — End-to-End Validation Report & Runbook

**Date**: September 24, 2026  
**Status**: Production-Ready for Demo & Frontend Integration  
**Backend Version**: v1.0.0-rc1  
**Test Suite**: 69 passed / 0 failed (100% passing)  
**Lint / Quality**: Ruff 0 errors (`All checks passed!`)

---

## 1. Executive Summary

The complete food rescue lifecycle has been end-to-end validated and verified as a unified, production-grade distributed system. The engine operates deterministically under zero external dependencies (with automatic haversine fallbacks when OSRM routing is offline and in-memory mock when Redis is absent), while preserving all real-world business constraints:

1. **Donor Submission**: Donors post surplus meals (or test preview during typing) with diet, storage condition, and pickup windows.
2. **Deterministic Safety Validation**: Dynamic shelf-life computation strictly derives `safe_until` based on food safety rules (e.g. 4.0h for hot cooked food, 3.0h for cold dairy/sweets).
3. **Multi-Objective Matching**: Candidate recipients are filtered against hard invariants (diet, storage capability, cold unit inventory, open service hours, time feasibility) and scored using a weighted multi-factor formula (time slack, distance, capacity fit, need level, reliability EWMA, fairness, and donor preference).
4. **Wedding-Night Mode (Split Allocation)**: Large donations (> recipient capacity) are split into labelled containers (`Container A`, `Container B`, ...) respecting minimum chunk sizes.
5. **Cascading Recipient Offers**: Recipients receive offers with TTL. Acceptance commits capacity; declines immediately cascade down the ranked candidate pool.
6. **Dynamic Driver Dispatch & VRP Route Generation**: Upon recipient acceptance, nearby compatible drivers (checking vehicle capacity and cold-box requirements) receive offers with turn-by-turn route previews.
7. **Secure OTP Handoff**: Pickup and dropoff stops require 6-digit OTP verification using constant-time hash comparisons. Dropoffs of cold food enforce temperature logging (`temp_c <= 8.0°C`).
8. **Real-Time Settlement & 80G Receipts**: Completed deliveries update driver EWMA speed factor, record immutable `ImpactLedger` entries (portions, weight in kg, CO2e avoided), and generate downloadable PDF receipts.
9. **Full Observability**: WebSocket broadcasts deliver live push events (`DONATION_CREATED`, `OFFER_CREATED`, `ROUTE_UPDATED`, `STOP_COMPLETED`, `DRIVER_LOCATION`), and the `/admin/live` endpoint feeds operational dashboards.

---

## 2. Test Results Matrix

| Test Suite File | Focus Area | Tests | Status |
|---|---|---|---|
| `tests/test_e2e_lifecycle.py` | Complete 8-stage lifecycle integration | 1 | **PASSED** |
| `tests/test_demo_scenario.py` | Hackathon deterministic 3-org demo scenario | 3 | **PASSED** |
| `tests/test_rejection_paths.py` | Edge cases, idempotency, auth, invalid OTP | 7 | **PASSED** |
| `tests/test_degradation.py` | OSRM fallback, haversine routing, resilience | 3 | **PASSED** |
| `tests/test_ws_lifecycle.py` | Real-time WebSocket subscriptions & event broadcast | 2 | **PASSED** |
| `tests/test_matching.py` | Matching filters, weights, scoring, split allocations | 10 | **PASSED** |
| `tests/test_dispatch.py` | Driver allocation, offer cascade, stops lifecycle | 11 | **PASSED** |
| `tests/test_donations.py` | Donation creation, preview, receipt PDF generation | 8 | **PASSED** |
| `tests/test_capacity.py` | Capacity reservations, holds, consumption, expiry | 6 | **PASSED** |
| `tests/test_extended_api.py` | Admin live snapshot, simulation, metrics, chaos | 5 | **PASSED** |
| `tests/test_auth.py` | JWT authentication, demo token generation, RBAC | 4 | **PASSED** |
| `tests/test_errors.py` | RFC 7807 error responses and validation formatting | 2 | **PASSED** |
| `tests/test_safety.py` | Food safety rules, temperature checks, shelf-life | 4 | **PASSED** |
| `tests/test_routing.py` | OSRM client, ETA calculations, polyline decoder | 3 | **PASSED** |
| **TOTAL** | **Entire Test Suite** | **69** | **ALL PASSED (100%)** |

- **Ruff Linting**: Clean (0 errors).
- **Execution Time**: ~55s for full test suite.

---

## 3. Demo Scenario & Execution Runbook

### Step 3.1 — Database Initialization & Seeding
Populate realistic Delhi-NCR donor kitchens, recipient shelters, and volunteer drivers:
```powershell
.venv\Scripts\python.exe -m app.services.sim.seed
```
This generates:
- Demo users for all 4 roles with standard password `Password123!`
- 12 donor restaurants & event halls
- 25 recipient shelters with diverse dietary policies and cold-chain capacities
- 10 volunteer drivers (bicycles, scooters, e-rickshaws, vans; 3 equipped with certified cold boxes)

### Step 3.2 — Start Backend Server
```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Step 3.3 — Executing the 8-Stage Lifecycle Demo via cURL

#### 1. Acquire Demo Donor Token
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/demo \
  -H "Content-Type: application/json" \
  -d '{"role": "donor"}'
```

#### 2. Post Surplus Food (e.g. 50 portions hot vegetarian curry)
```bash
curl -s -X POST http://localhost:8000/api/v1/donations \
  -H "Authorization: Bearer <DONOR_TOKEN>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: demo-run-001" \
  -d '{
    "items": [{"name": "Paneer Makhani & Rotis", "portions": 50}],
    "diet": "veg",
    "storage": "hot",
    "category": "cooked_meals",
    "prepared_at": "2026-09-24T18:00:00Z",
    "pickup_window": {
      "start": "2026-09-24T18:15:00Z",
      "end": "2026-09-24T20:15:00Z"
    },
    "pickup": {"lat": 28.6139, "lng": 77.2090, "address": "Connaught Place Kitchen"}
  }'
```
*Expected Output*: Returns `status: "matched"`, allocation ID, and `pickup_otp` (e.g. `"491823"`).

#### 3. Recipient Organization Checks Offers & Accepts
```bash
# Get recipient token
RECIP_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/demo -H "Content-Type: application/json" -d '{"role": "recipient"}' | jq -r .access_token)

# Accept offer
curl -s -X POST http://localhost:8000/api/v1/offers/<OFFER_ID>/accept \
  -H "Authorization: Bearer $RECIP_TOKEN" \
  -H "Content-Type: application/json"
```

#### 4. Driver Inspects Assigned Route
```bash
# Get driver token
DRIVER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/demo -H "Content-Type: application/json" -d '{"role": "driver"}' | jq -r .access_token)

# View active route with pickup & dropoff stops
curl -s -X GET http://localhost:8000/api/v1/driver/route \
  -H "Authorization: Bearer $DRIVER_TOKEN"
```

#### 5. Complete Pickup Handoff
```bash
# 1. Driver arrives at pickup
curl -s -X POST http://localhost:8000/api/v1/stops/<PICKUP_STOP_ID>/arrive \
  -H "Authorization: Bearer $DRIVER_TOKEN"

# 2. Complete with OTP from donor
curl -s -X POST http://localhost:8000/api/v1/stops/<PICKUP_STOP_ID>/complete \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"otp": "<PICKUP_OTP>"}'
```

#### 6. Complete Delivery Handoff
```bash
# 1. Driver arrives at shelter
curl -s -X POST http://localhost:8000/api/v1/stops/<DROPOFF_STOP_ID>/arrive \
  -H "Authorization: Bearer $DRIVER_TOKEN"

# 2. Complete delivery OTP
curl -s -X POST http://localhost:8000/api/v1/stops/<DROPOFF_STOP_ID>/complete \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"otp": "<DROPOFF_OTP>"}'
```

#### 7. Download PDF Tax Receipt
```bash
curl -s -X GET "http://localhost:8000/api/v1/donations/<DONATION_ID>/receipt.pdf" -o receipt.pdf
```

---

## 4. Known Boundaries & Engineering Decisions

1. **Cold Chain Temperature Verification**:
   - `temp_c` check is enforced on dropoff stop completion for cold items. In staging/test without physical Bluetooth probes, drivers submit manually verified temperatures.
2. **Routing Failover**:
   - Default routing connects to an OSRM instance. If unreachable or timeout exceeds 2s, the routing client immediately falls back to haversine road-detour calculations (factor 1.35x) without user-facing disruption.
3. **Database Concurrency**:
   - For SQLite local development, busy-timeouts and write locks are handled gracefully. In enterprise production, swap to PostgreSQL by changing `DATABASE_URL` in `.env`.

---

## 5. Quickstart for Frontend Integration

- **Backend API**: Running on port `8000`
- **CORS Policy**: Configured to accept any origin in development (`*`), allowing Next.js, Vite, or React Native dev servers on ports `3000`, `5173`, or `19000` to connect immediately.
- **WebSocket Testing**: Connect directly to `ws://localhost:8000/ws?token=<demo_jwt>&role=admin` to monitor live system events.
