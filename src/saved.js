const KEY = 'cpw.saved';

export function isSaved(saved, id) {
  return saved.some((s) => s.id === id);
}

export function toggleSaved(saved, listing, savedAt) {
  if (isSaved(saved, listing.id)) {
    return saved.filter((s) => s.id !== listing.id);
  }
  return [...saved, {
    id: listing.id,
    url: listing.url,
    title: listing.title,
    price_uf: listing.price_uf,
    image_url: listing.image_url,
    comuna: listing.comuna,
    class: listing.class,
    saved_at: savedAt,
  }];
}

export function annotateSaved(saved, liveById) {
  return saved.map((s) => {
    const live = liveById[s.id];
    if (!live || !live.active) return { ...s, status: 'gone' };
    if (live.price_uf !== s.price_uf) return { ...s, status: 'changed', current_uf: live.price_uf };
    return { ...s, status: 'active', current_uf: live.price_uf };
  });
}

export function loadSaved() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || [];
  } catch {
    return [];
  }
}

export function storeSaved(saved) {
  localStorage.setItem(KEY, JSON.stringify(saved));
}
