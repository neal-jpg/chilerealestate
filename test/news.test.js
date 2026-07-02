import { test } from 'node:test';
import assert from 'node:assert/strict';
import { newsListHtml, newsDetailHtml } from '../src/news.js';

const article = {
  id: 'a', title: 'Regla <nueva>', region: 'X', category: 'Regulation',
  summary: ['Para one.', 'Para two.'], context_slice: ['Slice bullet.'],
  library_refs: ['how-yield-works'], source: 'La Tercera', url: 'https://x.test/a', date: '2026-06-28',
};
const national = { ...article, id: 'n', region: 'national', title: 'Rates', library_refs: [], context_slice: [] };
const contextByKey = { 'how-yield-works': { key: 'how-yield-works', title: 'How yield works', body: 'Seasonal income.' } };

test('newsListHtml shows regional and national articles for a region', () => {
  const html = newsListHtml([article, national], 'X');
  assert.match(html, /Regla/);
  assert.match(html, /Rates/);
});

test('newsListHtml hides other regions', () => {
  const other = { ...article, id: 'o', region: 'IX', title: 'Araucanía item' };
  assert.doesNotMatch(newsListHtml([other], 'X'), /Araucanía item/);
});

test('newsDetailHtml renders both summary paragraphs and escapes the title', () => {
  const html = newsDetailHtml(article, contextByKey);
  assert.match(html, /Para one\./);
  assert.match(html, /Para two\./);
  assert.match(html, /Regla &lt;nueva&gt;/);
});

test('newsDetailHtml includes the library callout and the per-article slice', () => {
  const html = newsDetailHtml(article, contextByKey);
  assert.match(html, /How yield works/);
  assert.match(html, /From your library/);
  assert.match(html, /Slice bullet\./);
});

test('newsDetailHtml links to the original', () => {
  assert.match(newsDetailHtml(article, contextByKey), /href="https:\/\/x\.test\/a"/);
});

test('newsDetailHtml neutralizes a non-http(s) URL scheme', () => {
  const evil = { ...article, url: 'javascript:alert(1)' };
  const html = newsDetailHtml(evil, contextByKey);
  assert.doesNotMatch(html, /href="javascript:/);
  assert.match(html, /href="#"/);
});

test('newsDetailHtml preserves a valid https URL and adds noreferrer', () => {
  const html = newsDetailHtml(article, contextByKey);
  assert.match(html, /href="https:\/\/x\.test\/a"/);
  assert.match(html, /rel="noopener noreferrer"/);
});
