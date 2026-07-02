import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sparklineSvg, priceHistoryHtml } from '../src/pricehistory.js';

const points = [
  { date: '2026-05-20', price_uf: 9500 },
  { date: '2026-06-12', price_uf: 9200 },
  { date: '2026-07-01', price_uf: 8900 },
];

test('sparklineSvg draws a polyline and one circle per point', () => {
  const svg = sparklineSvg(points);
  assert.match(svg, /<polyline/);
  assert.equal((svg.match(/<circle/g) || []).length, 3);
});

test('priceHistoryHtml graphs when there are 2+ points, with a drop readout', () => {
  const html = priceHistoryHtml(points, '2026-05-20');
  assert.match(html, /<svg/);
  assert.match(html, /9\.500 → 8\.900 UF/);
  assert.match(html, /6%/);
});

test('priceHistoryHtml shows an empty state with under 2 points', () => {
  const html = priceHistoryHtml([], '2026-07-01');
  assert.match(html, /Tracking since 1 Jul/);
  assert.doesNotMatch(html, /<svg/);
});
