import { formatUf, formatUsd, formatPerM2, escapeHtml, safeUrl } from './format.js';
import { isSaved } from './saved.js';

const OPP_CLASS = { Strong: 'strong', Fair: 'fair', Watch: 'watch', Unrated: 'unrated' };
const OPP_ICON = { Strong: 'ti-award', Fair: 'ti-scale', Watch: 'ti-alert-triangle', Unrated: 'ti-help' };

// Filterable "kind" — the finer type, but every parcela-class listing (type
// Parcela or Land) collapses into one "Land" bucket for the filter + card strip.
const KIND_ICON = { House: 'ti-home', Apartment: 'ti-building', Cabin: 'ti-tent', Land: 'ti-map-2' };
const KIND_ORDER = ['House', 'Apartment', 'Cabin', 'Land'];

export function listingKind(l) {
  return l.class === 'parcela' ? 'Land' : (l.type || 'House');
}

function pill(icon, text) {
  return `<span class="pill">${icon ? `<i class="ti ${icon}" aria-hidden="true"></i>` : ''}${escapeHtml(text)}</span>`;
}

export function cardHtml(l, saved) {
  const isLand = l.class === 'parcela';
  const oppLabel = isLand ? `${l.opportunity} · land` : l.opportunity;
  const oppTag = `<button class="tag tag--${OPP_CLASS[l.opportunity]}" data-action="why" data-id="${escapeHtml(l.id)}" aria-label="Why ${escapeHtml(oppLabel)}?"><i class="ti ${OPP_ICON[l.opportunity]}" aria-hidden="true"></i>${escapeHtml(oppLabel)}</button>`;
  const dropTag = l.price_drop_pct
    ? `<span class="tag tag--drop"><i class="ti ti-trending-down" aria-hidden="true"></i>${l.price_drop_pct}%</span>`
    : '';
  const kind = listingKind(l);
  const typeIcon = KIND_ICON[kind] || 'ti-home';
  const typeLabel = kind;
  const classPill = isLand
    ? (l.price_per_m2_uf != null
        ? `<span class="pill pill--ppm"><i class="ti ti-ruler-2" aria-hidden="true"></i>${formatPerM2(l.price_per_m2_uf)}</span>`
        : '')
    : (l.yield_band
        ? `<span class="pill pill--yield"><i class="ti ti-percentage" aria-hidden="true"></i>${escapeHtml(l.yield_band)}</span>`
        : '');
  const safeImg = l.image_url ? safeUrl(l.image_url) : '';
  const img = (safeImg && safeImg !== '#')
    ? `<img src="${escapeHtml(safeImg)}" alt="" loading="lazy" onerror="this.remove()">`
    : '';
  const bookmark = isSaved(saved, l.id) ? 'bookmark bookmark--on' : 'bookmark';
  const bookmarkLabel = isSaved(saved, l.id) ? 'Saved' : 'Save';
  const m2Pill = l.m2 != null ? pill('', `${l.m2.toLocaleString('es-CL')} m²`) : '';

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
    <div class="card__why" data-why-for="${escapeHtml(l.id)}"></div>
    <h3 class="card__title">${escapeHtml(l.title)}</h3>
    <div class="price"><span class="price__uf">${formatUf(l.price_uf)}</span><span class="price__usd">${formatUsd(l.price_usd)}</span></div>
    <div class="pills">
      ${l.status && l.status !== 'null' ? pill('', l.status) : ''}
      ${m2Pill}
      ${l.water ? pill('ti-droplet', 'Water') : ''}
      ${l.power ? pill('ti-bolt', 'Power') : ''}
      ${classPill}
    </div>
    <div class="card__foot">
      <a class="src" href="${escapeHtml(safeUrl(l.url))}" target="_blank" rel="noopener noreferrer">via ${escapeHtml(l.source)} <i class="ti ti-external-link" aria-hidden="true"></i></a>
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

// Type-filter chip row. Options are data-driven — only kinds actually present
// across the data get a chip — so the bar stays stable as you switch regions.
export function typeChipsHtml(listings, active) {
  const present = new Set(listings.map(listingKind));
  const chip = (label, icon, on) => `<button class="tab${on ? ' tab--on' : ''}" data-type="${escapeHtml(label)}">`
    + `<i class="ti ${icon}" aria-hidden="true"></i>${escapeHtml(label)}</button>`;
  const kinds = KIND_ORDER.filter((k) => present.has(k)).map((k) => chip(k, KIND_ICON[k], active === k)).join('');
  return `<div class="tabs tabs--types">${chip('All', 'ti-layout-grid', active === 'All')}${kinds}</div>`;
}

export function listingsHtml(listings, saved, activeRegion, thin, activeType = 'All') {
  const chips = typeChipsHtml(listings, activeType);
  const byRegion = activeRegion === 'All'
    ? listings
    : listings.filter((l) => l.region === activeRegion);
  const filtered = activeType === 'All'
    ? byRegion
    : byRegion.filter((l) => listingKind(l) === activeType);
  const banner = thin
    ? `<div class="banner"><i class="ti ti-info-circle" aria-hidden="true"></i>Thin coverage here — leaning on alerts and news.</div>`
    : '';
  if (filtered.length === 0) {
    return `${chips}${banner}<p class="empty">No listings match here yet.</p>`;
  }
  const groups = groupByComuna(filtered).map((g) => `
  <section class="town">
    <h2 class="town__head">${escapeHtml(g.comuna)} <span class="town__count">· ${g.items.length} listing${g.items.length === 1 ? '' : 's'}</span></h2>
    ${g.items.map((l) => cardHtml(l, saved)).join('')}
  </section>`).join('');
  return chips + banner + groups;
}
