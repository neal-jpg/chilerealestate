import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cardHtml, groupByComuna, listingsHtml } from '../src/listings.js';

const turnkey = {
  id: 'a', url: 'a', title: 'Casa <lago>', source: 'Yapo', region: 'IX', comuna: 'Pucón',
  class: 'turnkey', type: 'House', status: 'Built', price_uf: 8900, price_usd: 365000, m2: 140,
  price_per_m2_uf: 63.57, water: true, power: true, access: null, image_url: 'x.jpg',
  yield_band: '~4–8% gross · seasonal', opportunity: 'Strong', price_drop_pct: 6, first_seen: '2026-05-20',
};
const parcela = {
  id: 'b', url: 'b', title: 'Parcela', source: 'BuenasParcelas', region: 'IX', comuna: 'Villarrica',
  class: 'parcela', type: 'Parcela', status: 'Project', price_uf: 2400, price_usd: 98000, m2: 5000,
  price_per_m2_uf: 0.48, water: true, power: true, access: true, image_url: '', yield_band: null,
  opportunity: 'Fair', price_drop_pct: null, first_seen: '2026-07-01',
};

test('turnkey card shows the yield band and not a price/m²', () => {
  const html = cardHtml(turnkey, []);
  assert.match(html, /gross · seasonal/);
  assert.doesNotMatch(html, /UF\/m²/);
});

test('turnkey card shows type strip House and a price-drop pill', () => {
  const html = cardHtml(turnkey, []);
  assert.match(html, /ti-home/);
  assert.match(html, /6%/);
});

test('parcela card shows price/m² and no yield, tagged land', () => {
  const html = cardHtml(parcela, []);
  assert.match(html, /0,48 UF\/m²/);
  assert.doesNotMatch(html, /gross/);
  assert.match(html, /· land/);
  assert.match(html, /ti-map-2/);
});

test('card escapes the title', () => {
  const html = cardHtml(turnkey, []);
  assert.match(html, /Casa &lt;lago&gt;/);
});

test('card marks bookmark on when saved', () => {
  assert.match(cardHtml(turnkey, [{ id: 'a' }]), /bookmark--on/);
  assert.doesNotMatch(cardHtml(turnkey, []), /bookmark--on/);
});

test('groupByComuna groups and sorts comunas', () => {
  const groups = groupByComuna([parcela, turnkey]);
  assert.deepEqual(groups.map((g) => g.comuna), ['Pucón', 'Villarrica']);
});

test('listingsHtml filters by region and shows an empty message when none', () => {
  assert.match(listingsHtml([turnkey, parcela], [], 'X', false), /No listings/);
  assert.match(listingsHtml([turnkey, parcela], [], 'IX', false), /Pucón/);
});

test('listingsHtml shows a thin-coverage banner when flagged', () => {
  assert.match(listingsHtml([turnkey], [], 'IX', true), /thin/i);
});

test('listingsHtml shows both the thin-coverage banner and the empty message when a thin region has no listings', () => {
  const html = listingsHtml([], [], 'X', true);
  assert.match(html, /thin/i);
  assert.match(html, /No listings/);
});

test('card omits the image tag for an unsafe image_url scheme', () => {
  const evil = { ...turnkey, image_url: 'javascript:alert(1)' };
  const html = cardHtml(evil, []);
  assert.doesNotMatch(html, /<img/);
});
