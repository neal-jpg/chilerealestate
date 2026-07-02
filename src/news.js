import { formatDate, escapeHtml } from './format.js';

const CAT_CLASS = { Regulation: 'warning', Market: 'accent', Rates: 'accent', Infrastructure: 'neutral' };

function safeUrl(url) {
  try {
    const parsed = new URL(url);
    return (parsed.protocol === 'http:' || parsed.protocol === 'https:') ? url : '#';
  } catch {
    return '#';
  }
}

function catTag(category) {
  const cls = CAT_CLASS[category] || 'neutral';
  return `<span class="cat cat--${cls}">${escapeHtml(category)}</span>`;
}

export function newsListHtml(articles, activeRegion) {
  const filtered = activeRegion === 'All'
    ? articles
    : articles.filter((a) => a.region === activeRegion || a.region === 'national');
  if (filtered.length === 0) {
    return `<p class="empty">No news for this region yet.</p>`;
  }
  return filtered.map((a) => `<article class="news-card" data-action="article" data-id="${escapeHtml(a.id)}">
  <div class="news-card__top">${catTag(a.category)}<i class="ti ti-chevron-right" aria-hidden="true"></i></div>
  <h3 class="news-card__title">${escapeHtml(a.title)}</h3>
  <div class="news-card__meta">${escapeHtml(a.source)} · ${formatDate(a.date)}</div>
</article>`).join('');
}

export function newsDetailHtml(article, contextByKey) {
  const summary = article.summary.map((p) => `<p class="summary__p">${escapeHtml(p)}</p>`).join('');
  const callouts = (article.library_refs || [])
    .map((k) => contextByKey[k])
    .filter(Boolean)
    .map((c) => `<div class="callout">
    <div class="callout__title">${escapeHtml(c.title)}</div>
    <div class="callout__body">${escapeHtml(c.body)}</div>
    <div class="callout__src"><i class="ti ti-book-2" aria-hidden="true"></i>From your library</div>
  </div>`).join('');
  const slice = (article.context_slice || [])
    .map((b) => `<div class="slice__item"><i class="ti ti-point" aria-hidden="true"></i>${escapeHtml(b)}</div>`)
    .join('');
  const context = (callouts || slice)
    ? `<div class="context">
    <div class="context__head"><i class="ti ti-bulb" aria-hidden="true"></i>Context for you</div>
    ${callouts}
    ${slice ? `<div class="slice__head">For your search</div>${slice}` : ''}
  </div>`
    : '';
  return `<div class="detail">
  <button class="back" data-action="back"><i class="ti ti-chevron-left" aria-hidden="true"></i>News</button>
  <div class="detail__tags">${catTag(article.category)}<span class="cat cat--neutral">${escapeHtml(article.region)}</span></div>
  <h1 class="detail__title">${escapeHtml(article.title)}</h1>
  <div class="detail__meta">${escapeHtml(article.source)} · ${formatDate(article.date)}</div>
  <div class="summary">${summary}</div>
  ${context}
  <a class="readorig" href="${escapeHtml(safeUrl(article.url))}" target="_blank" rel="noopener noreferrer">Read the original <i class="ti ti-external-link" aria-hidden="true"></i></a>
</div>`;
}
