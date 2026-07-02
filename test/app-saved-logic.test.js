import { test } from 'node:test';
import assert from 'node:assert/strict';
import { annotateSaved } from '../src/saved.js';

test('annotateSaved marks an inactive-but-present listing as gone, not changed', () => {
  const saved = [{ id: 'a', price_uf: 8900 }];
  const liveById = { a: { id: 'a', price_uf: 8900, active: false } };
  const [result] = annotateSaved(saved, liveById);
  assert.equal(result.status, 'gone');
});

test('annotateSaved marks an inactive listing as gone even if its price also changed', () => {
  const saved = [{ id: 'a', price_uf: 8900 }];
  const liveById = { a: { id: 'a', price_uf: 7000, active: false } };
  const [result] = annotateSaved(saved, liveById);
  assert.equal(result.status, 'gone');
});
