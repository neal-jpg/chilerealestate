const CLP = new Intl.NumberFormat('es-CL');
const CLP2 = new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function formatUf(n) {
  return `${CLP.format(Math.round(n))} UF`;
}

export function formatUsd(n) {
  return `≈ US$${CLP.format(Math.round(n))}`;
}

export function formatPerM2(n) {
  return `${CLP2.format(n)} UF/m²`;
}

export function formatDate(iso) {
  const [, m, d] = iso.split('-').map(Number);
  return `${d} ${MONTHS[m - 1]}`;
}

export function dropPct(first, current) {
  if (!(current < first)) return null;
  const pct = Math.round(((first - current) / first) * 100);
  return pct >= 1 ? pct : null;
}

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}
