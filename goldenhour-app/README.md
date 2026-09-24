# ⏳ GoldenHour — Algorithmic Food Rescue Platform (Jaipur Metro)

> **Matches surplus food from commercial kitchens to shelters before it spoils, dispatching drivers on zero-detour routes.**

Designed for the **Rajasthan Hackathon 2026**, pixel-ported from the high-fidelity OptiMeal reference design system, and localized for the **Jaipur metropolitan food rescue corridor** (C-Scheme, MI Road, Tonk Road, Malviya Nagar, and Jagatpura).

---

## 🌟 The 9 Completed Phases

| Phase | Component / Module | Status | Highlights |
|---|---|:---:|---|
| **Phase 1** | **Design System & Foundations** | ✅ Complete | Exact token port (`tokens.css`, `base.css`, `motion.css`), DM Sans + Instrument Serif fonts, 31×18 pill toggle with halo glow, LiveBadges, MetricCards with number tweening, native dialog modals. |
| **Phase 2** | **Landing Page (12 Sections)** | ✅ Complete | 3-way role switcher (Donor / Shelter / Driver), animated staggered copy, floating live cards, demand card, Cost of Delay breakdown, interactive role previews, weekly bar sparklines, FAQ accordion, PathBox modal. |
| **Phase 3** | **Data Layer & Jaipur Mock Engine** | ✅ Complete | MSW service worker simulating all Appendix A endpoints, realistic Jaipur seed dataset, mock WebSocket bus broadcasting telemetry, server-time synchronization with clock offset. |
| **Phase 4** | **Domain Components** | ✅ Complete | `CountdownRing` with 3-tier risk threshold colors, `SlackBar`, `DietBadge` (Veg/Egg/Non-veg), `StorageBadge` (Hot/Ambient/Cold), `StatusStepper`, `CapacityGauge`, `CapacityTimeline`, `RouteMap`, `PhoneFrame`. |
| **Phase 5** | **Donor App (`/donor`)** | ✅ Complete | Metric overview, NLP Quick Post parser ("40 veg meals at C-Scheme..."), instant feasibility checker, safe-until slider, photo simulation, live donation detail with handover OTP. |
| **Phase 6** | **Shelter / Recipient App (`/org`)** | ✅ Complete | Tablet-first layout, real-time Capacity Gauge, instant intake pause switch, pending offer cards with 60s accept timer, 6-hour projection timeline, driver gate OTP verification. |
| **Phase 7** | **Driver App (`/driver`)** | ✅ Complete | Mobile-first thumb zone, online/offline toggle, 45s countdown Offer Sheet, turn-by-turn stop sequence manifest, OTP verification input, completion celebration screen, offline queue & throttled GPS tracker. |
| **Phase 8** | **Ops Live Console (`/ops`)** | ✅ Complete | Full-height interactive Jaipur corridor map, live KPI tickers, streaming WebSocket event log, scenario switcher (Normal, Wedding Surge, Rush Hour), chaos injection triggers (Driver Drop, Shelter Full, Traffic Jam). |
| **Phase 9** | **Polish, i18n & Production Build** | ✅ Complete | English & Hindi (हिंदी) translations, PWA/offline readiness, clean `npm run build` production bundling with zero TypeScript errors. |

---

## 🚀 Instant Demo Logins (Jaipur Corridor)

Open the app at `http://localhost:5173` and click **"Sign In"** or use the quick role pills in the header:

1. **🍲 Donor Portal:** `Spice Route Kitchen` (C-Scheme, Ashok Nagar, Jaipur)
2. **🏠 Shelter Hub:** `Asha Shelter Foundation` (Sector 4, Malviya Nagar, Jaipur)
3. **🛵 Driver Cockpit:** `Rajesh Kumar` (E-Rickshaw #RJ-14-ER-9821, MI Road)
4. **⚡ Ops Control Console:** Central Jaipur Dispatch Center (All live corridors)

---

## 🔌 Connecting Your Friend's Backend

GoldenHour is built with a dual-mode data layer:

### 1. Mock Mode (Default)
Runs 100% in the browser using Mock Service Worker (MSW) and an in-memory WebSocket event simulator. No backend installation required.
```env
VITE_USE_MOCKS=true
```

### 2. Live Backend Mode
When your friend launches the backend service:
1. Open `.env` in `goldenhour-app`:
   ```env
   VITE_USE_MOCKS=false
   VITE_API_URL=http://localhost:8000/api
   VITE_WS_URL=ws://localhost:8000/ws
   ```
2. Restart the frontend dev server (`npm run dev`).
3. GoldenHour immediately bypasses MSW and speaks directly to your friend's API endpoints using standard JWT bearer headers and the Appendix A JSON schema!

### Appendix A Endpoints Supported:
- `GET /api/time` — Clock synchronization
- `POST /api/auth/login` & `/api/auth/refresh` — Authentication
- `GET /api/donations` & `POST /api/donations` — Active donations
- `POST /api/donations/parse` — AI Natural Language Quick Post
- `POST /api/donations/feasibility` — Intake feasibility check
- `GET /api/offers` & `POST /api/offers/:id/accept` — Recipient / Driver offers
- `GET /api/capacity/current` & `POST /api/capacity` — Shelter capacity & policies
- `GET /api/routes/active` & `POST /api/routes/:id/stops/:stop_id/done` — Driver navigation
- `GET /api/admin/live` & `POST /api/admin/simulate` & `POST /api/admin/chaos` — Ops telemetry

---

## 🛠 Quick Start

```bash
# 1. Navigate to directory
cd d:/AMI-HACK/goldenhour-app

# 2. Run local development server
npm run dev

# 3. Build for production
npm run build
```

Open your browser at `http://localhost:5173`.
