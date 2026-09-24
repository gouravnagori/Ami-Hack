# ⏳ GoldenHour — Algorithmic Food Rescue Network (Ami-Hack 2026)

> **Matches surplus food from commercial kitchens to shelters before it spoils, dispatching drivers on zero-detour routes across the Jaipur metropolitan corridor.**

---

## 📁 Repository Structure

```text
├── goldenhour-app/            # Complete Frontend (React 18 + Vite + TypeScript)
│   ├── src/
│   │   ├── components/        # Signature UI and Domain components (CountdownRing, etc.)
│   │   ├── features/          # 4 Portals: Donor, Shelter, Driver, Ops + Landing
│   │   ├── lib/               # Clock sync, Jaipur geo utils, i18n (EN/HI), API & WS client
│   │   ├── mocks/             # In-browser MSW engine & simulated Jaipur WebSocket telemetry
│   │   └── store/             # Zustand session and UI stores
│   ├── public/                # Static assets and PWA manifest
│   ├── README.md              # Detailed frontend documentation
│   └── package.json           # Dependencies and scripts
│
├── reference.html             # Pixel-accurate reference design source of truth
└── GoldenHour_Frontend_Prompt.md  # Architecture and Appendix A API contract specification
```

---

## 🚀 Quick Start (Frontend)

```bash
cd goldenhour-app
npm install
npm run dev
```

Open `http://localhost:5173` to explore:
- 🍲 **Donor App:** Quick Post with AI parsing & feasibility checker
- 🏠 **Shelter App:** Real-time Capacity Gauge & 60s offer response
- 🛵 **Driver Cockpit:** Multi-stop turn-by-turn navigation & OTP handshake
- ⚡ **Ops Console:** Live Jaipur corridor map & simulation / chaos testing controls

---

## 🔌 Backend Integration

GoldenHour is ready for seamless backend pairing. To connect your real backend:
1. Open `goldenhour-app/.env`
2. Set:
   ```env
   VITE_USE_MOCKS=false
   VITE_API_URL=http://localhost:8000/api
   VITE_WS_URL=ws://localhost:8000/ws
   ```
3. Restart `npm run dev`. The frontend automatically bypasses MSW and connects directly!
