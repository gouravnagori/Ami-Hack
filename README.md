# ⏳ GoldenHour — Algorithmic Food Rescue Logistics Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React: 19](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg)](https://www.typescriptlang.org)
[![OR-Tools](https://img.shields.io/badge/Google-OR--Tools%20v9.10+-EA4335.svg)](https://developers.google.com/optimization)
[![FSSAI Compliant](https://img.shields.io/badge/Standard-FSSAI%202019%20Compliant-orange.svg)](https://fssai.gov.in)

> **GoldenHour** is a real-time, deadline-driven logistics engine that intercepts commercial food surplus (banquets, hotels, caterers, and messes) and matches it to recipient shelters *before bacterial spoilage thresholds are crossed*. Unlike conventional directories that optimize for static proximity, GoldenHour formulates food rescue as a **time-constrained deadline scheduling problem** combining thermal decay physics, bipartite matching, and vehicle routing with time windows.

---

## 🏛️ System Architecture

GoldenHour is structured as an event-driven, asynchronous micro-monolith designed for sub-second algorithmic dispatch and real-time WebSocket state synchronization.

```mermaid
graph TB
    subgraph ClientTier ["Client Tier (PWA & Edge)"]
        DonorApp["🍲 Donor Portal<br/>(React 19 / MapLibre)"]
        ShelterApp["🏠 Shelter Hub<br/>(React 19 / Capacity Engine)"]
        DriverApp["🛵 Driver Cockpit<br/>(React 19 / Navigation)"]
        OpsConsole["⚡ Ops Console<br/>(Telemetry & Heatmap)"]
    end

    subgraph GatewayTier ["API Gateway & Ingestion Layer"]
        FastAPI["🚀 FastAPI Async Gateway<br/>(Uvicorn / Python 3.14)"]
        AuthMiddleware["🛡️ JWT & Role Auth Middleware<br/>(Argon2id / RBAC)"]
        WSManager["📡 WebSocket Connection Pool<br/>(Real-Time Broadcast)"]
        AIParser["🤖 Vision & NLP Parser<br/>(Gemini 1.5 Flash + Regex Heuristic)"]
    end

    subgraph EngineTier ["Algorithmic Core (Operations Research)"]
        DecayEngine["⏱️ Thermal Spoilage & Safe Slack<br/>(FSSAI Danger Zone Decay Model)"]
        HungarianMatcher["🧩 Min-Cost Bipartite Matcher<br/>(SciPy Linear Sum Assignment)"]
        OR_Tools_PDP["🗺️ Multi-Stop Route Optimizer<br/>(Google OR-Tools PDP-TW Solver)"]
        FallbackRouter["♻️ Zero-Dump Fallback Pipeline<br/>(Gaushala & Biogas Routing)"]
    end

    subgraph PersistenceTier ["Storage & Distributed State"]
        RelationalDB[("🗄️ Relational Core<br/>PostGIS Spatial (Prod)<br/>SQLite + aiosqlite (Dev)")]
        RedisCache[("⚡ Distributed Memory & PubSub<br/>Redis 7 (Matrix Cache & Locks)")]
        AuditLedger[("📜 Cryptographic Audit Ledger<br/>(Time-Stamped OTP Proofs)")]
    end

    subgraph ExternalServices ["External Telemetry Providers"]
        OSRM["🌐 OSRM Routing Machine<br/>(Real-Time Road Network Matrix)"]
        MapLibreTiles["🗺️ MapLibre Open Vector Tiles"]
    end

    %% Client Interactions
    DonorApp -->|REST / HTTPS| FastAPI
    ShelterApp -->|REST & WebSockets| FastAPI
    DriverApp -->|GPS Telemetry Stream| FastAPI
    OpsConsole <-->|Bi-directional WS| WSManager

    %% Gateway Routing
    FastAPI --> AuthMiddleware
    FastAPI --> AIParser
    FastAPI --> WSManager

    %% Engine Workflows
    FastAPI --> DecayEngine
    DecayEngine --> HungarianMatcher
    HungarianMatcher --> OR_Tools_PDP
    OR_Tools_PDP --> FallbackRouter

    %% Persistence & External
    OR_Tools_PDP <-->|Matrix Queries| OSRM
    FastAPI <-->|State & Geofencing| RelationalDB
    FastAPI <-->|Locks & TTL Caching| RedisCache
    DriverApp -.->|OTP Verification| AuditLedger
    ClientTier -.->|Vector Styles| MapLibreTiles

    classDef primary fill:#173d2a,stroke:#8fd35a,stroke-width:2px,color:#fff;
    classDef secondary fill:#f7f6f1,stroke:#173d2a,stroke-width:1px,color:#17221b;
    classDef highlight fill:#8fd35a,stroke:#173d2a,stroke-width:2px,color:#17221b;
    classDef danger fill:#d96b4b,stroke:#173d2a,stroke-width:1px,color:#fff;

    class FastAPI,DecayEngine,HungarianMatcher,OR_Tools_PDP primary;
    class DonorApp,ShelterApp,DriverApp,OpsConsole secondary;
    class RedisCache,RelationalDB highlight;
    class FallbackRouter danger;
```

---

## 🔄 End-to-End Sequence: Life of a Rescue

This sequence diagram illustrates the lifecycle of a surplus food donation from initial logging to verified delivery.

```mermaid
sequenceDiagram
    autonumber
    actor Donor as Commercial Kitchen (Donor)
    participant API as FastAPI Gateway
    participant AI as Gemini / NLP Parser
    participant Engine as Dispatch Core (OR-Tools)
    actor Shelter as Shelter Home (Recipient)
    actor Driver as E-Rickshaw (Driver)
    participant Fallback as Cattle / Biogas Partner

    Donor->>API: Post raw text / photo ("50 plates Dal Bati, hot, 1h ago")
    API->>AI: Extract portions, diet tag (VEG), and storage (HOT)
    AI-->>API: Structured draft (50 portions, 20 kg, FSSAI Window: 120m)
    API->>Engine: Evaluate Safe-Slack & candidate match
    
    rect rgb(240, 248, 240)
        Note over Engine: Safe Slack = SafeLimit - (CookingAge + Transit + Buffer)
        Engine->>Engine: Run SciPy Bipartite Match & OR-Tools PDP-TW
    end

    alt Feasible Match Found (Safe Slack > 15m)
        Engine->>Shelter: Push Reserve Capacity Offer (60s window)
        Shelter->>API: 1-Tap Accept Offer
        API->>Driver: Dispatch Turn-by-Turn Route + ETA
        Driver->>Donor: Arrive at Venue & Pick Up Food
        Driver->>API: Confirm Pickup (Thermal Check)
        API->>Shelter: Real-time Radar Tracking Stream (WebSocket)
        Driver->>Shelter: Arrive at Shelter Gate before Curfew
        Shelter->>Driver: Provide 6-digit Time-Stamped OTP
        Driver->>API: Submit OTP & Proof
        API-->>Donor: Digital 80G Tax Receipt & Impact Audit
    else Infeasible / Slack < 10m (Traffic Spike)
        Engine->>Fallback: Trigger Zero-Dump Bio-compost / Gaushala Reroute
        Fallback-->>API: Confirm Non-Landfill Handoff Logged
    end
```

---

## ⏱️ Real-Time Dynamic Safe-Slack Re-Routing Loop

GoldenHour's safety monitor continuously evaluates active routes against live traffic conditions.

```mermaid
flowchart TD
    Start([Active Rescue In Transit]) --> PollGPS[Poll Driver GPS Telemetry every 15s]
    PollGPS --> QueryTraffic[Query OSRM Road Distance Matrix]
    QueryTraffic --> CalcSlack["Calculate Safe Slack:<br/>Slack = T_safe - (t_elapsed + transit_duration + buffer)"]
    
    CalcSlack --> CheckThreshold{Evaluate Safe Slack}
    
    CheckThreshold -->|Slack >= 20 mins| StateGreen[🟢 Status: SAFE<br/>Continue active navigation]
    CheckThreshold -->|10 mins <= Slack < 20 mins| StateTight[🟡 Status: TIGHT<br/>Notify driver & prioritize traffic corridor]
    CheckThreshold -->|Slack < 10 mins| CheckAlternative{Can closer shelter absorb?}
    
    StateGreen --> SleepLoop[Wait 15 seconds] --> PollGPS
    StateTight --> SleepLoop

    CheckAlternative -->|Yes: Closer capacity verified| Reroute[⚡ Dynamic Re-allocation:<br/>Assign closer shelter with positive slack]
    CheckAlternative -->|No: All human routes infeasible| TriggerFallback[🚨 Trigger Zero-Dump Pipeline:<br/>Reroute to Gaushala / Bio-compost partner]
    
    Reroute --> NotifyAll[Notify Driver, Previous Shelter, New Shelter via WS]
    TriggerFallback --> LogAudit[Log Environmental Safeguard in Ledger]
```

---

## 🛠️ Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Frontend UI/UX** | **React 19**, TypeScript, MapLibre GL, Zustand | Mobile-first Progressive Web App (PWA) with sub-second vector map rendering. |
| **Backend Framework** | **FastAPI**, Python 3.14, AsyncIO, Uvicorn | Asynchronous, non-blocking REST API and WebSocket gateway. |
| **Optimization Core** | **Google OR-Tools (v9.10+)**, **SciPy** | Solves Bipartite matching and Pickup and Delivery with Time Windows (PDP-TW). |
| **AI / NLP Ingestion** | **Google Gemini 1.5 Flash**, Regex Heuristics | Zero-friction natural language donation extraction with offline fallback. |
| **Spatial & Persistence** | **PostGIS (PostgreSQL 16)**, **SQLite + aiosqlite** | Production spatial indexing (`ST_DWithin`, `ST_Point`) with zero-config local dev fallback. |
| **State & Cache** | **Redis 7 (Alpine)** | Distributed route matrix caching, pub/sub messaging, and atomic rate-limiting. |
| **Food Safety Science** | **FSSAI 2019 Regulatory Engine** | Enforces exponential bacterial decay curves and maximum danger zone thresholds. |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
* **Node.js** (v18+)
* **Python** (v3.12+)

### One-Click Startup (Recommended)
From the repository root or the `goldenhour-app` folder:
```cmd
.\start.bat
```
*This automatically sets up Python `.venv`, installs dependencies, initializes the zero-config SQLite database, builds frontend modules, and starts both servers.*

### Manual Startup

#### 1. Backend Server (FastAPI)
```powershell
cd d:\AMI-HACK
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Backend API: `http://localhost:8000`
* Interactive OpenAPI (Swagger) Docs: `http://localhost:8000/docs`
* Health Probes: `http://localhost:8000/healthz` and `http://localhost:8000/readyz`

#### 2. Frontend Client (Vite + React)
```powershell
cd d:\AMI-HACK\goldenhour-app
npm install
npm run dev
```
* Live Application: `http://localhost:5173`

---

## 🗺️ Verified Jaipur Rescue Corridor

The platform is seeded and validated with real-world geospatial coordinates across Jaipur's primary hospitality and institutional shelter clusters:

* **Primary Donor Hubs:** Mansarovar Banquet Cluster, C-Scheme Kitchens, Tonk Road Event Lawns, Vaishali Nagar Cloud Kitchens.
* **Shelter Partner Nodes:** Asha Shelter Home (Malviya Nagar), Bal Sambhal Kendra (JLN Marg), Jagatpura Community Kitchen.
* **Micro-Transit Fleet:** Multi-modal driver profiles including E-Rickshaws (100-portion capacity), Two-Wheelers (30-portion thermal backpacks), and Light Commercial Vans.

---

## 📄 License & Attribution
GoldenHour is an open-source initiative developed for **Ami-Hack 2026** under the **Track A: Surplus-to-Shelter** problem statement. Licensed under the [MIT License](LICENSE).
