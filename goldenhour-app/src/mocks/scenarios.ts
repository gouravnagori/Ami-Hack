/* ============================================================
   GoldenHour — Simulation Scenarios & Chaos Injections
   ============================================================ */
import type { SimScenario, ChaosKind } from '../types/api';
import { mockWsBus } from './ws';

export interface ScenarioDef {
  id: SimScenario;
  name: string;
  description: string;
  donationsPerMin: number;
  trafficMultiplier: number;
}

export const SCENARIOS: Record<SimScenario, ScenarioDef> = {
  normal: {
    id: 'normal',
    name: 'Normal Operation (Jaipur Lunchtime)',
    description: 'Steady donations from C-Scheme restaurants and banquet halls with ample drivers.',
    donationsPerMin: 2,
    trafficMultiplier: 1.0,
  },
  wedding_night: {
    id: 'wedding_night',
    name: 'Wedding Banquet Surge (Mansarovar)',
    description: 'High volume (300+ portions) late night surplus from palace gardens and resorts.',
    donationsPerMin: 6,
    trafficMultiplier: 0.8,
  },
  rush_hour: {
    id: 'rush_hour',
    name: 'Evening Rush Hour (Tonk Rd / JLN Marg)',
    description: 'Severe traffic congestion reducing vehicle speeds by 50% and shrinking slack windows.',
    donationsPerMin: 3,
    trafficMultiplier: 2.2,
  },
};

export function runChaosAction(kind: ChaosKind) {
  switch (kind) {
    case 'driver_drop':
      mockWsBus.emit('sim.log', {
        type: 'warning',
        text: 'Driver Rajesh Kumar went offline unexpectedly near MI Road. Auto-reassigning Stop #1.',
      });
      mockWsBus.emit('route.updated', {
        status: 'replanned',
        reason: 'driver_late',
        new_driver: 'Amit Sharma (Scooter)',
      });
      break;

    case 'org_full':
      mockWsBus.emit('sim.log', {
        type: 'alert',
        text: 'Asha Shelter Foundation reached 100% capacity! Rerouting batch to Akshaya Patra Jagatpura.',
      });
      mockWsBus.emit('capacity.updated', {
        org_id: 'org_asha',
        available_now: 0,
        is_open: false,
      });
      break;

    case 'traffic_spike':
      mockWsBus.emit('sim.log', {
        type: 'warning',
        text: 'Traffic congestion alert on Tonk Road (+14 min delay). Recalculating slack times.',
      });
      mockWsBus.emit('alert.risk', {
        donation_id: 'don_jaipur_02',
        new_risk: 'critical',
        slack_seconds: 320,
      });
      break;

    case 'osrm_down':
      mockWsBus.emit('sim.log', {
        type: 'info',
        text: 'Routing engine fallback to Euclidean Haversine matrix. Rerouting 4 drivers.',
      });
      break;
  }
}
