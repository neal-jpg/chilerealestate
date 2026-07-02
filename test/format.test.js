import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatUf, formatUsd, formatPerM2, formatDate, dropPct, escapeHtml, safeUrl } from '../src/format.js';

test('formatUf uses Chilean thousands and a UF suffix', () => {
  assert.equal(formatUf(8900), '8.900 UF');
});

test('formatUsd prefixes with approx US$ and Chilean thousands', () => {
  assert.equal(formatUsd(365000), '≈ US$365.000');
});

test('formatPerM2 uses two decimals with a comma', () => {
  assert.equal(formatPerM2(0.48), '0,48 UF/m²');
});

test('formatDate renders day and short month', () => {
  assert.equal(formatDate('2026-07-01'), '1 Jul');
});

test('dropPct returns a rounded percent only for a real drop', () => {
  assert.equal(dropPct(9500, 8900), 6);
  assert.equal(dropPct(8900, 8900), null);
  assert.equal(dropPct(8900, 9200), null);
});

test('escapeHtml neutralizes angle brackets and quotes', () => {
  assert.equal(escapeHtml('<a "x">'), '&lt;a &quot;x&quot;&gt;');
});

test('safeUrl allows http and https, blocks other schemes', () => {
  assert.equal(safeUrl('https://example.com/a.jpg'), 'https://example.com/a.jpg');
  assert.equal(safeUrl('http://example.com/a.jpg'), 'http://example.com/a.jpg');
  assert.equal(safeUrl('javascript:alert(1)'), '#');
  assert.equal(safeUrl('data:text/html,<script>alert(1)</script>'), '#');
  assert.equal(safeUrl('not a url'), '#');
});
