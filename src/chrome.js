import { escapeHtml } from './format.js';

function tab(region, active) {
  const on = region.code === active ? ' tab--on' : '';
  return `<button class="tab${on}" data-region="${escapeHtml(region.code)}">${escapeHtml(region.code)} ${escapeHtml(region.name)}</button>`;
}

export function regionTabsHtml(regions, active) {
  const sorted = [...regions].sort((a, b) => a.order - b.order);
  const all = `<button class="tab${active === 'All' ? ' tab--on' : ''}" data-region="All">All</button>`;
  return `<div class="tabs">${all}${sorted.map((r) => tab(r, active)).join('')}</div>`;
}

const NAV = [
  { tab: 'listings', label: 'Listings', icon: 'ti-building-community' },
  { tab: 'news', label: 'News', icon: 'ti-news' },
  { tab: 'saved', label: 'Saved', icon: 'ti-bookmark' },
];

export function navHtml(active) {
  return `<nav class="nav">${NAV.map((n) => `<button class="nav__item${n.tab === active ? ' nav__item--on' : ''}" data-tab="${n.tab}"><i class="ti ${n.icon}" aria-hidden="true"></i>${n.label}</button>`).join('')}</nav>`;
}
