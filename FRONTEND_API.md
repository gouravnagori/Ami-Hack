# RescueOS / GoldenHour — Frontend API & Integration Contract

This document provides the authoritative integration specification for frontend clients interacting with the GoldenHour RescueOS backend.

---

## 1. Global Conventions & Protocol

### 1.1 Base URL & Environment
- **Local Dev Base URL**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **ReDoc Spec**: `http://localhost:8000/redoc`
- **OpenAPI Schema (JSON)**: `http://localhost:8000/openapi.json`
- **WebSocket URL**: `ws://localhost:8000/ws`

### 1.2 Authentication Scheme
- Standard HTTP Authorization Header:
  ```http
  Authorization: Bearer <access_token>
  ```
- Demo authentication endpoint `POST /api/v1/auth/demo` generates valid JWTs without SMS/email verification for all 4 roles: `donor`, `recipient`, `driver`, `admin`.

### 1.3 Standard Request Headers
| Header | Requirement | Description |
|---|---|---|
| `Authorization` | Required for authenticated routes | `Bearer <jwt_token>` |
| `Content-Type` | Required for JSON bodies | `application/json` |
| `Idempotency-Key` | Recommended for all mutating `POST` endpoints | Unique UUID/string per mutation. Repeating the same key returns the cached successful response without duplicate side-effects. |
| `X-Request-ID` | Optional | Client-generated trace ID. If omitted, the server automatically assigns and returns a UUID in the response header. |

### 1.4 Standard Error Response Format
All application errors adhere to RFC 7807 problem details:
```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid 6-digit delivery OTP",
  "details": {},
  "request_id": "7f09cba1-82df-4e31-8bc1-50e50f3b55c2"
}
```

Common HTTP status codes:
- `400 Bad Request`: Format / domain validation error (`code: "VALIDATION_ERROR"`).
- `401 Unauthorized`: Missing, expired, or invalid JWT (`code: "UNAUTHENTICATED"`).
- `403 Forbidden`: Authenticated user lacks the required role (`code: "FORBIDDEN"`).
- `404 Not Found`: Resource does not exist (`code: "NOT_FOUND"`).
- `409 Conflict`: Business invariant violation / stale state (`code: "STATE_CONFLICT"`).
- `422 Unprocessable Content`: Pydantic schema validation failure.
- `500 Internal Server Error`: Unhandled server exception.

---

## 2. Authentication API

### `POST /api/v1/auth/demo`
Generate a bearer token for instantaneous frontend demo and testing.

- **Auth Required**: None (public demo route)
- **Request Body**:
  ```json
  {
    "role": "donor"
  }
  ```
  *(Supported roles: `"donor"`, `"recipient"`, `"driver"`, `"admin"`)*
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "role": "donor",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "demo_donor@goldenhour.local"
  }
  ```

---

## 3. Donor Flow

### `POST /api/v1/donations/preview`
Real-time feasibility check and recipient matching preview while the donor is typing.

- **Auth Required**: `donor` or `admin`
- **Request Body**:
  ```json
  {
    "items": [
      { "name": "Dal & Rice", "portions": 40 }
    ],
    "diet": "veg",
    "storage": "hot",
    "category": "cooked_meals",
    "prepared_at": "2026-09-24T18:00:00Z",
    "pickup_window": {
      "start": "2026-09-24T18:30:00Z",
      "end": "2026-09-24T20:30:00Z"
    },
    "pickup": {
      "lat": 28.6139,
      "lng": 77.2090,
      "address": "Connaught Place, New Delhi"
    }
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "feasible_recipients": 3,
    "best": {
      "name": "Asha Kuteer Shelter",
      "score": 87.5,
      "reasons": [
        { "code": "HIGH_NEED", "label": "Urgent need level (90%)" },
        { "code": "PROXIMITY", "label": "Only 0.8 km away" },
        { "code": "TIME_SLACK", "label": "85 min to spare before expiry" }
      ]
    },
    "safe_until": "2026-09-24T22:00:00Z",
    "safety_rule_applied": "hot / cooked_meals (max 4.0h)"
  }
  ```

### `POST /api/v1/donations`
Publish surplus food into the matching engine.

- **Auth Required**: `donor`
- **Headers**: `Idempotency-Key: <unique-key>`
- **Request Body**: Same schema as preview above.
- **Response `201 Created`**:
  ```json
  {
    "id": "c1f7b036-7c64-4dd2-87f5-2bf327b7de7a",
    "status": "matched",
    "diet": "veg",
    "storage": "hot",
    "category": "cooked_meals",
    "safe_until": "2026-09-24T22:00:00Z",
    "items": [
      { "name": "Dal & Rice", "portions": 40 }
    ],
    "allocations": [
      {
        "id": "e0b968a3-94c0-43f9-ae79-880eafe14c62",
        "recipient_id": "a1811a2f-e8b2-4d12-b0e6-fb72714241d9",
        "recipient_name": "Asha Kuteer Shelter",
        "portions": 40,
        "container_label": "Container A",
        "status": "offered",
        "deadline": "2026-09-24T21:45:00Z",
        "predicted_delivery": "2026-09-24T19:15:00Z",
        "pickup_otp": "481920"
      }
    ],
    "created_at": "2026-09-24T18:05:00Z"
  }
  ```
  *(Note: The donor response exposes plain `pickup_otp` to hand to the driver).*

### `GET /api/v1/donations/{id}`
Retrieve donation status, allocation details, and full matching breakdown.

- **Auth Required**: Authenticated user
- **Response `200 OK`**:
  Returns the `DonationSchema` with populated `allocations`, `items`, and `explanation` scores.

### `GET /api/v1/donations/{id}/receipt.pdf`
Download downloadable 80G tax receipt and food rescue certificate.

- **Auth Required**: Public / Authenticated
- **Response `200 OK`**:
  - `Content-Type: application/pdf`
  - Body: Binary PDF stream.

---

## 4. Organization (Recipient) Flow

### `GET /api/v1/org/offers`
List pending and historical donation offers for the logged-in recipient organization.

- **Auth Required**: `recipient`
- **Query Params**: `status=pending` (optional filter: `pending`, `accepted`, `declined`, `expired`)
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "8c3c1c2f-7f33-4577-a2fc-2d1e66ee0c09",
      "allocation_id": "e0b968a3-94c0-43f9-ae79-880eafe14c62",
      "kind": "recipient",
      "portions": 40,
      "food_category": "cooked_meals",
      "diet": "veg",
      "storage": "hot",
      "status": "pending",
      "expires_at": "2026-09-24T18:35:00Z",
      "ttl_seconds_remaining": 1780
    }
  ]
  ```

### `POST /api/v1/offers/{id}/accept`
Accept an incoming food allocation. Locks reserved capacity and triggers driver dispatch.

- **Auth Required**: `recipient` (for recipient offers) or `driver` (for driver offers)
- **Headers**: `Idempotency-Key: <unique-key>`
- **Request Body**: `{}`
- **Response `200 OK`**:
  ```json
  {
    "status": "accepted",
    "offer_id": "8c3c1c2f-7f33-4577-a2fc-2d1e66ee0c09",
    "allocation_id": "e0b968a3-94c0-43f9-ae79-880eafe14c62",
    "accepted_at": "2026-09-24T18:07:00Z"
  }
  ```

### `POST /api/v1/offers/{id}/decline`
Decline an offer. Immediately triggers automatic cascade to the next ranked recipient.

- **Auth Required**: `recipient` or `driver`
- **Request Body**:
  ```json
  {
    "reason": "capacity_full"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "status": "declined",
    "offer_id": "8c3c1c2f-7f33-4577-a2fc-2d1e66ee0c09"
  }
  ```

### `GET /api/v1/org/capacity`
Inspect organization's active capacity, cold units, and scheduled service windows.

- **Auth Required**: `recipient`
- **Response `200 OK`**:
  ```json
  {
    "org_id": "a1811a2f-e8b2-4d12-b0e6-fb72714241d9",
    "name": "Asha Kuteer Shelter",
    "total_capacity_portions": 100,
    "available_portions": 60,
    "committed_portions": 40,
    "cold_storage_units": 40,
    "cold_storage_used": 0,
    "is_open": true
  }
  ```

---

## 5. Driver Flow

### `GET /api/v1/driver/offers`
View delivery assignments offered to the volunteer driver.

- **Auth Required**: `driver`
- **Query Params**: `status=pending`
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "7b508ee0-0fc1-460d-85fa-7f411ba188ef",
      "allocation_id": "e0b968a3-94c0-43f9-ae79-880eafe14c62",
      "kind": "driver",
      "status": "pending",
      "route_preview": {
        "pickup_address": "Connaught Place, New Delhi",
        "dropoff_address": "Asha Kuteer Shelter, Daryaganj",
        "est_distance_km": 3.8,
        "est_duration_minutes": 18
      },
      "expires_at": "2026-09-24T18:25:00Z"
    }
  ]
  ```

### `GET /api/v1/driver/route`
Retrieve current active multi-stop navigation manifest.

- **Auth Required**: `driver`
- **Response `200 OK`**:
  ```json
  {
    "id": "4a35017e-79fb-4d40-9a28-66258950d18e",
    "status": "active",
    "version": 1,
    "planned_distance_m": 4120.0,
    "planned_duration_s": 1080.0,
    "polyline": "gfo_Ia_...encoded_polyline...",
    "stops": [
      {
        "id": "1b089c19-df55-46aa-b2b9-e13cbef78e10",
        "seq": 1,
        "type": "pickup",
        "status": "pending",
        "address": "Connaught Place, New Delhi",
        "lat": 28.6139,
        "lng": 77.2090,
        "window_start": "2026-09-24T18:30:00Z",
        "window_end": "2026-09-24T20:30:00Z",
        "portions": 40
      },
      {
        "id": "713bc498-8ec1-4318-8742-fca1218df883",
        "seq": 2,
        "type": "dropoff",
        "status": "pending",
        "address": "Asha Kuteer Shelter, Daryaganj",
        "lat": 28.6150,
        "lng": 77.2095,
        "window_start": "2026-09-24T19:00:00Z",
        "window_end": "2026-09-24T21:45:00Z",
        "portions": 40
      }
    ]
  }
  ```

### `POST /api/v1/stops/{id}/arrive`
Driver flags arrival at pickup/dropoff checkpoint.

- **Auth Required**: `driver`
- **Response `200 OK`**:
  ```json
  {
    "id": "1b089c19-df55-46aa-b2b9-e13cbef78e10",
    "status": "arrived",
    "arrived_at": "2026-09-24T18:28:45Z"
  }
  ```

### `POST /api/v1/stops/{id}/complete`
Complete stop with cryptographically validated OTP handoff.

- **Auth Required**: `driver`
- **Headers**: `Idempotency-Key: <unique-key>`
- **Request Body**:
  ```json
  {
    "otp": "481920",
    "temp_c": 65.0,
    "proof_photo_base64": null
  }
  ```
  *(Note: `temp_c` is required when completing dropoff for cold-chain goods).*
- **Response `200 OK`**:
  ```json
  {
    "id": "1b089c19-df55-46aa-b2b9-e13cbef78e10",
    "status": "done",
    "completed_at": "2026-09-24T18:32:10Z"
  }
  ```

### `POST /api/v1/stops/{id}/issue`
Report on-the-ground operational exception (e.g. food spoiled, door locked).

- **Auth Required**: `driver`
- **Request Body**:
  ```json
  {
    "code": "food_not_ready",
    "note": "Donor kitchen running 20 minutes late"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "id": "1b089c19-df55-46aa-b2b9-e13cbef78e10",
    "status": "failed",
    "issue_code": "food_not_ready"
  }
  ```

### `POST /api/v1/driver/ping`
Publish high-frequency telemetry & GPS location update.

- **Auth Required**: `driver`
- **Request Body**:
  ```json
  {
    "lat": 28.6142,
    "lng": 77.2091,
    "speed_kmh": 24.5
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "status": "recorded",
    "timestamp": "2026-09-24T18:30:15Z"
  }
  ```

### `GET /api/v1/driver/stats`
Volunteer performance & verified impact summary.

- **Auth Required**: `driver`
- **Response `200 OK`**:
  ```json
  {
    "completed_deliveries": 12,
    "total_meals_delivered": 480,
    "co2e_saved_kg": 420.0,
    "on_time_rate": 0.98
  }
  ```

---

## 6. Ops & Admin Control Center

### `GET /api/v1/admin/live`
Real-time fleet operations snapshot for the live dispatch map.

- **Auth Required**: `admin`
- **Response `200 OK`**:
  ```json
  {
    "as_of": "2026-09-24T18:35:00Z",
    "donors": [{ "id": "...", "org_name": "Delhi Palace", "lat": 28.6139, "lng": 77.2090 }],
    "orgs": [{ "id": "...", "name": "Asha Kuteer", "lat": 28.6150, "lng": 77.2095, "need_level": 0.9 }],
    "drivers": [{ "id": "...", "name": "Rohan Driver", "status": "en_route", "lat": 28.6142, "lng": 77.2091 }],
    "routes": [{ "id": "...", "driver_id": "...", "status": "active", "stops_count": 2 }],
    "online_drivers": 7,
    "active_routes": 3,
    "donations": []
  }
  ```

### `GET /api/v1/admin/metrics`
High-level KPIs, rescue rates, and cold-chain compliance.

- **Auth Required**: `admin`
- **Response `200 OK`**:
  ```json
  {
    "rescue_rate": 0.94,
    "avg_delivery_minutes": 27.5,
    "cold_chain_breaches": 0,
    "total_meals_rescued": 1250,
    "total_co2e_saved_kg": 1093.75
  }
  ```

### `POST /api/v1/admin/simulate/donation`
Inject synthetic donations to demo matching behavior live.

- **Auth Required**: `admin`
- **Request Body**:
  ```json
  {
    "scenario": "wedding_feast",
    "count": 1
  }
  ```
  *(Supported scenarios: `"wedding_feast"`, `"cold_chain"`, `"expiring_fast"`, `"regular"`)*
- **Response `200 OK`**:
  ```json
  {
    "scenario": "wedding_feast",
    "created": [
      {
        "id": "c1f7b036-7c64-4dd2-87f5-2bf327b7de7a",
        "total_portions": 250,
        "status": "matched"
      }
    ],
    "donations": [
      {
        "id": "c1f7b036-7c64-4dd2-87f5-2bf327b7de7a",
        "total_portions": 250,
        "status": "matched"
      }
    ]
  }
  ```

### `POST /api/v1/admin/chaos`
Simulate operational degradation scenarios (e.g. driver dropout, OSRM outage).

- **Auth Required**: `admin`
- **Request Body**:
  ```json
  {
    "scenario": "driver_drop",
    "target_id": "4a35017e-79fb-4d40-9a28-66258950d18e"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "status": "injected",
    "scenario": "driver_drop",
    "detail": "Driver cancelled route; automated re-dispatch initiated"
  }
  ```

---

## 7. Real-time WebSocket Protocol

Connect via:
```
ws://localhost:8000/ws?token=<jwt_token>&role=<role>&id=<user_id>
```

### Event Message Format
All inbound and outbound events use the standard envelope:
```json
{
  "event": "EVENT_NAME",
  "data": { ... },
  "timestamp": "2026-09-24T18:35:00Z"
}
```

### Supported Event Types
| Event Name | Target Audience | Payload Summary |
|---|---|---|
| `DONATION_CREATED` | Admin / Donors | `{ "donation_id": "...", "status": "matched" }` |
| `OFFER_CREATED` | Recipient Org / Driver | `{ "offer_id": "...", "kind": "recipient|driver", "allocation_id": "..." }` |
| `OFFER_ACCEPTED` | Donor / Recipient / Driver | `{ "offer_id": "...", "status": "accepted" }` |
| `ROUTE_UPDATED` | Driver / Admin | `{ "route_id": "...", "status": "active", "stops": [...] }` |
| `STOP_ARRIVED` | Donor / Recipient / Admin | `{ "stop_id": "...", "type": "pickup|dropoff" }` |
| `STOP_COMPLETED` | Donor / Recipient / Admin | `{ "stop_id": "...", "type": "pickup|dropoff", "status": "done" }` |
| `DRIVER_LOCATION` | Admin / Dispatch Map | `{ "driver_id": "...", "lat": 28.6142, "lng": 77.2091 }` |
| `ALLOCATION_UPDATED` | Recipient / Admin | `{ "allocation_id": "...", "status": "delivered" }` |
