import { regionTabsHtml, navHtml } from './chrome.js';
import { listingsHtml, cardHtml } from './listings.js';
import { priceHistoryHtml } from './pricehistory.js';
import { newsListHtml, newsDetailHtml } from './news.js';
import { loadSaved, storeSaved, toggleSaved, annotateSaved } from './saved.js';
import { formatUf, escapeHtml } from './format.js';

const state = {
  region: 'All',
  tab: 'listings',
  article: null,
  openHistory: new Set(),
};
const data = {};
let saved = loadSaved();

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function listingById() {
  return Object.fromEntries(data.listings.map((l) => [l.id, l]));
}

function contextByKey() {
  return Object.fromEntries(data.context.map((c) => [c.key, c]));
}

function thinForRegion() {
  return state.region !== 'All' && data.meta.thin_coverage.includes(state.region);
}

function savedViewHtml() {
  const annotated = annotateSaved(saved, listingById());
  if (annotated.length === 0) {
    return `<p class="empty">Nothing saved yet. Tap the bookmark on a listing to keep it here.</p>`;
  }
  return annotated.map((s) => {
    const live = listingById()[s.id];
    if (s.status !== 'gone') {
      const note = s.status === 'changed'
        ? `<span class="saved-note">Now ${formatUf(s.current_uf)}</span>`
        : '';
      return cardHtml(live, saved).replace('</h3>', `</h3>${note}`);
    }
    return `<article class="card"><div class="card__body">
      <h3 class="card__title">${escapeHtml(s.title)} <span class="saved-note saved-note--gone">No longer listed</span></h3>
      <div class="price"><span class="price__uf">${formatUf(s.price_uf)}</span></div>
      <div class="src">Saved ${s.saved_at}</div>
    </div></article>`;
  }).join('');
}

function bodyHtml() {
  if (state.tab === 'listings') {
    return listingsHtml(data.listings, saved, state.region, thinForRegion());
  }
  if (state.tab === 'saved') {
    return savedViewHtml();
  }
  if (state.article) {
    const article = data.news.find((a) => a.id === state.article);
    return newsDetailHtml(article, contextByKey());
  }
  return newsListHtml(data.news, state.region);
}

function render() {
  document.getElementById('tabs').innerHTML = regionTabsHtml(data.meta.regions, state.region);
  document.getElementById('app').innerHTML = bodyHtml();
  document.getElementById('nav').innerHTML = navHtml(state.tab);
  for (const id of state.openHistory) {
    const slot = document.querySelector(`[data-history-for="${CSS.escape(id)}"]`);
    if (slot) slot.innerHTML = priceHistoryHtml(data.snapshots[id] || [], listingById()[id].first_seen);
  }
}

function onClick(e) {
  const el = e.target.closest('[data-action], [data-region], [data-tab]');
  if (!el) return;
  if (el.dataset.region) {
    state.region = el.dataset.region;
    render();
    return;
  }
  if (el.dataset.tab) {
    state.tab = el.dataset.tab;
    state.article = null;
    render();
    return;
  }
  const { action, id } = el.dataset;
  if (action === 'save') {
    saved = toggleSaved(saved, listingById()[id], todayIso());
    storeSaved(saved);
    render();
  } else if (action === 'history') {
    if (state.openHistory.has(id)) state.openHistory.delete(id);
    else state.openHistory.add(id);
    render();
  } else if (action === 'article') {
    state.article = id;
    render();
  } else if (action === 'back') {
    state.article = null;
    render();
  }
}

async function boot() {
  const files = ['listings', 'snapshots', 'news', 'context', 'fx', 'meta'];
  const loaded = await Promise.all(files.map((f) => fetch(`data/${f}.json`).then((r) => r.json())));
  files.forEach((f, i) => { data[f] = loaded[i]; });
  document.getElementById('head-date').textContent = data.meta.build_date;
  document.body.addEventListener('click', onClick);
  render();
}

boot();
