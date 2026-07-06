/** Filter list scoped to loaded evidence type (image / video / both). */

export function filterMatchesMediaType(filter, mediaType) {
  if (!filter) return false;
  if (filter.domain === 'both') return true;
  if (mediaType === 'video') return filter.domain === 'video';
  return filter.domain === 'image';
}

export function filtersForMediaType(filters, mediaType, hasEvidence) {
  let list = filters.filter((f) => f.implemented);
  if (!list.length) list = filters;

  if (!hasEvidence) return [];

  if (mediaType === 'video') {
    return list.filter((f) => f.domain === 'video' || f.domain === 'both');
  }
  return list.filter((f) => f.domain === 'image' || f.domain === 'both');
}

export function filterScopeSummary(filters, mediaType, hasEvidence) {
  const scoped = filtersForMediaType(filters, mediaType, hasEvidence);
  const imageCount = scoped.filter((f) => f.domain === 'image').length;
  const videoCount = scoped.filter((f) => f.domain === 'video').length;
  const bothCount = scoped.filter((f) => f.domain === 'both').length;
  return {
    total: scoped.length,
    imageCount,
    videoCount,
    bothCount,
    mediaType: hasEvidence ? mediaType : null,
  };
}

export function mediaContext(state) {
  const hasEvidence = Boolean(state.preview || state.previewOriginal || state.storagePath);
  const isVideo = hasEvidence && state.mediaType === 'video';
  const isImage = hasEvidence && state.mediaType !== 'video';
  return { hasEvidence, isVideo, isImage };
}

/** Which Examination Lab tool groups to show for the loaded evidence type. */
export function examinationToolGroups(state) {
  const ctx = mediaContext(state);
  return {
    overlays: ctx.hasEvidence,
    geometry: ctx.hasEvidence,
    video: ctx.isVideo,
  };
}
