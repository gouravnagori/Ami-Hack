/* ============================================================
   GoldenHour — MSW Handlers for Appendix A API Contract
   ============================================================ */
import { http, HttpResponse } from 'msw';
import {
  MOCK_USERS,
  MOCK_DONATIONS,
  MOCK_CAPACITY,
  MOCK_DRIVER_ROUTE,
  MOCK_OFFERS,
  MOCK_IMPACT,
  MOCK_ADMIN_SNAPSHOT,
} from './data';
import type { Donation, ParseResult, FeasibilityResult, Route } from '../types/api';

// In-memory state copies
let donations = [...MOCK_DONATIONS];
let offers = [...MOCK_OFFERS];
let driverRoute: Route = { ...MOCK_DRIVER_ROUTE };
let capacityStore = { ...MOCK_CAPACITY };

export const handlers = [
  // ── Server Time ──
  http.get('/api/time', () => {
    return HttpResponse.json({
      server_time: new Date().toISOString(),
      epoch_ms: Date.now(),
    });
  }),

  // ── Auth ──
  http.post('/api/auth/login', async ({ request }) => {
    const body = (await request.json()) as { role?: string; email?: string };
    const role = body.role || 'donor';
    const user =
      role === 'donor'
        ? MOCK_USERS.donor1
        : role === 'recipient'
        ? MOCK_USERS.org1
        : role === 'driver'
        ? MOCK_USERS.driver1
        : MOCK_USERS.admin1;

    return HttpResponse.json({
      user,
      tokens: {
        access_token: `mock_jwt_access_${user.id}`,
        refresh_token: `mock_jwt_refresh_${user.id}`,
        expires_in: 3600,
      },
    });
  }),

  http.post('/api/auth/refresh', () => {
    return HttpResponse.json({
      access_token: `mock_jwt_access_${Date.now()}`,
      refresh_token: `mock_jwt_refresh_${Date.now()}`,
      expires_in: 3600,
    });
  }),

  // ── Donor Endpoints ──
  http.get('/api/donations', () => {
    return HttpResponse.json({
      items: donations,
    });
  }),

  http.get('/api/donations/:id', ({ params }) => {
    const found = donations.find((d) => d.id === params.id);
    if (!found) {
      return new HttpResponse(null, { status: 404 });
    }
    return HttpResponse.json(found);
  }),

  http.post('/api/donations', async ({ request }) => {
    const body = (await request.json()) as Partial<Donation>;
    const newDonation: Donation = {
      id: `don_${Date.now()}`,
      donor_id: 'donor_spiceroute',
      status: 'matching',
      items: body.items || [{ name: 'Chef Special Surplus', portions: body.total_portions || 30 }],
      total_portions: body.total_portions || 30,
      diet: body.diet || 'veg',
      storage: body.storage || 'ambient',
      prepared_at: body.prepared_at || new Date().toISOString(),
      safe_until: body.safe_until || new Date(Date.now() + 2 * 3600 * 1000).toISOString(),
      pickup_window: body.pickup_window || {
        start: new Date().toISOString(),
        end: new Date(Date.now() + 1800 * 1000).toISOString(),
      },
      pickup: body.pickup || {
        lat: 26.9085,
        lng: 75.8012,
        address: 'C-Scheme, Ashok Nagar, Jaipur',
      },
      notes: body.notes,
      parse_confidence: 0.95,
      risk: 'safe',
      slack_seconds: 3600,
      created_at: new Date().toISOString(),
      allocations: [
        {
          id: `alloc_${Date.now()}`,
          donation_id: `don_${Date.now()}`,
          portions: body.total_portions || 30,
          status: 'driver_pending',
          recipient: {
            id: 'org_asha',
            name: 'Asha Shelter Foundation (Malviya Nagar)',
            geo: { lat: 26.8580, lng: 75.8150, address: 'Sector 4, Malviya Nagar, Jaipur' },
          },
          container_label: 'JPR-NEW',
          deadline: new Date(Date.now() + 7200 * 1000).toISOString(),
          risk: 'safe',
          pickup_otp: '5512',
        },
      ],
    };

    donations.unshift(newDonation);
    return HttpResponse.json(newDonation, { status: 201 });
  }),

  // AI Natural Language Quick Post Parser
  http.post('/api/donations/parse', async ({ request }) => {
    const body = (await request.json()) as { text: string };
    const text = (body.text || '').toLowerCase();

    const portionsMatch = text.match(/(\d+)\s*(meals|portions|people|servings|pax)?/);
    const portions = portionsMatch ? parseInt(portionsMatch[1], 10) : 40;

    const isNonVeg = text.includes('chicken') || text.includes('egg') || text.includes('non-veg');
    const isHot = text.includes('hot') || text.includes('fresh') || text.includes('cooked') || text.includes('curry');
    const isCold = text.includes('cold') || text.includes('dessert') || text.includes('ice');

    const result: ParseResult = {
      draft: {
        total_portions: portions,
        diet: isNonVeg ? 'non_veg' : 'veg',
        storage: isCold ? 'cold' : isHot ? 'hot' : 'ambient',
        items: [{ name: body.text.slice(0, 30) || 'Nutritious Meal Surplus', portions }],
        pickup: {
          lat: 26.9085,
          lng: 75.8012,
          address: 'Spice Route Kitchen, C-Scheme, Jaipur',
        },
        safe_until: new Date(Date.now() + 3 * 3600 * 1000).toISOString(),
      },
      confidence: 0.92,
      missing: [],
    };

    return HttpResponse.json(result);
  }),

  // Feasibility Check
  http.post('/api/donations/feasibility', () => {
    const feasibility: FeasibilityResult = {
      feasible_recipients: 3,
      best: {
        name: 'Asha Shelter Foundation (Malviya Nagar)',
        distance_m: 5200,
        slack_seconds: 3600,
      },
      warnings: [],
    };
    return HttpResponse.json(feasibility);
  }),

  // ── Recipient Offers & Capacity ──
  http.get('/api/offers', () => {
    return HttpResponse.json({ items: offers });
  }),

  http.post('/api/offers/:id/accept', ({ params }) => {
    offers = offers.filter((o) => o.id !== params.id);
    return HttpResponse.json({ success: true, message: 'Offer accepted successfully' });
  }),

  http.post('/api/offers/:id/decline', ({ params }) => {
    offers = offers.filter((o) => o.id !== params.id);
    return HttpResponse.json({ success: true, message: 'Offer declined' });
  }),

  http.get('/api/capacity/current', () => {
    return HttpResponse.json(capacityStore.org_asha);
  }),

  http.post('/api/capacity', async ({ request }) => {
    const update = (await request.json()) as Partial<typeof capacityStore.org_asha>;
    capacityStore.org_asha = {
      ...capacityStore.org_asha,
      ...update,
    };
    return HttpResponse.json(capacityStore.org_asha);
  }),

  // ── Driver Routes & Actions ──
  http.get('/api/routes/active', () => {
    return HttpResponse.json(driverRoute);
  }),

  http.post('/api/routes/:id/stops/:stop_id/done', ({ params }) => {
    const stopIdx = driverRoute.stops.findIndex((s) => s.id === params.stop_id);
    if (stopIdx !== -1) {
      driverRoute.stops[stopIdx].status = 'done';
    }
    return HttpResponse.json({ success: true, route: driverRoute });
  }),

  http.post('/api/routes/:id/stops/:stop_id/issue', async ({ request }) => {
    const body = (await request.json()) as { reason: string };
    return HttpResponse.json({
      success: true,
      message: `Issue recorded: ${body.reason}`,
      fallback_suggested: true,
    });
  }),

  http.get('/api/driver/status', () => {
    return HttpResponse.json({
      status: 'available',
      active_route_id: driverRoute.id,
      shift_hours: 3.5,
      completed_today: 4,
    });
  }),

  http.post('/api/driver/status', async ({ request }) => {
    const body = (await request.json()) as { status: string };
    return HttpResponse.json({ status: body.status });
  }),

  http.post('/api/driver/location', () => {
    return HttpResponse.json({ acknowledged: true });
  }),

  // ── Impact & Analytics ──
  http.get('/api/impact/summary', () => {
    return HttpResponse.json(MOCK_IMPACT);
  }),

  // ── Ops Console ──
  http.get('/api/admin/live', () => {
    return HttpResponse.json(MOCK_ADMIN_SNAPSHOT);
  }),

  http.get('/api/admin/metrics', () => {
    return HttpResponse.json({
      on_time_rate: 0.978,
      median_time_to_match_s: 164,
      active_routes: 3,
      at_risk_count: 1,
    });
  }),

  http.post('/api/admin/simulate', async ({ request }) => {
    const body = (await request.json()) as { scenario: string; speed?: number };
    return HttpResponse.json({
      scenario: body.scenario,
      running: true,
      speed: body.speed || 1,
      message: `Simulation started for scenario: ${body.scenario}`,
    });
  }),

  http.post('/api/admin/chaos', async ({ request }) => {
    const body = (await request.json()) as { kind: string };
    return HttpResponse.json({
      chaos: body.kind,
      applied: true,
      message: `Chaos injected: ${body.kind}. Engine replanning triggered.`,
    });
  }),
];
