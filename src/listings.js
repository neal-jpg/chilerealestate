import { formatUf, formatUsd, formatPerM2, escapeHtml } from './format.js';
import { isSaved } from './saved.js';

const OPP_CLASS = { Strong: 'strong', Fair: 'fair', Watch: 'watch', Unrated: 'unrated' };
const OPP_ICON = { Strong: 'ti-award', Fair: 'ti-scale', Watch: 'ti-alert-triangle', Unrated: 'ti-help' };

function pill(icon, text) {
  return `<span class="pill">${icon ? `<i class="ti ${icon}" aria-hidden="true"></i>` : ''}${escapeHtml(text)}</span>`;
}

export function cardHtml(l, saved) {
  const isLand = l.class === 'parcela';
  const oppLabel = isLand ? `${l.opportunity} · land` : l.opportunity;
  const oppTag = `<span class="tag tag--${OPP_CLASS[l.opportunity]}"><i class="ti ${OPP_ICON[l.opportunity]}" aria-hidden="true"></i>${escapeHtml(oppLabel)}</span>`;
  const dropTag = l.price_drop_pct
    ? `<span class="tag tag--drop"><i class="ti ti-trending-down" aria-hidden="true"></i>${l.price_drop_pct}%</span>`
    : '';
  const typeIcon = isLand ? 'ti-map-2' : 'ti-home';
  const typeLabel = isLand ? 'Land' : 'House';
  const classPill = isLand
    ? `<span class="pill pill--ppm"><i class="ti ti-ruler-2" aria-hidden="true"></i>${formatPerM2(l.price_per_m2_uf)}</span>`
    : `<span class="pill pill--yield"><i class="ti ti-percentage" aria-hidden="true"></i>${escapeHtml(l.yield_band)}</span>`;
  const img = l.image_url
    ? `<img src="${escapeHtml(l.image_url)}" alt="" loading="lazy" onerror="this.remove()">`
    : '';
  const bookmark = isSaved(saved, l.id) ? 'bookmark bookmark--on' : 'bookmark';
  const bookmarkLabel = isSaved(saved, l.id) ? 'Saved' : 'Save';

  return `<article class="card" data-id="${escapeHtml(l.id)}">
  <div class="card__img">
    <i class="ti ti-photo card__imgph" aria-hidden="true"></i>
    ${img}
    <div class="card__type"><i class="ti ${typeIcon}" aria-hidden="true"></i>${typeLabel}</div>
  </div>
  <div class="card__body">
    <div class="card__top">
      <div class="tags">${oppTag}${dropTag}</div>
      <button class="${bookmark}" data-action="save" data-id="${escapeHtml(l.id)}" aria-label="${bookmarkLabel}"><i class="ti ti-bookmark" aria-hidden="true"></i></button>
    </div>
    <h3 class="card__title">${escapeHtml(l.title)}</h3>
    <div class="price"><span class="price__uf">${formatUf(l.price_uf)}</span><span class="price__usd">${formatUsd(l.price_usd)}</span></div>
    <div class="pills">
      ${pill('', l.status)}
      ${pill('', `${l.m2.toLocaleString('es-CL')} m²`)}
      ${l.water ? pill('ti-droplet', 'Water') : ''}
      ${l.power ? pill('ti-bolt', 'Power') : ''}
      ${classPill}
    </div>
    <div class="card__foot">
      <span class="src">via ${escapeHtml(l.source)}</span>
      <button class="toggle" data-action="history" data-id="${escapeHtml(l.id)}">Price history <i class="ti ti-chevron-right" aria-hidden="true"></i></button>
    </div>
    <div class="card__history" data-history-for="${escapeHtml(l.id)}"></div>
  </div>
</article>`;
}

export function groupByComuna(listings) {
  const map = new Map();
  for (const l of listings) {
    if (!map.has(l.comuna)) map.set(l.comuna, []);
    map.get(l.comuna).push(l);
  }
  return [...map.keys()]
    .sort((a, b) => a.localeCompare(b, 'es-CL'))
    .map((comuna) => ({ comuna, items: map.get(comuna) }));
}

export function listingsHtml(listings, saved, activeRegion, thin) {
  const filtered = activeRegion === 'All'
    ? listings
    : listings.filter((l) => l.region === activeRegion);
  if (filtered.length === 0) {
    return `<p class="empty">No listings in this region yet.</p>`;
  }
  const banner = thin
    ? `<div class="banner"><i class="ti ti-info-circle" aria-hidden="true"></i>Thin coverage here — leaning on alerts and news.</div>`
    : '';
  const groups = groupByComuna(filtered).map((g) => `
  <section class="town">
    <h2 class="town__head">${escapeHtml(g.comuna)} <span class="town__count">· ${g.items.length} listing${g.items.length === 1 ? '' : 's'}</span></h2>
    ${g.items.map((l) => cardHtml(l, saved)).join('')}
  </section>`).join('');
  return banner + groups;
}
