import { formatUf, formatDate, dropPct } from './format.js';

export function sparklineSvg(points) {
  const W = 300, H = 130, padX = 24, padTop = 15, padBot = 30;
  const prices = points.map((p) => p.price_uf);
  const min = Math.min(...prices), max = Math.max(...prices);
  const span = (max - min) || 1;
  const x = (i) => (points.length === 1 ? W / 2 : padX + (i * (W - 2 * padX)) / (points.length - 1));
  const y = (v) => padTop + ((max - v) / span) * (H - padTop - padBot);
  const pts = points.map((p, i) => `${x(i).toFixed(1)},${y(p.price_uf).toFixed(1)}`).join(' ');
  const dots = points.map((p, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(p.price_uf).toFixed(1)}" r="3" class="ph__dot"></circle>`).join('');
  return `<svg viewBox="0 0 ${W} ${H}" class="ph__svg" role="img" aria-label="Price history line graph">
  <polyline points="${pts}" class="ph__line" fill="none"></polyline>
  ${dots}
  <text x="${padX}" y="120" class="ph__axis" text-anchor="start">${formatDate(points[0].date)}</text>
  <text x="${W - padX}" y="120" class="ph__axis" text-anchor="end">${formatDate(points[points.length - 1].date)}</text>
</svg>`;
}

export function priceHistoryHtml(points, firstSeen) {
  if (!points || points.length < 2) {
    return `<div class="ph__empty">
  <i class="ti ti-chart-dots" aria-hidden="true"></i>
  <p class="ph__emptyhead">Tracking since ${formatDate(firstSeen)}</p>
  <p class="ph__emptysub">The graph fills in as the price changes. Nothing to chart yet.</p>
</div>`;
  }
  const first = points[0].price_uf;
  const last = points[points.length - 1].price_uf;
  const drop = dropPct(first, last);
  const dropPill = drop
    ? `<span class="tag tag--drop"><i class="ti ti-trending-down" aria-hidden="true"></i>${drop}% since ${formatDate(points[0].date)}</span>`
    : '';
  const firstNum = formatUf(first).replace(/ UF$/, '');
  return `<div class="ph">
  ${sparklineSvg(points)}
  <div class="ph__read"><span class="ph__readuf">${firstNum} → ${formatUf(last)}</span>${dropPill}</div>
</div>`;
}
