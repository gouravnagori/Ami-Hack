/* ============================================================
   GoldenHour — Unit Tests for Spoilage Risk & Formatting
   ============================================================ */
import { formatPortions, formatDistance, formatSlack } from '../lib/format';

describe('GoldenHour Formatter & Risk Logic', () => {
  test('formats portion counts correctly', () => {
    expect(formatPortions(1)).toBe('1 portion');
    expect(formatPortions(45)).toBe('45 portions');
    expect(formatPortions(120)).toBe('120 portions');
  });

  test('formats distances in metres and kilometres', () => {
    expect(formatDistance(450)).toBe('450 m');
    expect(formatDistance(1200)).toBe('1.2 km');
    expect(formatDistance(5200)).toBe('5.2 km');
  });

  test('formats remaining slack minutes and hours', () => {
    expect(formatSlack(45)).toBe('45s');
    expect(formatSlack(180)).toBe('3m');
    expect(formatSlack(3600)).toBe('60m');
    expect(formatSlack(7200)).toBe('2h');
  });
});
