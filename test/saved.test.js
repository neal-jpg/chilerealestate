import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isSaved, toggleSaved, annotateSaved } from '../src/saved.js';

const listing = {
  id: 'a', url: 'a', title: 'Casa', price_uf: 8900,
  image_url: 'x.jpg', comuna: 'Pucón', class: 'turnkey',
};

test('toggleSaved adds a snapshot when absent', () => {
  const out = toggleSaved([], listing, '2026-07-01');
  assert.equal(out.length, 1);
  assert.equal(out[0].id, 'a');
  assert.equal(out[0].price_uf, 8900);
  assert.equal(out[0].saved_at, '2026-07-01');
});

test('toggleSaved removes when already present', () => {
  const saved = toggleSaved([], listing, '2026-07-01');
  assert.deepEqual(toggleSaved(saved, listing, '2026-07-02'), []);
});

test('isSaved reflects membership', () => {
  const saved = toggleSaved([], listing, '2026-07-01');
  assert.equal(isSaved(saved, 'a'), true);
  assert.equal(isSaved(saved, 'b'), false);
});

test('annotateSaved flags gone and price-changed items', () => {
  const saved = [
    { id: 'a', price_uf: 8900 },
    { id: 'b', price_uf: 5000 },
    { id: 'c', price_uf: 3000 },
  ];
  const liveById = {
    a: { id: 'a', price_uf: 8900, active: true },
    b: { id: 'b', price_uf: 4700, active: true },
    c: { id: 'c', price_uf: 3000, active: false },
  };
  const out = annotateSaved(saved, liveById);
  assert.equal(out[0].status, 'active');
  assert.equal(out[1].status, 'changed');
  assert.equal(out[1].current_uf, 4700);
  assert.equal(out[2].status, 'gone');
});
