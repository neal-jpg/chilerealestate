import { test } from 'node:test';
import assert from 'node:assert/strict';
import { regionTabsHtml, navHtml } from '../src/chrome.js';

const regions = [
  { code: 'X', name: 'Los Lagos', order: 3 },
  { code: 'IX', name: 'Araucanía', order: 1 },
  { code: 'XIV', name: 'Los Ríos', order: 2 },
];

test('regionTabsHtml orders north-to-south with All first and shows numerals', () => {
  const html = regionTabsHtml(regions, 'IX');
  const order = ['All', 'IX Araucanía', 'XIV Los Ríos', 'X Los Lagos']
    .map((t) => html.indexOf(t));
  assert.ok(order.every((v, i) => i === 0 || order[i - 1] < v));
});

test('regionTabsHtml marks the active tab', () => {
  const html = regionTabsHtml(regions, 'IX');
  assert.match(html, /tab--on[^>]*data-region="IX"|data-region="IX"[^>]*tab--on/);
});

test('navHtml marks the active tab and has all three', () => {
  const html = navHtml('saved');
  assert.match(html, /Listings/);
  assert.match(html, /News/);
  assert.match(html, /Saved/);
  assert.match(html, /nav__item--on[^>]*data-tab="saved"|data-tab="saved"[^>]*nav__item--on/);
});
