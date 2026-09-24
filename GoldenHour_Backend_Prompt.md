# BACKEND PROMPT — GoldenHour (working name) · FastAPI · Python 3.12

> Paste this whole file into your AI coding tool. If the tool has a length limit, paste **Sections 0–3 + Appendix A first**, then paste each Build Phase (Section 12) one at a time. Do not skip Appendix A: the frontend is being built in parallel against it.

---

## 0. Your role and how to answer

You are a principal backend engineer (25+ years, logistics and marketplace dispatch systems) building the API for a hackathon project that must also survive a real NGO pilot. Rules for this job:

1. **Build real, running code.** No pseudo-code, no `TODO`, no `pass` stubs, no "implement later". If something is out of scope, say so in one line and leave a clean interface.
2. **Start by printing the repo tree**, then output files in dependency order, each with its full path as a heading.
3. **Business rules live in pure functions** (inputs in, decision out, `now` injected through a `Clock`). Databases, Redis, HTTP and WebSockets live in thin adapters. This is what makes the engines testable and is the main thing technical judges will read.
4. **Every decision is explainable.** Matching returns reasons. Dispatch returns the cost breakdown. Rejections return a machine code from Appendix A5.
5. **Everything degrades gracefully.** The system must work with no LLM key, no OSRM, no SMS provider, and no internet map service.
6. When a requirement conflicts with Appendix A, Appendix A wins.

---

## 1. The product in one minute

Restaurants, caterers, hostel messes and event hosts end the night with cooked food that is still safe but will not be safe for long. Shelters and NGOs have people to feed but find out too late. Today this runs on phone calls and WhatsApp groups.

GoldenHour is a **real-time matching and dispatch engine**: a donor posts surplus in under a minute → the system finds recipient organisations that can legally, physically and in time take it → a driver is assigned with a route that respects every expiry window → the handoff is verified → impact is counted.

**Three users** (plus a hidden ops console for demo and monitoring):

| User | What they do | What the backend must give them |
|---|---|---|
| **Donor** | Posts surplus (items, portions, diet, storage, safe-until, pickup window) | Instant feasibility preview, automatic matching, live status, OTP for pickup, receipts |
| **Recipient organisation** | Sets capacity and what it accepts, accepts or declines offers, confirms delivery | Time-aware capacity, ranked offers with countdown, live ETA of incoming food |
| **Driver** | Goes online, accepts offers, follows a multi-stop route, completes stops | Blinkit/Zomato-style dispatch, Amazon-style route optimisation, live re-planning |
| **Admin/ops** | Watches everything, injects failures | Live snapshot, simulator, chaos controls, KPIs |

**The core insight that shapes every design choice:** this is a *deadline-scheduling problem*, not a *nearest-neighbour problem*. The nearest shelter may be closed, full, pure-vegetarian, or lack cold storage. A "match" is valid only if the food can physically arrive **before it stops being safe**.

---

## 2. Non-negotiable business rules (enforced in code, tested as invariants)

| # | Rule | Where enforced |
|---|---|---|
| R1 | **Quantity ≤ available capacity.** An allocation of *p* portions to an org is legal only if *p ≤ projected available capacity at the driver's ETA*, not at posting time. | `services/capacity.py`, checked again inside the reservation transaction |
| R2 | **Diet.** `non_veg` and `egg` never go to an org that does not accept them. A driver carrying mixed diets must carry them in separate labelled containers (one container per allocation). | `matching.hard_filters` |
| R3 | **Cold chain.** `storage=cold` requires an org with cold storage **and** enough free cold units **and** a driver whose vehicle has a cold box. `storage=hot` requires a shorter transit cap. | `matching.hard_filters`, `dispatch.filters` |
| R4 | **Time window.** For every allocation: `predicted_delivery + handling_buffer ≤ deadline`, where `deadline = min(donation.safe_until, recipient_window_end)`. Never route food that cannot make it. | `services/safety.py`, re-checked at every re-plan |
| R5 | **Capacity changes over time.** Capacity is a function of time, not a number (Section 5.2). Manual updates by the recipient take effect immediately and trigger re-evaluation of pending offers. | `services/capacity.py` |
| R6 | **No double-booking.** Concurrent accepts can never oversubscribe an org or a driver. | Row locks + idempotency keys |
| R7 | **Privacy.** Recipient address and donor phone reach the driver only after the driver accepts; the driver's phone is masked for everyone else. | Serialisers |
| R8 | **Trust.** Pickup and delivery each require a 6-digit OTP. Cold-chain drops record `temp_c`. | `dispatch.stops` |
| R9 | **Never dump quietly.** If no human-consumption match is feasible, the donation moves to `fallback` (compost/animal-feed/biogas partner type) or `expired`, with a reason recorded. | `matching.cascade` |

`safe_until = min(donor_best_before, prepared_at + rule.max_hours(storage, category))`, where `food_safety_rules` is a DB table seeded with **placeholder** values (e.g. hot cooked meals 4 h, cold dairy sweets 3 h, ambient packaged 24 h) and a comment `-- VALIDATE WITH FSSAI / LOCAL FOOD-SAFETY GUIDANCE BEFORE PILOT`. Donors may shorten `safe_until`, never extend it.

---

## 3. Stack and repository layout

**Stack:** Python 3.12 · FastAPI · Pydantic v2 + pydantic-settings · SQLAlchemy 2.0 async + asyncpg · Alembic · PostgreSQL 16 + **PostGIS** (GeoAlchemy2) · Redis 7 (pub/sub, delayed jobs, distributed locks, caches) · **ARQ** workers · **OR-Tools** (routing) · SciPy `linear_sum_assignment` (assignment) · NumPy · httpx · structlog · sentry-sdk · prometheus-fastapi-instrumentator · argon2 password hashing + PyJWT · slowapi/redis rate limiting · reportlab (PDF receipts) · pytest, pytest-asyncio, **hypothesis**, httpx, ruff · Docker + docker-compose.

```
goldenhour-api/
  app/
    main.py                     # app factory, lifespan, middleware, routers
    core/  config.py security.py logging.py errors.py deps.py clock.py idempotency.py
    db/    session.py base.py models/*.py     # one model file per aggregate
    schemas/                    # Pydantic models = Appendix A shapes
    api/v1/ auth.py donations.py org.py offers.py driver.py stops.py impact.py admin.py ws.py
    services/
      safety.py                 # safe_until, deadlines, risk classification          (pure)
      capacity.py               # time-aware projection + reserve/commit/release
      matching.py               # filters, scoring, split, cascade planning           (pure core)
      routing/  osrm.py matrix_cache.py eta.py fallback_matrix.py
      dispatch/ batcher.py assignment.py insertion.py vrp.py offers.py replan.py     # pure core
      tracking.py               # GPS ingestion, ETA refresh, risk monitor
      notifications/ base.py console.py sms.py email.py
      impact.py receipts.py
      ai/       llm.py parse.py agent.py                       # all optional, feature-flagged
      sim/      seed.py driver_sim.py chaos.py
    workers/    settings.py jobs.py                            # ARQ jobs (Section 8)
    ws/         manager.py events.py
  migrations/   tests/   docker-compose.yml   Dockerfile   .env.example   Makefile   README.md   pyproject.toml
```

`docker-compose.yml` runs: `api`, `worker`, `postgres` (postgis image), `redis`, and an optional `osrm` profile. `make dev`, `make seed`, `make test`, `make load` must work. `.env.example` lists every setting with a default and a one-line comment.

---

## 4. Data model (PostgreSQL + PostGIS)

Use `geography(Point,4326)` for locations, GiST indexes on them, UUID primary keys, `created_at/updated_at` everywhere, soft-delete only where noted. Key tables and the columns that matter:

- **users** `id, role, name, phone, email, password_hash, is_active, locale ('en'|'hi')`
- **donors** `user_id, org_name, kind (restaurant|caterer|hostel_mess|event|grocer), address, geo, fssai_no?, default_pickup_window`
- **recipient_orgs** `user_id, name, address, geo, fssai_reg_no?, verified_at?, accepts_diets[], accepts_storage[], cold_max_units, service_rate_per_hour, need_level (0–1), is_open_override?, last_received_at, reliability_ewma`
- **capacity_windows** `org_id, dow?|date?, start_time, end_time, max_portions`
- **capacity_adjustments** *(ledger, append-only)* `org_id, delta_portions, reason, actor_id, at`
- **capacity_reservations** `id, org_id, allocation_id, portions, cold_units, state (held|committed|released|consumed), held_until, arrives_at`
- **donations** `id, donor_id, status, diet, storage, category, total_portions, prepared_at, best_before, safe_until, pickup_window_start/end, pickup_geo, photo_url, parse_confidence, created_at`
- **donation_items** `donation_id, name, portions, weight_kg`
- **allocations** `id, donation_id, recipient_id, portions, status, deadline, container_label, predicted_delivery, slack_seconds, score, explanation jsonb, pickup_otp_hash, dropoff_otp_hash`
- **drivers** `user_id, vehicle_type, capacity_portions, has_cold_box, status, geo, last_ping_at, accept_rate_ewma, speed_factor_ewma, service_radius_m, shift_started_at`
- **driver_locations** `driver_id, geo, speed, heading, at` (partition by day or prune to 48 h)
- **offers** `id, kind, allocation_id?, route_preview jsonb?, target_user_id, status, expires_at, score, created_at, responded_at`
- **routes** `id, driver_id, version, status, planned_distance_m, planned_duration_s, polyline, replanned_reason`
- **route_stops** `id, route_id, seq, type, allocation_id, planned_arrival, predicted_arrival, window_start, window_end, slack_seconds, status, arrived_at, completed_at, temp_c, proof_photo_url`
- **food_safety_rules** `storage, category, max_hours, transit_cap_minutes, handling_buffer_minutes`
- **impact_ledger** `allocation_id, meals, weight_kg, co2e_kg, delivered_at` (written once, on `delivered`)
- **audit_events** *(append-only)* `at, actor_id, entity, entity_id, action, before jsonb, after jsonb, request_id`
- **idempotency_keys** `key, user_id, endpoint, response jsonb, created_at`

Indexes to include explicitly: partial index on `offers(expires_at) WHERE status='pending'`; `route_stops(route_id, seq)`; `donations(status) WHERE status IN ('posted','matching','partially_matched','matched','in_transit')`; GiST on every geo column; `capacity_reservations(org_id, state)`.

---

## 5. The engines

### 5.1 Safety and time-window engine — `services/safety.py` (pure)

```
deadline(alloc)   = min(donation.safe_until, recipient_window_end) − handling_buffer(storage, category)
predicted_delivery = now + wait_for_pickup + eta(driver→pickup) + pickup_service
                        + eta(pickup→dropoff) + dropoff_service
slack_seconds     = deadline − predicted_delivery
slack_ratio       = slack_seconds / (deadline − now)
risk              = safe if slack_ratio > 0.30 · tight if 0.10–0.30 · critical if < 0.10 · infeasible if slack < 0
```
Also enforce `transit_cap_minutes` for `hot` and `cold` food (time in the vehicle between pickup and dropoff). Expose `is_feasible(...)` and `classify_risk(...)`. Property-test that risk is monotone in slack.

### 5.2 Capacity engine — time-aware, reservation-based — `services/capacity.py`

Capacity is **projected to the arrival time**, because food arrives 30–60 minutes from now and the shelter keeps serving in between.

```
in_stock_now       = portions delivered but not yet served
projected_stock(t) = max(0, in_stock_now − service_rate_per_hour × hours(t − now))
committed_before(t)= Σ portions of held(non-expired) + committed reservations arriving ≤ t
available(t)       = max_portions(window containing t) − projected_stock(t) − committed_before(t)
                     (0 if the org is closed at t or has marked itself full)
```
- Provide `snapshot(org, now)` returning the `CapacitySnapshot` of Appendix A (including the 6-hour, 15-minute projection).
- **Reserve → commit → release ledger.** When an offer is created, place a `held` reservation with `held_until = offer.expires_at`. On accept → `committed`. On decline/expiry/withdraw → `released`. On delivery confirmation → `consumed` and `in_stock += received_portions`.
- **Concurrency (R6):** inside one transaction take `pg_advisory_xact_lock(hash(org_id))`, recompute `available(arrival)`, and insert the reservation only if `portions ≤ available`; otherwise raise `CAPACITY_EXCEEDED` with `details.available`. Accept endpoints are idempotent through `Idempotency-Key`.
- **Manual updates:** `POST /org/capacity/adjust` and `/capacity/full` append to the ledger, then emit `capacity.updated` and call `matching.reevaluate_pending(org_id)` — any pending offer that no longer fits is `withdrawn` and the donation re-enters matching.
- Cold units are tracked the same way against `cold_max_units`.

### 5.3 Recipient matching — `services/matching.py`

**Step 1 — hard filters** (each rejection carries a reason code): org active and verified-or-demo · open at ETA · diet accepted (R2) · storage accepted and cold units free (R3) · `available(eta) ≥ min_chunk` · time-feasible with the best currently-available or nearest-idle-driver ETA (R4) · not on the donor's block list.

**Step 2 — score** every survivor, all sub-scores normalised to [0,1]:

| Sub-score | Meaning | Weight |
|---|---|---|
| `time` | slack ratio, clipped | 0.28 |
| `distance` | `1 − d/d_max` (road distance when OSRM is up) | 0.18 |
| `fit` | portions/available: reward ≤ 0.85, penalise near-full because capacity can change | 0.14 |
| `need` | org's declared need level and recent shortfall | 0.14 |
| `reliability` | EWMA of accepted-and-completed offers | 0.10 |
| `fairness` | log-scaled time since the org last received food (stops big NGOs hoarding) | 0.08 |
| `preference` | favourite donor, diet or cuisine preference | 0.08 |

`score = 100 × Σ wᵢ·sᵢ`. Weights come from settings. Return the top 3 reasons as `{code, label, weight}` where labels are human sentences ("38 min to spare", "Has cold storage", "Needs vegetarian food tonight").

**Step 3 — split allocation.** If no single org can take everything, solve a small transportation problem: maximise Σ score × portions subject to each org's `available(eta)`, a minimum chunk of `max(10 portions, 20 %)` to avoid silly splits, and time feasibility. Use greedy for ≤ 3 candidates and OR-Tools CP-SAT above that. Each allocation is packed into its own labelled container (`container_label`) and becomes its own delivery task — this is the "Wedding-Night Mode" (e.g. 300 plates → 3 shelters).

**Step 4 — offer cascade.**
- Offer to the top candidate (per allocation) with `ttl = clamp(0.08 × time_to_deadline, 90 s, 10 min)`.
- If `slack_ratio < 0.25`, offer in **parallel** to the top 2 with `held` reservations; first accept wins and the other is `withdrawn`.
- On decline or expiry, release the hold and offer to the next candidate. After the top 3 fail, widen radius ×1.5 once, then go to fallback (R9).
- The cascade is driven by an ARQ delayed job per offer (`offer_expiry`) so a crashed API process never loses a timer.

### 5.4 Driver dispatch — the crown jewel — `services/dispatch/`

Model it on the **publicly documented patterns** behind hyperlocal delivery and last-mile routing: (a) time-window **batching** of requests, (b) **min-cost bipartite assignment** of tasks to riders, (c) **insertion-based stacking** of new tasks onto in-flight routes, (d) **PDPTW route optimisation** (pickup-and-delivery with time windows and capacity), (e) an **ETA model** learned from actuals, and (f) **continuous re-optimisation** as GPS and traffic change. Do not claim these are any company's proprietary system; implement them as described here.

**Task definition.** One task = `pickup(donor, ready_at, latest_pickup) → dropoff(org, window_end)` for one allocation, with `portions`, `diet`, `storage`, `deadline`.

**Stage 0 — Trigger.** Run dispatch (a) every `DISPATCH_TICK_SECONDS=10` for pending tasks, and (b) *immediately* for any task whose `slack_ratio < 0.25` (priority dispatch). Use a Redis lock per task so two workers never dispatch the same task.

**Stage 1 — Candidate filter.** Drivers with `status ∈ {available, on_task}`, fresh GPS (`last_ping_at < 60 s`), inside `service_radius_m` of the pickup, `capacity_portions` sufficient along the route, `has_cold_box` if `storage=cold` (R3), not currently holding an unanswered offer. Keep the best N=15 by straight-line distance to cut work.

**Stage 2 — Cost matrix and assignment (idle drivers).** Cost in **minutes**, for driver *d* and task *t*:

```
cost(d,t) = w_pick · pickup_eta_min(d,t)
          + w_late · max(0, predicted_delivery − soft_deadline)_min          # soft_deadline = deadline − 10 % of window
          + w_acc  · (1 − p_accept(d)) · 10                                   # p_accept from accept_rate_ewma
          + w_load · workload_penalty(d)                                      # deliveries in the last 2 h, for fairness
          + w_risk · risk_term(t)                                             # small bonus for serving the most urgent first
infeasible (hard deadline miss, capacity, cold, diet-container rule) → BIG (1e6)
defaults: w_pick=1.0  w_late=8.0  w_acc=0.6  w_load=0.3  w_risk=−2.0 for critical
```
Solve with `scipy.optimize.linear_sum_assignment` on the padded matrix; discard any assignment whose cost ≥ BIG. Unassigned tasks wait for the next tick unless priority.

**Stage 3 — Stacking by insertion (drivers already on a route).** For every candidate driver with an active route, try inserting the new `(pickup p, dropoff q)` at positions `i < j` in the stop sequence. Feasibility uses **forward time slack per stop** (Savelsbergh push-forward) so each candidate check is O(1) after an O(n) precompute:
- precedence (`p` before `q`), vehicle capacity along the whole route, cold-box rule, container labels distinct;
- for **every downstream stop**, `arrival + push_forward ≤ latest_arrival` (no existing promise is broken);
- `added_detour_s ≤ MAX_DETOUR_S (600)` and detour ratio ≤ 0.35.
Pick the cheapest feasible insertion (`added_time + w_late·lateness`). Compare it to the best idle-driver assignment from Stage 2 and take the cheaper. This is the "stacked order" behaviour: two donations 1.2 km apart get one driver and one route.

**Stage 4 — Route optimisation (PDPTW) with OR-Tools.** Re-optimise a route when it gains a third stop, when a re-plan is triggered, or on demand. Build the model as:
- nodes: driver's current location (start), all pending stops, a dummy zero-cost end node (open route);
- `AddPickupAndDelivery(p, q)`, `VehicleVar(p)==VehicleVar(q)`, `CumulVar_time(p) ≤ CumulVar_time(q)`;
- **time dimension** with per-node windows `[ready_at, latest]` and service times; **capacity dimension** with `+portions` at pickup and `−portions` at dropoff;
- cold nodes forbidden for vehicles without a cold box (`SetAllowedVehiclesForIndex`);
- **optional stops via disjunction penalties**: an already-picked-up dropoff has an effectively infinite penalty; a not-yet-started pickup near expiry has a very high penalty; only far-future optional tasks have a low one — this yields graceful shedding instead of an infeasible model;
- objective: minimise total travel time + lateness penalties; `PATH_CHEAPEST_ARC` first solution, `GUIDED_LOCAL_SEARCH`, time limit `VRP_TIME_LIMIT_S=2`;
- run in a `ProcessPoolExecutor` (CPU-bound) so the event loop never blocks;
- if the solver times out without a solution, fall back to the best insertion result plus a 2-opt/Or-opt pass.
Persist the result as a new `route.version`, and store `saved_seconds_vs_previous` and `replanned_reason` (the frontend animates this).

**Stage 5 — Driver offer (Zomato-style).** Send the driver a route preview (Appendix A `Offer.kind="driver"`) with `ttl = 45 s` (25 s if priority). Decline or timeout → next best driver by cost. `p_accept` and `accept_rate_ewma` update from outcomes. If the top 3 fail, widen radius ×1.5 and allow stacking on busier drivers; if still unassigned by `slack_ratio < 0.15`, switch to **broadcast-claim** (every eligible driver sees it; first accept wins) and raise `alert.risk` to ops.

**Stage 6 — Live tracking and re-optimisation.** Drivers stream GPS over the WebSocket every 5 s. Every `RISK_MONITOR_SECONDS=15`, for each active stop recompute `predicted_arrival` with the latest position and traffic factor. On a risk transition emit `alert.risk`. If a stop becomes `critical`: (1) re-sequence with PDPTW; (2) offer that stop to a nearer driver via insertion (handoff); (3) notify the recipient/donor; (4) if still infeasible, mark the allocation `failed`, release capacity, and re-enter matching or fallback. If a driver is silent for `STALE_DRIVER_SECONDS=90`, set `stale` and warn ops; at 180 s release the driver's not-yet-started stops and re-dispatch them.

**Stage 7 — Rebalancing (optional, feature flag).** A forecast job (Section 5.10) computes per-zone expected surplus for the next hour; the driver app shows a "heat zone" hint. Keep it a read-only suggestion.

### 5.5 Travel-time and ETA service — `services/routing/`

- Primary provider: **OSRM** (`/table` for matrices, `/route` for polylines) with a Redis matrix cache keyed by coordinates rounded to 5 decimals plus a 5-minute time bucket.
- **Fallback provider** (used automatically when OSRM is unreachable or `chaos osrm_down` is active): haversine × 1.35 detour factor ÷ vehicle speed (bicycle 12, scooter 24, e_rickshaw 20, van 22 km/h).
- **ETA model:** `eta = base_time × traffic_factor(hour, weekday) × driver.speed_factor_ewma`. `traffic_factor` is a small seeded table (peak hours slower). After every completed leg, update `speed_factor_ewma = 0.8·old + 0.2·(actual/planned)` and per-place dwell times. This is honest, tiny "online learning" that you can explain in one sentence.

### 5.6 Real-time layer — `ws/`

Authenticate the socket with the JWT. Keep a per-user set of connections in memory and fan out through Redis pub/sub so multiple API replicas work. Implement the envelope and replay behaviour of Appendix A4. Backpressure: drop `driver.location` for slow consumers, never drop state events.

### 5.7 Notifications — `services/notifications/`

`NotificationService.send(user, template, data)` with adapters: console (default, logs the message), SMS (Twilio-style HTTP adapter behind an env flag), email (SMTP). Templates for `new_offer`, `offer_expiring`, `driver_assigned`, `picked_up`, `delivered`, `risk_alert`. Retries with backoff via ARQ. Never block a request on a notification.

### 5.8 Impact and receipts — `services/impact.py`, `receipts.py`

On `delivered`, write one `impact_ledger` row: `meals = received_portions`, `weight_kg = Σ item weights or portions × PORTION_KG (default 0.4)`, `co2e_kg = weight_kg × CO2E_PER_KG` (**default 2.5, placeholder — cite a source before presenting**). Serve `/impact/public` (cached), `/donor/impact`, `/org/impact`, plus KPIs `on_time_rate` and `median_time_to_match_s`. `GET /donations/{id}/receipt.pdf` renders a donor receipt (donor, recipient, items, times, OTP-verified handoff, impact) with reportlab; add `?format=csv` for CSR/ESG reporting.

### 5.9 Trust and handoff

Generate `pickup_otp` and `dropoff_otp` (6 digits, stored hashed, 4-hour validity). The donor sees the pickup OTP; the recipient sees the dropoff OTP. Completing a stop requires the OTP (constant-time compare, 5 attempts then lock for 10 min). Optionally accept a base64 photo (store to local disk/S3-compatible adapter, max 2 MB, image MIME check). Every transition writes `audit_events`.

### 5.10 AI modules — optional, feature-flagged, never on the safety path

Principle: **the LLM proposes, the rules dispose.** Every LLM output is validated by Pydantic and then re-checked by the pure engines. If the flag is off, the LLM errors, or confidence is low, the deterministic path takes over.

- `POST /donations/parse`: free text (English, Hindi, Hinglish) or a photo → structured `draft` with `confidence` and `missing[]`. Use structured output/tool-use with a strict schema. Include a deterministic regex/keyword fallback (e.g. "60 plates veg dal rice, cooked at 7 pm") so the endpoint works with no key. Ship an **eval set of 30 labelled messages** and a script that prints field-level accuracy — this number goes in the demo.
- **Dispatch agent** (`AGENT_ENABLED=false` by default): handles free-text replies from recipients/donors (e.g. "aa jaiye, par 9 baje ke baad") by calling tools `get_allocation`, `propose_window_change`, `re_evaluate`. Every tool call passes through `safety.py`; if a proposed change is infeasible the agent must reply with the nearest feasible alternative. Log every tool call to `audit_events`.
- **Surplus forecast** (optional): per-donor weekday×hour exponential smoothing on the seeded history; expose `GET /admin/forecast`. Be honest in the README that it runs on synthetic data.
- Model IDs come from env (`LLM_PARSE_MODEL`, `LLM_AGENT_MODEL`); keep the client provider-agnostic behind `LLMClient`.

---

## 6. Security, privacy, abuse

Argon2 password hashing; JWT with role claim; `require_role(...)` dependencies on every router; per-user and per-IP rate limits (auth 10/min, writes 60/min); strict CORS from `CORS_ORIGINS`; request-size caps; Pydantic validation on everything; parameterised queries only; mask phones (`+91 98•••••21`) except where R7 allows; signed short-lived URLs for uploaded photos; secrets only from env; an `audit_events` row for every state change. Small donors must not face friction: no mandatory FSSAI number at signup (add a "Verified" badge later).

## 7. Reliability rules

- All timers (offer expiry, dispatch tick, risk monitor, stale-driver check, capacity tick) are **ARQ jobs**, restart-safe and idempotent.
- Every state transition is a single DB transaction that also writes the audit row and enqueues its events **after commit** (outbox pattern or `after_commit` hook).
- Optimistic concurrency on routes: writes carry `version`; mismatches return `ROUTE_VERSION_CONFLICT`.
- Retries with jitter for OSRM/LLM/SMS; circuit breaker that flips to the fallback provider after 5 consecutive failures for 60 s.
- `/healthz` (process) and `/readyz` (DB + Redis + worker heartbeat).

## 8. Workers (ARQ)

`dispatch_tick` (10 s) · `offer_expiry` (delayed per offer) · `risk_monitor` (15 s) · `stale_driver_check` (30 s) · `capacity_tick` (60 s, refresh projections) · `notify` (on demand) · `forecast` (hourly, optional). Each job logs duration and outcome and is safe to run twice.

## 9. Simulation, seed, chaos — build this early; it is your demo

- `make seed`: a configurable city (`SEED_CENTER_LAT/LNG`, `SEED_RADIUS_KM`), **25 recipient orgs** (varied diets, cold storage, hours, capacities), **12 donors**, **10 drivers** (mixed vehicles, 3 with cold boxes), 30 days of synthetic history, and demo logins for each role.
- `POST /admin/simulate/donation` scenarios: `normal`, `rush_hour`, `wedding_night` (300 portions at 23:40).
- **Driver simulator**: moves each simulated driver along its route polyline at vehicle speed × `SIM_SPEED`, emitting real GPS pings through the same ingestion path.
- **Chaos endpoints:** `driver_drop` (driver goes silent mid-route), `org_full` (org sets full), `traffic_spike` (×2 travel time on an area), `osrm_down`. After each chaos event, the system must re-plan or reassign and every invariant must still hold. The ops console shows the resulting `sim.log` stream.

## 10. Observability and deployment

structlog JSON logs with `request_id`, `user_id`, `entity_id`; Sentry; Prometheus metrics `gh_match_latency_seconds`, `gh_dispatch_tick_seconds`, `gh_vrp_solve_seconds`, `gh_offers_total{kind,status}`, `gh_on_time_rate`, `gh_active_routes`; Dockerfile (multi-stage, non-root); `.env.example`; Alembic migrations that run on start; GitHub Actions CI (ruff + pytest); deployment notes for Render/Railway/Fly with managed Postgres (PostGIS enabled) and Redis; a keep-warm ping to avoid cold starts before the demo. Include a **k6 script** for a load scenario (100 concurrent donors posting, 30 drivers streaming GPS).

## 11. Tests and acceptance criteria

Unit tests for every pure engine, plus **hypothesis property tests** for these invariants:

1. Σ allocated portions to an org never exceeds `available(eta)`, even under 20 concurrent accepts.
2. No allocation is ever created with `slack_seconds < 0`.
3. `non_veg`/`egg` never allocated to an org that does not accept them.
4. `cold` never allocated without both org cold storage and a driver cold box.
5. In every route, each pickup precedes its dropoff and vehicle load never exceeds capacity.
6. Idempotent accept: the same key twice yields one reservation.
7. Expired or withdrawn offers cannot be accepted.

Scenario tests: (a) happy path post → match → assign → OTP pickup → OTP delivery → impact row; (b) a time-aware capacity case where an org that is full now becomes eligible at ETA because of `service_rate`; (c) wedding-night split across 3 orgs with precedence-valid routes; (d) two nearby donations stacked on one driver; (e) chaos: driver drop, org full, OSRM down, LLM off — the system recovers.

**Performance targets:** match p95 < 500 ms with 200 orgs; dispatch tick p95 < 1.5 s with 50 drivers × 30 tasks; read endpoints p95 < 150 ms; WS fan-out < 250 ms.

## 12. Build phases (implement in this order; each ends runnable)

1. **Foundation:** config, DB models + migrations, auth and roles, error format, Clock, health endpoints, docker-compose, seed.
2. **Rules core:** `safety`, `capacity`, `matching` (filters, scoring, explanations) with unit and property tests.
3. **Donation lifecycle:** post/preview/list, offers and cascade with ARQ timers, accept/decline with reservations, impact ledger.
4. **Routing and dispatch:** OSRM + fallback, matrix cache, ETA model, assignment, insertion, PDPTW, driver offers, stop lifecycle with OTP.
5. **Real-time:** WebSocket, Redis fan-out, GPS ingestion, risk monitor, re-planning, stale-driver handling.
6. **Simulation and chaos:** simulator, scenarios, chaos endpoints, admin snapshot and metrics.
7. **Extras:** parse endpoint + eval, receipts, notifications, optional agent/forecast, k6, README with an architecture diagram (Mermaid) and a "how to run the demo" section.

**Final output checklist:** repo tree · every file complete · `.env.example` · README with run steps and API docs link (`/docs`) · a `DEMO.md` listing the exact 3-minute click path · a `NOTES.md` listing placeholders that need validation (safety hours, CO₂e factor, traffic table).

---

# APPENDIX A — SHARED CONTRACT (identical in the frontend and backend prompts; never deviate from it)

Base path `/api/v1` · JSON · all timestamps ISO-8601 with offset (server stores UTC) · ids are UUID strings · distances in metres · durations in seconds · quantities in **portions** (1 portion ≈ one plated meal) with optional `weight_kg`. Every mutating POST accepts an `Idempotency-Key` header. List endpoints use cursor pagination: `?cursor=&limit=` → `{ items, next_cursor }`.

## A1. Enums

```
Role              donor | recipient | driver | admin
DietType          veg | egg | non_veg
StorageCondition  ambient | hot | cold
DonationStatus    draft | posted | matching | partially_matched | matched | in_transit | delivered | expired | fallback | cancelled
AllocationStatus  offered | accepted | driver_pending | driver_assigned | picked_up | delivered | declined | expired | cancelled | failed
OfferKind         recipient | driver
OfferStatus       pending | accepted | declined | expired | withdrawn
StopType          pickup | dropoff
StopStatus        pending | arrived | done | skipped | failed
DriverStatus      offline | available | on_task | stale
VehicleType       bicycle | scooter | e_rickshaw | van
Risk              safe | tight | critical      // slack_ratio > 0.30 | 0.10–0.30 | < 0.10
```

## A2. Core shapes (TypeScript notation)

```ts
interface GeoPoint { lat: number; lng: number; address?: string }

interface Donation {
  id: string; donor_id: string; status: DonationStatus;
  items: { name: string; portions: number; weight_kg?: number }[];
  total_portions: number; diet: DietType; storage: StorageCondition;
  prepared_at: string;
  safe_until: string;                 // server-computed cap; donor may only shorten it
  pickup_window: { start: string; end: string };
  pickup: GeoPoint; photo_url?: string; notes?: string;
  parse_confidence?: number;          // 0–1, only when created through /donations/parse
  allocations: Allocation[];
  risk: Risk; slack_seconds: number;  // live, worst allocation
  created_at: string;
}

interface Allocation {
  id: string; donation_id: string; portions: number; status: AllocationStatus;
  recipient: { id: string; name: string; geo: GeoPoint };
  container_label: string;            // "Container B" — donor packs one container per allocation
  deadline: string;                   // min(safe_until, recipient window end) − handling buffer
  predicted_delivery?: string; slack_seconds?: number; risk: Risk;
  match_explanation?: { score: number; reasons: { code: string; label: string; weight: number }[] };
  driver?: { id: string; name: string; vehicle: VehicleType; phone_masked: string };
  pickup_otp?: string;                // visible to donor only
}

interface CapacitySnapshot {
  org_id: string; as_of: string;
  max_portions: number; in_stock_portions: number; service_rate_per_hour: number;
  held_portions: number; committed_portions: number;
  cold: { max: number; used: number };
  available_now: number;
  projection: { at: string; available: number }[];      // next 6 h, 15-minute steps
  accepts: { diets: DietType[]; storage: StorageCondition[] };
  is_open: boolean; closes_at?: string;
}

interface Offer {
  id: string; kind: OfferKind; status: OfferStatus; created_at: string; expires_at: string;
  donation: { id: string; donor_name: string; diet: DietType; storage: StorageCondition;
              total_portions: number; safe_until: string; distance_m: number; items: string[] };
  // kind = recipient
  max_acceptable_portions?: number; offered_portions?: number;
  match_explanation?: Allocation["match_explanation"];
  // kind = driver
  route_preview?: { stops: Stop[]; total_distance_m: number; total_duration_s: number;
                    on_time_confidence: number; added_detour_s: number; polyline: [number, number][] };
}

interface Stop {
  id: string; seq: number; type: StopType; allocation_id: string;
  place: GeoPoint & { name: string };
  window: { start: string; end: string };
  planned_arrival: string; predicted_arrival: string;
  slack_seconds: number; risk: Risk;
  portions: number; diet: DietType; storage: StorageCondition; container_label: string;
  status: StopStatus; requires_otp: boolean;
}

interface Route {
  id: string; driver_id: string; version: number;        // bumps on every re-plan
  status: "planned" | "active" | "completed" | "cancelled";
  stops: Stop[]; polyline: [number, number][];           // [lng, lat]
  total_distance_m: number; total_duration_s: number;
  replanned_reason?: "new_stop" | "traffic" | "driver_late" | "recipient_change" | "manual";
  saved_seconds_vs_previous?: number;
}

interface ImpactSummary {
  meals_rescued: number; weight_kg: number; co2e_kg_avoided: number;
  on_time_rate: number; median_time_to_match_s: number; donations_total: number;
  series?: { date: string; meals: number }[];
}
```

## A3. Endpoints

| Area | Method + path | Purpose |
|---|---|---|
| Auth | `POST /auth/register` `{role, name, phone, email?, password, profile}` | Create account per role |
| | `POST /auth/login` · `POST /auth/refresh` · `GET /me` | JWT access (15 min) + refresh (7 d) |
| | `POST /auth/demo` `{role}` | Seeded demo login (disabled when `DEMO_MODE=false`) |
| Public | `GET /impact/public` | Landing counters (cached 30 s) |
| | `GET /time` | Server time, for clock-skew correction |
| Donor | `POST /donations/parse` `{text? , photo_base64?}` → `{draft, confidence, missing[]}` | Free text or photo → structured draft |
| | `POST /donations/preview` `{draft}` → `{feasible_recipients: n, best: {...}, warnings[]}` | Live feasibility while typing |
| | `POST /donations` | Post surplus → status `posted`, matching starts instantly |
| | `GET /donations` · `GET /donations/{id}` · `POST /donations/{id}/cancel` | Own donations, timeline, cancel |
| | `POST /donations/repeat/{id}` | One-tap repeat of a past donation |
| | `GET /donations/{id}/receipt.pdf` · `GET /donor/impact` | Tax/CSR receipt and personal impact |
| Recipient | `GET /org/profile` · `PUT /org/profile` | Name, geo, FSSAI number, accepted diets/storage, cold capacity |
| | `GET /org/capacity` → `CapacitySnapshot` | Live capacity + projection |
| | `PUT /org/capacity/windows` | Open hours and `max_portions` per window |
| | `POST /org/capacity/adjust` `{delta_portions, reason}` · `POST /org/capacity/full` `{is_full}` | Real-time manual updates |
| | `GET /offers?status=pending` | Recipient offers |
| | `POST /offers/{id}/accept` `{portions?}` · `POST /offers/{id}/decline` `{reason_code}` | Partial accept allowed |
| | `GET /org/incoming` | Allocations en route, with live ETA |
| | `POST /allocations/{id}/confirm-delivery` `{otp, received_portions, photo_base64?, temp_c?}` | Proof of delivery |
| | `GET /org/impact` | Org impact |
| Driver | `POST /driver/shift` `{status: "available"\|"offline"}` · `PUT /driver/profile` | Go online/offline, vehicle, capacity, cold box |
| | `POST /driver/location` `{lat,lng,speed,heading,ts}` | HTTP fallback for GPS pings (WS preferred) |
| | `GET /driver/offers` · `POST /offers/{id}/accept` · `POST /offers/{id}/decline` | Driver offers use the same offer endpoints |
| | `GET /driver/route` → `Route \| null` | Current route |
| | `POST /stops/{id}/arrive` · `POST /stops/{id}/complete` `{otp?, photo_base64?, temp_c?}` · `POST /stops/{id}/issue` `{code, note?}` | Stop lifecycle; issue codes: `food_not_ready`, `recipient_closed`, `vehicle_issue`, `unsafe_food`, `other` |
| | `GET /driver/stats` · `GET /driver/history` | Earnings-free impact stats for volunteers |
| Admin | `GET /admin/live` | Snapshot of donors, orgs, drivers, routes for the ops map |
| | `POST /admin/simulate/donation` `{count, scenario}` scenarios: `normal`, `wedding_night`, `rush_hour` | Fire test donations |
| | `POST /admin/chaos` `{kind: "driver_drop"\|"org_full"\|"traffic_spike"\|"osrm_down", target_id?}` | Failure injection |
| | `GET /admin/metrics` | Dispatch KPIs |
| Realtime | `WS /ws?token=` | See A4 |

## A4. WebSocket envelope

```ts
{ event: string; seq: number; ts: string; data: any }   // seq is monotonically increasing per connection
```
Server → client: `offer.created`, `offer.expired`, `offer.withdrawn`, `donation.updated`, `allocation.updated`, `capacity.updated`, `route.updated`, `driver.location`, `alert.risk`, `impact.tick`, `sim.log`.
Client → server: `driver.location {lat,lng,speed,heading,ts}`, `ping`. On reconnect the client sends `?last_seq=` and the server replays missed events (up to 200) or tells the client to refetch.
Users receive only events for their own role and entities; `admin` receives everything.

## A5. Errors

```json
{ "error": { "code": "CAPACITY_EXCEEDED", "message": "Asha Shelter can take 40 more portions right now.", "details": { "available": 40 }, "request_id": "..." } }
```
Codes: `VALIDATION_ERROR`, `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `CAPACITY_EXCEEDED`, `DIET_MISMATCH`, `COLD_CHAIN_UNAVAILABLE`, `WINDOW_INFEASIBLE`, `OFFER_EXPIRED`, `OFFER_NOT_PENDING`, `OTP_INVALID`, `ROUTE_VERSION_CONFLICT`, `DRIVER_CAPACITY_EXCEEDED`, `RATE_LIMITED`, `INTERNAL`. Messages are plain-language sentences a shelter volunteer can act on; never expose stack traces.
