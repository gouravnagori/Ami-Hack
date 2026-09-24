/* ============================================================
   GoldenHour — Jaipur Mock Dataset
   Realistic food surplus, shelters, drivers, and active routes
   ============================================================ */
import type {
  Donation,
  CapacitySnapshot,
  Route,
  Offer,
  ImpactSummary,
  AdminLiveSnapshot,
  User
} from '../types/api';

// ── Jaipur Users ──
export const MOCK_USERS: Record<string, User> = {
  donor1: {
    id: 'donor_spiceroute',
    role: 'donor',
    name: 'Spice Route Kitchen',
    email: 'chef@spiceroutejaipur.com',
    phone: '+91 98290 12345',
  },
  donor2: {
    id: 'donor_marriott',
    role: 'donor',
    name: 'Jaipur Marriott Banquet',
    email: 'events@marriottjaipur.in',
    phone: '+91 98290 54321',
  },
  org1: {
    id: 'org_asha',
    role: 'recipient',
    name: 'Asha Shelter Foundation',
    email: 'relief@ashashelter.org',
    phone: '+91 94140 11223',
  },
  org2: {
    id: 'org_akshaya',
    role: 'recipient',
    name: 'Akshaya Patra Jaipur Hub',
    email: 'coordinator@akshayapatra.org',
    phone: '+91 94140 99887',
  },
  driver1: {
    id: 'driver_rajesh',
    role: 'driver',
    name: 'Rajesh Kumar',
    phone: '+91 97850 77665',
  },
  admin1: {
    id: 'admin_ops',
    role: 'admin',
    name: 'Jaipur Ops Control',
    email: 'ops@goldenhour.org',
  },
};

// Current reference timestamp (dynamic)
const now = Date.now();
const minutesFromNow = (m: number) => new Date(now + m * 60 * 1000).toISOString();
const minutesAgo = (m: number) => new Date(now - m * 60 * 1000).toISOString();

// ── Active Donations ──
export const MOCK_DONATIONS: Donation[] = [
  {
    id: 'don_jaipur_01',
    donor_id: 'donor_spiceroute',
    status: 'matching',
    items: [
      { name: 'Paneer Butter Masala', portions: 40, weight_kg: 14 },
      { name: 'Jeera Rice & Tawa Roti', portions: 40, weight_kg: 12 },
      { name: 'Dal Tadka', portions: 25, weight_kg: 8 },
    ],
    total_portions: 65,
    diet: 'veg',
    storage: 'hot',
    prepared_at: minutesAgo(45),
    safe_until: minutesFromNow(120),
    pickup_window: {
      start: minutesFromNow(10),
      end: minutesFromNow(45),
    },
    pickup: {
      lat: 26.9085,
      lng: 75.8012,
      address: 'Spice Route Kitchen, C-Scheme, Ashok Nagar, Jaipur',
    },
    notes: 'Packed in 3 large thermal containers, pickup via back gate',
    parse_confidence: 0.94,
    risk: 'safe',
    slack_seconds: 3600,
    created_at: minutesAgo(15),
    allocations: [
      {
        id: 'alloc_01_a',
        donation_id: 'don_jaipur_01',
        portions: 45,
        status: 'driver_assigned',
        recipient: {
          id: 'org_asha',
          name: 'Asha Shelter Foundation',
          geo: { lat: 26.8580, lng: 75.8150, address: 'Sector 4, Malviya Nagar, Jaipur' },
        },
        container_label: 'JPR-C1',
        deadline: minutesFromNow(90),
        predicted_delivery: minutesFromNow(45),
        slack_seconds: 2700,
        risk: 'safe',
        match_explanation: {
          score: 0.96,
          reasons: [
            { code: 'capacity', label: 'Adequate warm holding capacity (80 available)', weight: 0.4 },
            { code: 'diet', label: 'Strict pure-veg matching', weight: 0.35 },
            { code: 'distance', label: '5.2 km direct route via JLN Marg', weight: 0.25 },
          ],
        },
        driver: {
          id: 'driver_rajesh',
          name: 'Rajesh Kumar',
          vehicle: 'e_rickshaw',
          phone_masked: '+91 97850 ••••5',
        },
        pickup_otp: '4829',
      },
    ],
  },
  {
    id: 'don_jaipur_02',
    donor_id: 'donor_marriott',
    status: 'in_transit',
    items: [
      { name: 'Assorted Subzi & Pulao', portions: 120, weight_kg: 35 },
      { name: 'Gulab Jamun dessert', portions: 80, weight_kg: 10 },
    ],
    total_portions: 120,
    diet: 'veg',
    storage: 'hot',
    prepared_at: minutesAgo(80),
    safe_until: minutesFromNow(60),
    pickup_window: {
      start: minutesAgo(30),
      end: minutesFromNow(15),
    },
    pickup: {
      lat: 26.8524,
      lng: 75.7950,
      address: 'Jaipur Marriott Hotel, Ashram Marg, Tonk Rd, Jaipur',
    },
    parse_confidence: 0.98,
    risk: 'tight',
    slack_seconds: 1400,
    created_at: minutesAgo(60),
    allocations: [
      {
        id: 'alloc_02_a',
        donation_id: 'don_jaipur_02',
        portions: 120,
        status: 'picked_up',
        recipient: {
          id: 'org_akshaya',
          name: 'Akshaya Patra Community Hub',
          geo: { lat: 26.8220, lng: 75.8450, address: 'Mahal Road, Jagatpura, Jaipur' },
        },
        container_label: 'JPR-M12',
        deadline: minutesFromNow(55),
        predicted_delivery: minutesFromNow(25),
        slack_seconds: 1800,
        risk: 'tight',
        driver: {
          id: 'driver_vikram',
          name: 'Vikram Singh',
          vehicle: 'van',
          phone_masked: '+91 94140 ••••2',
        },
        pickup_otp: '7193',
      },
    ],
  },
  {
    id: 'don_jaipur_03',
    donor_id: 'donor_lmb',
    status: 'posted',
    items: [
      { name: 'Fresh Khasta Kachoris & Chutney', portions: 35, weight_kg: 7 },
    ],
    total_portions: 35,
    diet: 'veg',
    storage: 'ambient',
    prepared_at: minutesAgo(20),
    safe_until: minutesFromNow(180),
    pickup_window: {
      start: minutesFromNow(5),
      end: minutesFromNow(60),
    },
    pickup: {
      lat: 26.9208,
      lng: 75.8282,
      address: 'LMB Sweet Shop, Johari Bazaar, Pink City, Jaipur',
    },
    risk: 'safe',
    slack_seconds: 5400,
    created_at: minutesAgo(5),
    allocations: [],
  },
];

// ── Recipient Capacity Snapshots ──
export const MOCK_CAPACITY: Record<string, CapacitySnapshot> = {
  org_asha: {
    org_id: 'org_asha',
    as_of: new Date().toISOString(),
    max_portions: 150,
    in_stock_portions: 45,
    service_rate_per_hour: 30,
    held_portions: 15,
    committed_portions: 45,
    cold: { max: 50, used: 20 },
    available_now: 90,
    projection: [
      { at: minutesFromNow(60), available: 85 },
      { at: minutesFromNow(120), available: 110 },
      { at: minutesFromNow(180), available: 130 },
      { at: minutesFromNow(240), available: 95 },
      { at: minutesFromNow(300), available: 120 },
      { at: minutesFromNow(360), available: 140 },
    ],
    accepts: {
      diets: ['veg', 'egg'],
      storage: ['ambient', 'hot', 'cold'],
    },
    is_open: true,
    closes_at: '22:30',
  },
  org_akshaya: {
    org_id: 'org_akshaya',
    as_of: new Date().toISOString(),
    max_portions: 400,
    in_stock_portions: 180,
    service_rate_per_hour: 80,
    held_portions: 40,
    committed_portions: 120,
    cold: { max: 150, used: 60 },
    available_now: 180,
    projection: [
      { at: minutesFromNow(60), available: 190 },
      { at: minutesFromNow(120), available: 240 },
      { at: minutesFromNow(180), available: 290 },
      { at: minutesFromNow(240), available: 210 },
      { at: minutesFromNow(300), available: 260 },
      { at: minutesFromNow(360), available: 320 },
    ],
    accepts: {
      diets: ['veg'],
      storage: ['ambient', 'hot', 'cold'],
    },
    is_open: true,
    closes_at: '23:00',
  },
};

// ── Active Driver Route ──
export const MOCK_DRIVER_ROUTE: Route = {
  id: 'route_jpr_101',
  driver_id: 'driver_rajesh',
  version: 2,
  status: 'active',
  total_distance_m: 6800,
  total_duration_s: 1650,
  replanned_reason: 'new_stop',
  saved_seconds_vs_previous: 240,
  polyline: [
    [26.9124, 75.7873], // MI Road
    [26.9085, 75.8012], // C-Scheme (Pickup)
    [26.8850, 75.8080], // Tonk Phatak
    [26.8580, 75.8150], // Malviya Nagar (Dropoff)
  ],
  stops: [
    {
      id: 'stop_01_pickup',
      seq: 1,
      type: 'pickup',
      allocation_id: 'alloc_01_a',
      place: {
        name: 'Spice Route Kitchen',
        address: 'C-Scheme, Ashok Nagar, Jaipur',
        lat: 26.9085,
        lng: 75.8012,
      },
      window: {
        start: minutesFromNow(5),
        end: minutesFromNow(35),
      },
      planned_arrival: minutesFromNow(12),
      predicted_arrival: minutesFromNow(10),
      slack_seconds: 1500,
      risk: 'safe',
      portions: 45,
      diet: 'veg',
      storage: 'hot',
      container_label: 'JPR-C1',
      status: 'pending',
      requires_otp: true,
    },
    {
      id: 'stop_02_drop',
      seq: 2,
      type: 'dropoff',
      allocation_id: 'alloc_01_a',
      place: {
        name: 'Asha Shelter Foundation',
        address: 'Sector 4, Malviya Nagar, Jaipur',
        lat: 26.8580,
        lng: 75.8150,
      },
      window: {
        start: minutesFromNow(35),
        end: minutesFromNow(90),
      },
      planned_arrival: minutesFromNow(42),
      predicted_arrival: minutesFromNow(38),
      slack_seconds: 2400,
      risk: 'safe',
      portions: 45,
      diet: 'veg',
      storage: 'hot',
      container_label: 'JPR-C1',
      status: 'pending',
      requires_otp: true,
    },
  ],
};

// ── Pending Offers ──
export const MOCK_OFFERS: Offer[] = [
  {
    id: 'offer_asha_01',
    kind: 'recipient',
    status: 'pending',
    created_at: minutesAgo(2),
    expires_at: minutesFromNow(1), // 60s countdown
    donation: {
      id: 'don_jaipur_01',
      donor_name: 'Spice Route Kitchen (C-Scheme)',
      diet: 'veg',
      storage: 'hot',
      total_portions: 45,
      safe_until: minutesFromNow(120),
      distance_m: 5200,
      items: ['Paneer Butter Masala (40)', 'Jeera Rice (40)', 'Dal Tadka (25)'],
    },
    max_acceptable_portions: 60,
    offered_portions: 45,
    match_explanation: {
      score: 0.96,
      reasons: [
        { code: 'capacity', label: '80 warm holding slots free', weight: 0.4 },
        { code: 'diet', label: 'Matches pure veg shelter criteria', weight: 0.35 },
        { code: 'distance', label: '5.2 km distance via JLN Marg', weight: 0.25 },
      ],
    },
  },
  {
    id: 'offer_driver_01',
    kind: 'driver',
    status: 'pending',
    created_at: minutesAgo(1),
    expires_at: minutesFromNow(1), // 45s countdown
    donation: {
      id: 'don_jaipur_01',
      donor_name: 'Spice Route Kitchen',
      diet: 'veg',
      storage: 'hot',
      total_portions: 45,
      safe_until: minutesFromNow(120),
      distance_m: 6800,
      items: ['Packed in 3 hot meal canisters'],
    },
    route_preview: {
      stops: MOCK_DRIVER_ROUTE.stops,
      total_distance_m: 6800,
      total_duration_s: 1650,
      on_time_confidence: 0.94,
      added_detour_s: 360,
      polyline: MOCK_DRIVER_ROUTE.polyline,
    },
  },
];

// ── Platform Impact Summary ──
export const MOCK_IMPACT: ImpactSummary = {
  meals_rescued: 48260,
  weight_kg: 18450,
  co2e_kg_avoided: 42120,
  on_time_rate: 0.978,
  median_time_to_match_s: 164,
  donations_total: 1248,
  series: [
    { date: 'Mon', meals: 680 },
    { date: 'Tue', meals: 820 },
    { date: 'Wed', meals: 740 },
    { date: 'Thu', meals: 950 },
    { date: 'Fri', meals: 1240 },
    { date: 'Sat', meals: 1580 },
    { date: 'Sun', meals: 1390 },
  ],
};

// ── Admin Ops Snapshot ──
export const MOCK_ADMIN_SNAPSHOT: AdminLiveSnapshot = {
  donors: [
    { id: 'donor_spiceroute', name: 'Spice Route Kitchen (C-Scheme)', geo: { lat: 26.9085, lng: 75.8012 }, active_donations: 1 },
    { id: 'donor_marriott', name: 'Jaipur Marriott (Tonk Rd)', geo: { lat: 26.8524, lng: 75.7950 }, active_donations: 1 },
    { id: 'donor_lmb', name: 'LMB Sweets (Johari Bazaar)', geo: { lat: 26.9208, lng: 75.8282 }, active_donations: 1 },
    { id: 'donor_kanha', name: 'Kanha Caterers (Vaishali)', geo: { lat: 26.9120, lng: 75.7410 }, active_donations: 0 },
  ],
  orgs: [
    { id: 'org_asha', name: 'Asha Shelter (Malviya Nagar)', geo: { lat: 26.8580, lng: 75.8150 }, available_now: 90, is_open: true },
    { id: 'org_akshaya', name: 'Akshaya Patra (Jagatpura)', geo: { lat: 26.8220, lng: 75.8450 }, available_now: 180, is_open: true },
    { id: 'org_seva', name: 'Seva Kutir (Station Rd)', geo: { lat: 26.9215, lng: 75.7960 }, available_now: 40, is_open: true },
    { id: 'org_robin', name: 'RHA Depot (Mansarovar)', geo: { lat: 26.8610, lng: 75.7650 }, available_now: 65, is_open: true },
  ],
  drivers: [
    { id: 'driver_rajesh', name: 'Rajesh K. (E-Rickshaw)', status: 'on_task', geo: { lat: 26.9124, lng: 75.7873 }, vehicle: 'e_rickshaw' },
    { id: 'driver_amit', name: 'Amit S. (Scooter)', status: 'available', geo: { lat: 26.9040, lng: 75.8050 }, vehicle: 'scooter' },
    { id: 'driver_vikram', name: 'Vikram S. (Van)', status: 'on_task', geo: { lat: 26.8524, lng: 75.7950 }, vehicle: 'van' },
  ],
  routes: [MOCK_DRIVER_ROUTE],
};
