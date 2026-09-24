# FRONTEND PROMPT — GoldenHour (working name) · React + TypeScript

> **Attach the file `OptiMeal_hero_interactive_updated.html` together with this prompt.** It is the visual source of truth. If your tool has a length limit, paste **Sections 0–4 + Appendix A first**, attach the HTML, then paste each Build Phase (Section 13) one at a time.

---

## 0. Your role and how to answer

You are a principal product designer-engineer (25+ years, consumer and logistics apps). Build a complete, production-quality web app for a food-rescue platform, matching the attached HTML's look and motion **exactly** while replacing all of its content.

Rules:

1. **Real, working code only.** No lorem ipsum, no `TODO`, no placeholder components. Every screen listed below must exist and run.
2. **First print the file tree**, then output files in dependency order with full paths.
3. **Design plan before code:** write a 10-line token summary (colors, type, radii, shadows, easing) copied from the attached HTML and confirm every value below matches it. If the HTML disagrees with this prompt, **the HTML wins**.
4. **Copy the system, not the content.** Reuse the HTML's tokens, components, section skeleton, hover physics and animation timings. Never reuse the words "OptiMeal", "student", "attendance", "manager" or "demand prediction" ("mess" is allowed only as the donor type "hostel mess"). Replace all other copy with the copy in this prompt.
5. **The app must run with no backend** (mock mode, Section 11) and switch to the real API by changing one env variable. The API is defined in Appendix A; do not invent endpoints.
6. Spend visual boldness in **one place**: the countdown ring (Section 4). Everything else stays as quiet and disciplined as the reference.

---

## 1. Product in one minute

Restaurants, caterers, hostel messes and event hosts end the night with safe-to-eat food that will spoil within hours. Shelters and NGOs have people to feed but hear about it too late. **GoldenHour** matches the surplus to a shelter that can take it *in time*, dispatches a driver on an optimised multi-stop route, verifies the handoff, and counts the impact.

**Three users, three experiences** (plus a hidden ops console for demos):

| User | Device | Job to be done | Emotional tone |
|---|---|---|---|
| **Donor** (restaurant, caterer, hostel mess, event host) | Phone or laptop | Post surplus in under 60 seconds and know it is handled | Relief, control |
| **Recipient organisation** (shelter, NGO, community kitchen) | Tablet or phone, often non-technical staff | Know what is coming, accept what fits, keep capacity honest | Calm, clarity |
| **Driver** (volunteer or gig) | **Phone only**, one hand, outdoors | Accept a job, follow a route, complete stops on time | Focus, speed |
| **Ops** (hidden `/ops`) | Laptop / projector | Watch the whole system, inject failures live | Command room |

The one idea to make visible everywhere: **every donation has a countdown**, and the system's job is to turn that clock into a delivered meal.

---

## 2. Design system — extracted from the attached HTML

### 2.1 Tokens (put these in `src/styles/tokens.css`, exactly)

```css
:root{
  --ink:#17221b;  --deep:#173d2a;  --green:#8fd35a;  --green-dark:#69a83f;
  --soft:#e6f1df; --paper:#f7f6f1; --white:#fff;     --cream:#f1e8d2;
  --muted:#68736b; --line:#dce5da; --red:#d96b4b;    --blue:#8db8c9;
  --blue-text:#4d869d; --blue-tint:#f1f7fa; --warn-tint:#fff5f1; --analytics-bg:#f2f7f0;
  --on-dark-muted:#cbd9ce; --bar-idle:#c8dfbc; --peach:#f0a083; --peach-soft:#f5b19d;
  --ease:cubic-bezier(.16,1,.3,1);
  --shadow:0 25px 70px rgba(23,61,42,.12);
  --shadow-soft:0 14px 38px rgba(23,61,42,.08);
}
```

**Semantic mapping (new, uses only palette colors):** `safe` → `--green` fill with `--deep` text · `tight` → `--peach` · `critical` → `--red` · info/route/ETA → `--blue-text` · neutral surfaces → `--white` on `--paper` · success surfaces → `--soft`. Never put `--green` as body-text color on white (low contrast); use it for fills and `--deep` for text on it.

### 2.2 Typography

- **DM Sans** 400/500/600/700 for everything; **Instrument Serif italic** only inside `h1 em` at `1.07em`, colored `--deep` (one italic phrase per hero headline).
- Body `16px/1.55`. `h1` `clamp(3.5rem,6.3vw,6.25rem)`, line-height `.9`, letter-spacing `-.075em`. `h2` `clamp(2.4rem,4.8vw,4.5rem)`, line-height `.95`, letter-spacing `-.065em`. Big metric numbers `1.75–1.8rem`, weight 700, letter-spacing `-.07em`.
- Eyebrow: `.72rem`, 700, letter-spacing `.15em`, uppercase, color `--deep` (`--green` on dark). Use eyebrows only where they name a real category (a role, a section), not on every block.
- Small labels `.64–.72rem` in `--muted`.

### 2.3 Shape, spacing, elevation

Container `min(1160px, 100% − 40px)`. Header height 78 px, sticky, `background:#f7f6f1e8; backdrop-filter:blur(15px)`, border and shadow appear after scroll. Radii: buttons `999px`; big cards `22–24px`; small cards/rows `12–14px`; logo mark `11px 11px 11px 4px`. Cards: white, `1px solid var(--line)`, `--shadow` for floating panels, `--shadow-soft` for inline ones. Buttons: min-height 46 px; primary = `--green` with `0 9px 22px #8fd35a40`; outline = 1 px `--line`; hover lifts `-3px`, arrow glyph nudges `+4px`.

### 2.4 Motion vocabulary — reuse these, add nothing louder

| Motion | Spec (from the HTML) | Use it for |
|---|---|---|
| Easing | `cubic-bezier(.16,1,.3,1)` everywhere | All transitions |
| Hero entrance | Staggered `copyIn` (eyebrow 0 ms → h1 100 → p 280 → buttons 400 → demand card 520 → trust 680) | Landing hero only |
| Section reveal | `translateY(28px)` + fade, 0.8 s, via IntersectionObserver, `data-reveal` | Landing sections |
| Bars grow | `scaleY(0→1)` from bottom, 0.7 s, 70–80 ms stagger | All bar charts |
| Live dot | `livePulse` 2 s box-shadow ring | Every "live" badge |
| Signal path | Dashed `stroke-dasharray:6 8` draws in over 1.3 s, nodes pulse | **Route lines on maps and the landing hero** |
| Floating cards | Slow idle float + pointer-parallax via `data-depth` | Landing hero cards only |
| Number tween | Smooth numeric interpolation (~600 ms) | Every changing metric and capacity number |
| Button ripple + magnetic hover | Pointer-based, disabled on `pointer:coarse` | Primary buttons (desktop) |
| Toggle | 31×18 pill, knob slides with `--ease`, halo when on | On/off controls |
| Reduced motion | `prefers-reduced-motion` kills all of the above except state changes | Always |

### 2.5 Reference-to-new mapping (the HTML's blocks become these)

| HTML block | Becomes |
|---|---|
| Header + scroll progress + mobile drawer | Same, with links: Product · The clock · How it works · Donors · Shelters · Drivers · Impact |
| Hero with role-message switch (Mess / Student) | **Three-way switch: Donor / Shelter / Driver** swapping eyebrow, `h1`, sub-copy |
| `path-box` "What brings you here?" and `choice-modal` | Three paths: "I have surplus food" · "We feed people" · "I can drive" |
| `hero-demand` card (attendance → recommendation + bars) | "Tonight's rescue": portions posted → portions delivered before expiry |
| Floating `dashboard` | "Live rescue board" (Section 5) |
| Floating `impact` chip | "1,240 meals rescued" (illustrative) |
| Circular `food-photo` | Keep, with a real food photo (use an Unsplash URL of plated Indian meals) |
| Floating `student-card` with toggles | **Driver offer card** with countdown and an Accept toggle |
| `.dark` compare section with counters | "Most surplus fails because of the clock" |
| `waste-story` (image + points) | "Every minute of delay costs a meal" |
| `flow-card` ×4 | Post → Match → Dispatch → Delivered |
| `.phone` mockup section | Donor Quick Post and Driver route phones |
| `.manager-ui` panel | Shelter capacity panel |
| `pipeline` (inputs → engine → output) | Inputs: time window · capacity now and at arrival · diet and cold chain → "Dispatch engine" → "Best match + route" |
| `analytics` charts and metric cards | Impact view |
| FAQ accordion, CTA box, footer | Same structure, new copy |
| `.section-number` big background numerals | Keep for the landing only (the sections are a real sequence) |

---

## 3. Tech stack and structure

**React 18 + Vite + TypeScript (strict)**, React Router 6, TanStack Query 5, Zustand (session/UI), react-hook-form + zod, **MapLibre GL JS** (light, low-saturation basemap; style URL from `VITE_MAP_STYLE_URL`), i18next (**English + Hindi**), date-fns, vite-plugin-pwa, **MSW** (mock API), Vitest + Testing Library, Playwright (one e2e for the demo path). Styling: **plain CSS with CSS Modules** ported from the HTML so fidelity is exact. If your tool forces Tailwind, put every token above in `tailwind.config` and keep the same class-level visuals.

```
src/
  styles/        tokens.css base.css motion.css
  lib/           api.ts (fetch + auth + idempotency) ws.ts (reconnecting socket, seq replay)
                 clock.ts (server-time offset) format.ts geo.ts i18n/ en.json hi.json
  store/         session.ts ui.ts
  hooks/         useNow.ts useLive.ts useCountUp.ts useReveal.ts useParallax.ts usePointerFx.ts
  components/    ui/ (Button, Toggle, LiveBadge, MetricCard, Modal, PathBox, Toast, Skeleton, EmptyState, FAQ)
                 domain/ (CountdownRing, SlackBar, DietBadge, StorageBadge, StatusStepper, OfferCard,
                          StopList, CapacityGauge, CapacityTimeline, MiniBars, SignalLine, RouteMap, PhoneFrame)
  features/      landing/ auth/ donor/ org/ driver/ ops/
  mocks/         handlers.ts data.ts ws.ts scenarios.ts
  routes.tsx     App.tsx main.tsx
```

Routes: `/` landing · `/auth` · `/donor/*` · `/org/*` · `/driver/*` · `/ops` (admin only) · guards by `role` from `/me`. Each role bundle is lazy-loaded.

---

## 4. The signature component: `CountdownRing`

The one memorable element. An SVG ring that **drains in real time** toward the safe-until deadline.

- Props: `deadline`, `startedAt`, `size` (`sm` 44 / `md` 88 / `lg` 168), `label`.
- Center: `mm:ss` (or `h:mm` above one hour) in DM Sans 700 with tight tracking; below it a `.64rem` muted label like "safe until 9:42 pm".
- Color follows `Risk`: `safe` → `--green` stroke on `--soft` track · `tight` → `--peach` · `critical` → `--red` plus a slow pulse in the final 10 %.
- Smooth drain using `stroke-dashoffset` with `transition: stroke-dashoffset 1s linear`, driven by **one shared `useNow()` ticker** (never a timer per component). Uses server-time offset from `GET /time` so shelters and drivers see the same clock.
- Accessibility: `role="timer"`, an `aria-label` such as "42 minutes left to deliver", not announced every second; announce only risk changes through a polite live region.
- Appears on donation cards, offer cards, stop cards, the landing dashboard and the ops board.

Companion `SlackBar`: a thin bar showing planned slack vs window (`--soft` track, fill by risk), with text "38 min to spare".

Other domain components to build: `DietBadge` (veg = green dot, egg = cream, non-veg = red dot — always icon + text, never color alone), `StorageBadge` (Ambient / Hot / Cold with small glyph), `StatusStepper` (posted → matched → driver assigned → picked up → delivered, current step pulses), `CapacityGauge` (arc or horizontal bar with tweened number), `CapacityTimeline` (6-hour projection as bars using the HTML's `mini-bars` style, "now" marker), `SignalLine` (the HTML's dashed animated path used as the route line and as a decorative motif), `RouteMap` (MapLibre wrapper with custom markers: donor = green tile, shelter = deep-green tile, driver = pulsing blue dot; route drawn with the dashed signal style).

---

## 5. Landing page — section by section

Follow the HTML's section order and rhythm. All numbers on the landing are **illustrative**; label them exactly like the HTML does ("Illustrative interface example") and pull `GET /impact/public` when available.

**Header:** logo mark (same 34 px shape, clock-ring glyph instead of ⌁) + wordmark; links; "Log in" and primary "Choose your path".

**Hero** — role switch with three panels:
- *Donor* — eyebrow FOR DONORS · h1 "Post the surplus. <em>We race the clock.</em>" · p "Tell us what's left in under a minute. GoldenHour finds a shelter that can take it in time, and a driver to carry it."
- *Shelter* — FOR SHELTERS AND NGOs · "Know what's coming, <em>before it arrives.</em>" · "See safe, diet-matched donations with time to spare. Accept what fits your capacity and track every pickup live."
- *Driver* — FOR DRIVERS · "One clean route. <em>Every stop on time.</em>" · "Get stacked pickups and drop-offs planned around expiry windows, with live re-routing when things change."
- Shared paragraph: "GoldenHour turns surplus food into a live, time-boxed match, so more of it reaches a plate before it spoils."
- Buttons: primary "See a rescue in action →", outline "Choose your path". Trust row: Diet and cold-chain aware · Time-window safe · Live tracking.
- `hero-demand` card "Tonight's rescue" · "Live": *Portions posted* **214** → *Delivered before expiry* **198** (blue variant); 8 signal bars; caption "Mon … *Most matches land in minutes.* … Today".
- Floating **Live rescue board** (dash-grid): *Portions in play* 214 · *On time* 198 (blue) · *At risk* 3 (warning variant, sub "Being re-routed") · *Avg time to match* 3m 40s · wide *Rescued this week* mini-bars · wide recommend row "Best match now — **Asha Shelter · 2.1 km · 38 min to spare**".
- Floating impact chip: "**1,240 meals** rescued (illustrative)". Circular food photo. Floating **driver offer card** replacing the student card: title "New pickup", rows "Pickup · Spice Route Kitchen" and "Drop · Asha Shelter", a small `CountdownRing sm` at 0:38, and a real **Accept** toggle that, when toggled, shows "Route updated · +1 stop" with a route-line draw animation. Keep the pointer parallax, signal line and node pulses.

**Section 01 (dark) — the problem:** eyebrow THE PROBLEM · h2 "Most surplus food fails because of the clock." · p "The food is safe. The people are hungry. What's missing is a match that lands before the window closes." Compare cards with counters: *Left at closing time* **470** portions (peach) vs *Reached a plate before expiry* **398** portions (green); pill "72 still lost — sent to compost partners".

**Section 02 — waste story:** image of leftover food + card "What one late match costs" counter 31 portions; eyebrow THE COST OF DELAY · h2 "Every minute of delay <em>costs a meal.</em>"; three points: "Food has a 2–6 hour window" ("Most surplus is safe to donate for only a few hours."), "Phone calls and group chats don't scale" ("Coordination breaks down past a handful of relationships."), "Impact should leave a paper trail" ("Receipts and reports for donors, funders and regulators."); buttons "I have surplus food" / "We feed people".

**Section 03 — how it works (flow-cards):** 01 *Post surplus* "Add items, diet, storage and safe-until time. Under a minute." · 02 *Match in time* "We filter by diet, cold chain, capacity at arrival and time window, then rank." · 03 *Dispatch a driver* "Nearby drivers get one clean route, stacked when it saves time." · 04 *Delivered and counted* "OTP-verified handoff, live status, and an impact record."

**Section 04 — donors:** phone mockup "Quick post": free-text field "60 plates veg dal-rice, cooked 7 pm", parsed chips (Veg · Hot · 60 portions), safe-until "9:30 pm", feasibility "3 shelters can take this in time", primary "Post surplus". Features: "Post in seconds", "Repeat last donation", "Get a receipt automatically".

**Section 05 — shelters:** capacity panel (the `manager-ui` layout): *Free now* 84 · *At 8 pm* 120 · *Cold space* 12 · wide capacity projection line. Features: "Capacity that updates itself", "Accept part of a donation", "Know exactly when it arrives".

**Section 06 — drivers:** second phone mockup with route: 3 stops, per-stop spare-time bars. Features: "Stacked pickups, one route", "Live re-routing", "Simple proof of handoff".

**Pipeline section:** eyebrow THE DECISION PIPELINE · h2 "Turn scattered constraints into one match and one route." Inputs: *Time window · Expiry* · *Capacity · Now and at arrival* · *Diet and cold chain · Veg, egg, non-veg*. Engine "Dispatch engine — Calculating best match". Output "Best match" `Asha Shelter` with "38 min to spare" and a confidence track.

**Impact view:** eyebrow IMPACT VIEW · h2 "See what faster matching makes possible." · line chart *Meals rescued per week* + metric cards *Median time to match* 3m 40s · *On-time delivery* 94% · *CO₂e avoided (estimate)* 1.9 t — all labelled "Illustrative example".

**FAQ (4):** How does GoldenHour keep food safe? ("Every donation gets a safe-until time. We only match food that can arrive before it, and we never route food past it.") · What if a shelter can't take it? ("Offers move to the next best shelter automatically. If none can, it goes to a compost or animal-feed partner.") · Do I need to install an app? ("No. It's a web app you can add to your home screen.") · What if a driver is running late? ("We re-plan the route, hand the stop to a closer driver, or alert everyone involved.")

**CTA:** "Every rescued plate starts with one post." buttons "I have surplus food" · "We feed people" · "I can drive". **Footer:** same structure as the HTML, tagline "Smarter food rescue for donors, shelters, drivers and the planet."

---

## 6. Auth, onboarding and demo access

- `/auth`: role chooser modal (the HTML's `choice-modal`, three options), then login or register. Big **"Try the demo as Donor / Shelter / Driver"** buttons calling `POST /auth/demo` — essential for judges.
- **Donor signup:** business name, type, pin-drop address on the map, phone. **Recipient signup:** organisation name, address, phone, optional FSSAI number ("Adds a Verified badge"), then a **3-step wizard**: (1) capacity and service rate, (2) accepted diets and cold storage with toggles, (3) opening hours. **Driver signup:** name, phone, vehicle type, load capacity in portions, cold box toggle, service radius.
- Validation errors are inline, specific and never apologetic ("Add a pickup address so drivers can find you.").

---

## 7. Donor app (`/donor`)

Shell: sticky header (wordmark, live badge, language switch EN/हिं, avatar), page content max 1160 px, on mobile a bottom tab bar (Home · Post · Impact).

1. **Home.** Row of `MetricCard`s (Posted today, Delivered, Meals rescued, CO₂e avoided — tweened). Below, **active donations** as cards: title, `DietBadge`/`StorageBadge`, portions, `StatusStepper`, `CountdownRing md`, `SlackBar`. Empty state: "Nothing posted tonight. Post surplus and we'll start the clock." with primary "Post surplus".
2. **Quick Post** (the hero flow; under 60 seconds).
   - Top: one large text box — "Describe what's left" (accepts English/Hindi/Hinglish) with a mic button (Web Speech API where supported) and a camera button. On blur or pause, call `POST /donations/parse`, animate parsed values into editable chips; low-confidence fields get a peach outline and a question ("How many portions?").
   - Fields: items (name + portions), **diet segmented control** (Veg · Egg · Non-veg), **storage segmented control** (Ambient · Hot · Cold), prepared time (default now), **safe-until** slider whose maximum is the server rule with helper "Max 4 h for hot meals", pickup window (start/end), pickup address (saved default; map pin), optional photo and notes.
   - **Live feasibility strip** (debounced `POST /donations/preview`): "3 shelters can take this in time · best match 38 min to spare". Warnings inline: "No cold-storage shelter is open in your area. Change storage or safe-until."
   - "Repeat last donation" chip at top. Submit "Post surplus". Success state: the new card slides in with `CountdownRing lg` starting and the message "Matching now."
3. **Donation detail.** Header with `CountdownRing lg` and status. Timeline (`StatusStepper`). For split donations, a list of allocations: "Container A → Asha Shelter · 40 portions", each with its own status, driver, ETA and **"Why this shelter?"** popover rendering `match_explanation.reasons` as chips. **Pickup OTP** shown large with copy button and the text "Give this code to the driver." Live `RouteMap` showing driver approach. Actions: Cancel (confirm modal), Download receipt.
4. **Impact.** Charts in the HTML's chart style; totals; receipt list with PDF/CSV buttons.

---

## 8. Recipient app (`/org`)

Tablet-first, big targets, plain words.

1. **Home.** Left: **CapacityGauge** "Free now 84 of 200" with tween, plus `CapacityTimeline` "Free space over the next 6 hours". Right: **Offers** (top priority) and **Incoming**.
   - **OfferCard:** donor name, items, `DietBadge`, `StorageBadge`, portions, distance, `CountdownRing sm` showing the *offer* timer, `SlackBar` for delivery time to spare, and **"Why you?"** reasons. A stepper lets them **accept part** ("Take 40 of 60"), capped at `max_acceptable_portions`; primary "Accept", outline "Not now" opens reason chips (`full`, `closed`, `diet`, `no_cold`, `other`). New offers arrive with the `impactIn` motion and an audible-optional chime; the list is an `aria-live="polite"` region.
   - **Incoming:** each allocation with driver name, vehicle, live ETA, `StatusStepper`, and a big dropoff **OTP** to read to the driver. Button "Confirm delivery" opens a sheet: OTP input, received portions (defaults to expected), optional photo, temperature (cold only).
2. **Capacity manager.** The trust-building screen.
   - **Toggles** (reuse `.toggle`): "We're open tonight", "We're full right now" (immediate; shows a confirm toast "Paused — no new offers"), Accept: Veg / Egg / Non-veg, Cold storage available.
   - **Steppers** for `max_portions` and `service_rate_per_hour`, plus **quick adjust** buttons "−10 / +10" with a reason picker ("Served early", "Walk-in donation") calling `POST /org/capacity/adjust`.
   - **Opening hours editor** (`PUT /org/capacity/windows`): a day/time list; changes preview their effect on the 6-hour projection instantly.
   - Any change triggers `capacity.updated` on other tabs and animates the gauge.
3. **History and impact:** received donations, meals served, reliability score with an explanation of how it affects ranking.

---

## 9. Driver app (`/driver`) — mobile-first PWA, one-handed, sunlight-readable

Design for a thumb: primary actions at the bottom, ≥ 56 px tall, high contrast (`--ink` text on `--white`/`--soft`). No hover-only UI. Respect safe-area insets.

1. **Home.** Huge online/offline toggle ("Go online") with the HTML's toggle physics. When online: status "Waiting for a pickup", today's stats (stops, km, meals), and an optional **heat-zone hint** ("Busy soon near MG Road"). Warn if GPS permission is missing.
2. **Offer sheet** (full-screen bottom sheet, vibrates if supported): `CountdownRing lg` for the **accept timer** (45 s), mini `RouteMap`, stops list (pickup → drop), total distance and time, "**On-time confidence 91%**", "+6 min detour" if stacked, portions with `DietBadge`/`StorageBadge`, and two buttons at the bottom: **Accept** (primary, large) and **Decline** with reasons.
3. **Active route.** Top: current stop card with `CountdownRing md` to that stop's window end and a `SlackBar`. Middle: `RouteMap` with the dashed signal route and pulsing driver dot. Bottom sheet: ordered **StopList** (numbered, type icon, place name, window, spare time chip colored by `Risk`, portions, container label like "Container B — Veg, Hot"). Primary CTA changes by state: **Navigate** (opens `https://www.google.com/maps/dir/?api=1&destination=lat,lng`) → **I've arrived** → **Enter OTP** (6 large digit boxes, numeric keypad) → **Complete** (optional photo, temperature for cold). "Report a problem" chips: food not ready · recipient closed · vehicle issue · unsafe food.
4. **Re-plan moment.** When `route.updated` arrives, animate the new dashed line drawing in, flash the changed stop order, and show a toast "Route updated — saves 6 min" (from `saved_seconds_vs_previous`) with the reason in plain words ("A closer stop was added").
5. **Done screen:** meals delivered, a soft confetti-free confirmation (a green ring filling), next offer prompt.
6. **Offline resilience:** queue stop completions and GPS pings while offline, retry on reconnect, show a "Reconnecting…" banner; keep the last route cached by the service worker.

GPS: use `navigator.geolocation.watchPosition` (high accuracy) and send `driver.location` every 5 s over the socket (HTTP fallback), throttled when the screen is idle.

---

## 10. Ops console (`/ops`, hidden, admin only) — your demo weapon

Laptop layout on `--paper`: left a full-height `RouteMap` showing all donors, shelters, drivers and routes (colors as in Section 4); right a column of KPI `MetricCard`s (on-time rate, median time to match, active routes, at-risk count) and a **live event log** from `sim.log`/`alert.risk` (newest on top, fades in).
Control bar: **Simulate** (`Normal` · `Rush hour` · `Wedding night`), **Chaos** (`Driver drops out` · `Shelter says full` · `Traffic spike` · `Routing service down`), with a `SIM_SPEED` selector. Every action shows its effect in the log within seconds, which is the proof of reliability for judges.

---

## 11. Data layer, real-time, mock mode

- `lib/api.ts`: typed fetch wrapper with bearer token, refresh-on-401, `Idempotency-Key` on POSTs, error normalisation to the A5 shape; show `error.message` verbatim in toasts.
- **TanStack Query** for reads; **WebSocket events update the cache** (`setQueryData`/`invalidateQueries`) so screens change without polling. `useLive()` handles reconnect with exponential backoff, `?last_seq=` replay, and a visible "Reconnecting…" pill.
- `useNow()` returns a single shared, server-corrected `Date` ticking each second.
- **Mock mode** (`VITE_USE_MOCKS=true`): MSW handlers for **every** endpoint in Appendix A with realistic Indian data (shelters such as "Asha Shelter", "Seva Kitchen", donors like "Spice Route Kitchen"), plus a scripted mock WebSocket that runs the full story: offer arrives → accepted → driver assigned → route drawn → GPS moves → risk turns tight → re-plan → delivered → impact tick. A "Play demo" button in `/ops` triggers it. Types come from Appendix A (`src/types/api.ts`); if the backend exposes `/openapi.json`, add an `openapi-typescript` script.

---

## 12. Quality bar

- **States:** every list and card has designed loading (skeleton shimmer using `--soft`→`--line`), empty (an invitation to act) and error (says what happened and what to do; no apologies) states.
- **Microcopy:** sentence case, plain verbs, the same word for the same action everywhere ("Post surplus" → toast "Surplus posted"). Say "portions", "shelter", "driver".
- **Accessibility:** WCAG AA contrast; visible focus using the HTML's `3px #8db8c988` ring with 4 px offset; all controls keyboard-operable; `aria-live` for offers and risk changes; diet and risk never conveyed by color alone; touch targets ≥ 46 px (driver ≥ 56 px); `prefers-reduced-motion` honored.
- **Responsive:** breakpoints 900 / 650 / 420 as in the HTML; the landing hero collapses exactly as the reference does; the driver app is designed at 390 px first.
- **i18n:** all strings via i18next; ship complete `en` and `hi` for landing hero, auth, driver flow, offer accept/decline and capacity toggles; missing keys fall back to English.
- **Performance:** Lighthouse ≥ 90 on landing (mobile); lazy-load maps, images and role bundles; no layout shift from the hero animations; images have dimensions.
- **PWA:** installable manifest (green mark icon), service worker caching app shell, offline banner.
- **Tests:** Vitest for `CountdownRing` risk thresholds, offer partial-accept limits, and the WebSocket cache reducer; one Playwright test running the mock demo path (donor posts → shelter accepts → driver completes).

## 13. Build phases (implement in this order; each must run)

1. **Foundation:** Vite app, `tokens.css`/`base.css`/`motion.css` ported from the HTML, `Button`, `Toggle`, `LiveBadge`, `MetricCard`, `Modal`, `Toast`, `Skeleton`, header with scroll progress and drawer.
2. **Landing:** all sections of Section 5, every animation from Section 2.4, illustrative-data labels, role switch and path chooser.
3. **Data layer and mocks:** api client, socket, MSW handlers for all endpoints, `useNow`, session store, auth screens and demo login.
4. **Domain components:** `CountdownRing`, `SlackBar`, badges, `StatusStepper`, `CapacityGauge`, `CapacityTimeline`, `SignalLine`, `RouteMap`.
5. **Donor app** (Section 7).
6. **Recipient app** (Section 8).
7. **Driver app** (Section 9) including offline queue and re-plan animation.
8. **Ops console + scripted demo** (Section 10, 11).
9. **Polish:** i18n pass, accessibility pass, reduced-motion pass, Lighthouse pass, Playwright demo test, README with screenshots list and env variables (`VITE_API_URL`, `VITE_WS_URL`, `VITE_USE_MOCKS`, `VITE_MAP_STYLE_URL`).

**Final output checklist:** file tree · every file complete · README · `.env.example` · a short `DESIGN_NOTES.md` listing which HTML tokens/animations were reused and where.

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
