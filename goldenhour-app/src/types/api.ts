/* ============================================================
   GoldenHour — Appendix A Type Definitions
   Shared contract: never deviate from this.
   ============================================================ */

// ── Enums ──
export type Role = 'donor' | 'recipient' | 'driver' | 'admin';
export type DietType = 'veg' | 'egg' | 'non_veg';
export type StorageCondition = 'ambient' | 'hot' | 'cold';
export type DonationStatus =
  | 'draft' | 'posted' | 'matching' | 'partially_matched'
  | 'matched' | 'in_transit' | 'delivered' | 'expired'
  | 'fallback' | 'cancelled';
export type AllocationStatus =
  | 'offered' | 'accepted' | 'driver_pending' | 'driver_assigned'
  | 'picked_up' | 'delivered' | 'declined' | 'expired'
  | 'cancelled' | 'failed';
export type OfferKind = 'recipient' | 'driver';
export type OfferStatus = 'pending' | 'accepted' | 'declined' | 'expired' | 'withdrawn';
export type StopType = 'pickup' | 'dropoff';
export type StopStatus = 'pending' | 'arrived' | 'done' | 'skipped' | 'failed';
export type DriverStatus = 'offline' | 'available' | 'on_task' | 'stale';
export type VehicleType = 'bicycle' | 'scooter' | 'e_rickshaw' | 'van';
export type Risk = 'safe' | 'tight' | 'critical'; // slack_ratio > 0.30 | 0.10–0.30 | < 0.10
export type RouteStatus = 'planned' | 'active' | 'completed' | 'cancelled';
export type ReplanReason = 'new_stop' | 'traffic' | 'driver_late' | 'recipient_change' | 'manual';

// ── Core shapes ──
export interface GeoPoint {
  lat: number;
  lng: number;
  address?: string;
}

export interface DonationItem {
  name: string;
  portions: number;
  weight_kg?: number;
}

export interface Donation {
  id: string;
  donor_id: string;
  status: DonationStatus;
  items: DonationItem[];
  total_portions: number;
  diet: DietType;
  storage: StorageCondition;
  prepared_at: string;
  safe_until: string;
  pickup_window: { start: string; end: string };
  pickup: GeoPoint;
  photo_url?: string;
  notes?: string;
  parse_confidence?: number;
  allocations: Allocation[];
  risk: Risk;
  slack_seconds: number;
  created_at: string;
}

export interface MatchExplanation {
  score: number;
  reasons: { code: string; label: string; weight: number }[];
}

export interface Allocation {
  id: string;
  donation_id: string;
  portions: number;
  status: AllocationStatus;
  recipient: { id: string; name: string; geo: GeoPoint };
  container_label: string;
  deadline: string;
  predicted_delivery?: string;
  slack_seconds?: number;
  risk: Risk;
  match_explanation?: MatchExplanation;
  driver?: {
    id: string;
    name: string;
    vehicle: VehicleType;
    phone_masked: string;
  };
  pickup_otp?: string;
}

export interface CapacitySnapshot {
  org_id: string;
  as_of: string;
  max_portions: number;
  in_stock_portions: number;
  service_rate_per_hour: number;
  held_portions: number;
  committed_portions: number;
  cold: { max: number; used: number };
  available_now: number;
  projection: { at: string; available: number }[];
  accepts: { diets: DietType[]; storage: StorageCondition[] };
  is_open: boolean;
  closes_at?: string;
}

export interface Stop {
  id: string;
  seq: number;
  type: StopType;
  allocation_id: string;
  place: GeoPoint & { name: string };
  window: { start: string; end: string };
  planned_arrival: string;
  predicted_arrival: string;
  slack_seconds: number;
  risk: Risk;
  portions: number;
  diet: DietType;
  storage: StorageCondition;
  container_label: string;
  status: StopStatus;
  requires_otp: boolean;
}

export interface Route {
  id: string;
  driver_id: string;
  version: number;
  status: RouteStatus;
  stops: Stop[];
  polyline: [number, number][];
  total_distance_m: number;
  total_duration_s: number;
  replanned_reason?: ReplanReason;
  saved_seconds_vs_previous?: number;
}

export interface Offer {
  id: string;
  kind: OfferKind;
  status: OfferStatus;
  created_at: string;
  expires_at: string;
  donation: {
    id: string;
    donor_name: string;
    diet: DietType;
    storage: StorageCondition;
    total_portions: number;
    safe_until: string;
    distance_m: number;
    items: string[];
  };
  // kind = recipient
  max_acceptable_portions?: number;
  offered_portions?: number;
  match_explanation?: MatchExplanation;
  // kind = driver
  route_preview?: {
    stops: Stop[];
    total_distance_m: number;
    total_duration_s: number;
    on_time_confidence: number;
    added_detour_s: number;
    polyline: [number, number][];
  };
}

export interface ImpactSummary {
  meals_rescued: number;
  weight_kg: number;
  co2e_kg_avoided: number;
  on_time_rate: number;
  median_time_to_match_s: number;
  donations_total: number;
  series?: { date: string; meals: number }[];
}

// ── API envelope ──
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id: string;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor?: string;
}

// ── WebSocket ──
export interface WsMessage {
  event: string;
  seq: number;
  ts: string;
  data: unknown;
}

export type WsEvent =
  | 'offer.created' | 'offer.expired' | 'offer.withdrawn'
  | 'donation.updated' | 'allocation.updated' | 'capacity.updated'
  | 'route.updated' | 'driver.location' | 'alert.risk'
  | 'impact.tick' | 'sim.log';

// ── Auth ──
export interface User {
  id: string;
  role: Role;
  name: string;
  email?: string;
  phone?: string;
  city?: string;
  avatar_url?: string;
  profile?: Record<string, any>;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

// ── Donor parse result ──
export interface ParseResult {
  draft: Partial<Donation>;
  confidence: number;
  missing: string[];
}

export interface FeasibilityResult {
  feasible_recipients: number;
  best: {
    name: string;
    distance_m: number;
    slack_seconds: number;
  } | null;
  warnings: string[];
}

// ── Admin ──
export interface AdminLiveSnapshot {
  donors: Array<{ id: string; name: string; geo: GeoPoint; active_donations: number }>;
  orgs: Array<{ id: string; name: string; geo: GeoPoint; available_now: number; is_open: boolean }>;
  drivers: Array<{ id: string; name: string; status: DriverStatus; geo: GeoPoint; vehicle: VehicleType }>;
  routes: Route[];
}

export type SimScenario = 'normal' | 'wedding_night' | 'rush_hour';
export type ChaosKind = 'driver_drop' | 'org_full' | 'traffic_spike' | 'osrm_down';

export interface AdminMetrics {
  on_time_rate: number;
  median_time_to_match_s: number;
  active_routes: number;
  at_risk_count: number;
}

// Issue codes for driver stop issues
export type IssueCode = 'food_not_ready' | 'recipient_closed' | 'vehicle_issue' | 'unsafe_food' | 'other';
export type DeclineReason = 'full' | 'closed' | 'diet' | 'no_cold' | 'other';
