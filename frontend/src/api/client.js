const API_BASE = import.meta.env.VITE_API_URL || '';

export function parseApiError(data, fallback = 'Request failed') {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
  return data?.error || data?.message || fallback;
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(parseApiError(data, res.statusText));
  return data;
}

export const api = {
  health: () => request('/api/health'),
  createSession: () => request('/api/session', { method: 'POST' }),
  fetchFilters: () => request('/api/filters'),
  uploadMedia: async (sessionId, file) => {
    const form = new FormData();
    form.append('file', file);
    form.append('session_id', sessionId);
    const res = await fetch(`${API_BASE}/api/media/upload?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'POST', body: form,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(parseApiError(data, res.statusText));
    if (!data.preview) {
      throw new Error(data.detail || 'Could not decode media. For video install ffmpeg: brew install ffmpeg');
    }
    return data;
  },
  loadMediaPath: (sessionId, path) =>
    request('/api/media/load-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, path }),
    }),
  seekVideo: (sessionId, time_sec) =>
    request('/api/media/seek', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, time_sec }),
    }),
  mediaServeUrl: (storagePath) => `${API_BASE}/api/media/serve?path=${encodeURIComponent(storagePath)}`,
  applyFilter: (sessionId, filterId, params) =>
    request('/api/filters/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, filter_id: filterId, params }),
    }),
  undo: (sessionId) =>
    request('/api/edit/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    }),
  redo: (sessionId) =>
    request('/api/edit/redo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    }),
  licenseStatus: () => request('/api/license/status'),
  gpuEncoders: () => request('/api/gpu/encoders'),
  frameTypes: (path) =>
    request('/api/analysis/frame-types', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: '', path }),
    }),
  projectCurrent: () => request('/api/project/current'),
  projectNew: (name) =>
    request('/api/project/new', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    }),
  projectSave: (name, path) =>
    request('/api/project/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, path }),
    }),
  projectImport: (path) =>
    request('/api/project/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    }),
  projectYaml: () => request('/api/project/export-yaml'),
  exportPdfFrames: (body) =>
    request('/api/export/pdf-frames', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  exportMediaBundle: (body) =>
    request('/api/export/media-bundle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  extractAudio: (body) =>
    request('/api/export/audio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  audioStreams: (path) => request(`/api/audio/streams?path=${encodeURIComponent(path)}`),
  exportIFrames: (body) =>
    request('/api/export/i-frames', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  generateReport: (body) =>
    request('/api/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  reportTemplates: () => request('/api/reports/templates'),

  forensicsActiveCase: () => request('/api/forensics/cases/active'),
  forensicsCreateCase: (body) =>
    request('/api/forensics/cases', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  forensicsCustody: (caseId) => request(`/api/forensics/cases/${caseId}/custody`),
  forensicsApplyFilter: (sessionId, filterId, params) =>
    request('/api/forensics/examination/apply-filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, filter_id: filterId, params }),
    }),
  forensicsReset: (sessionId) =>
    request('/api/forensics/examination/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    }),
  forensicsRemoveFilter: (sessionId, index) =>
    request('/api/forensics/examination/remove-filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, index }),
    }),
  forensicsAnalyzeVideo: (path) =>
    request(`/api/forensics/examination/analyze-video?path=${encodeURIComponent(path)}`, { method: 'POST' }),
  forensicsHash: (path, algorithm = 'all') =>
    request(`/api/forensics/examination/hash?path=${encodeURIComponent(path)}&algorithm=${algorithm}`),

  capHashFile: (path) =>
    request('/api/capabilities/hash/file', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) }),
  capHashVerify: (path, expected) =>
    request('/api/capabilities/hash/verify', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, expected }) }),
  capHashFrame: (sessionId, algorithm = 'sha256') =>
    request(`/api/capabilities/hash/frame?session_id=${encodeURIComponent(sessionId)}&algorithm=${algorithm}`),
  capSecureCopy: (body) =>
    request('/api/capabilities/copy/secure', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capVideoInfo: (path) =>
    request('/api/capabilities/video/info', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) }),
  capSeekTime: (path, time_sec) =>
    request('/api/capabilities/video/seek/time', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, time_sec }) }),
  capSeekIframe: (path, time_sec) =>
    request('/api/capabilities/video/seek/iframe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, time_sec }) }),
  capTrim: (body) =>
    request('/api/capabilities/video/trim', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capAudioRedact: (body) =>
    request('/api/capabilities/audio/redact', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capAudioMux: (body) =>
    request('/api/capabilities/audio/mux', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capNotes: (caseId) => request(`/api/capabilities/notes/${caseId}`),
  capAddNote: (body) =>
    request('/api/capabilities/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capRedact: (sessionId, regions) =>
    request('/api/capabilities/examination/redact', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, regions }) }),
  capOverlay: (sessionId, opts) =>
    request('/api/capabilities/examination/overlay', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, ...opts }) }),
  capMeasure: (body) =>
    request('/api/capabilities/measure/distance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capCompareCreate: (left_path, right_path) =>
    request('/api/capabilities/compare/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ left_path, right_path }) }),
  capCompareRender: (body) =>
    request('/api/capabilities/compare/render', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capMpegViz: (path, time_sec, mode = 'macroblock') =>
    request(`/api/capabilities/mpeg/visualize?mode=${mode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, time_sec }) }),
  capMetadataExport: (path, output_path) =>
    request(`/api/capabilities/metadata/export?path=${encodeURIComponent(path)}&output_path=${encodeURIComponent(output_path)}`, { method: 'POST' }),
  capCaptureDevices: () => request('/api/capture/devices'),
  captureStreamUrl: (device = 0, filterId = null) => {
    const base = import.meta.env.VITE_API_URL || '';
    let url = `${base}/api/capture/stream/mjpeg?device=${device}&fps=15`;
    if (filterId) url += `&filter_id=${encodeURIComponent(filterId)}`;
    return url;
  },
  capCaptureSnapshot: (device = 0, filterId = null) => {
    let q = `/api/capture/snapshot?device=${device}`;
    if (filterId) q += `&filter_id=${encodeURIComponent(filterId)}`;
    return request(q);
  },
  capCaptureIngest: (sessionId, previewBase64, filename = 'live-capture.jpg') =>
    request('/api/capture/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, preview_base64: previewBase64, filename }),
    }),
  capScreenCapture: (body) =>
    request('/api/capture/screen', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capSequenceToVideo: (body) =>
    request('/api/capture/sequence/to-video', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capExamples: () => request('/api/capture/examples'),
  capExample: (id) => request(`/api/capture/examples/${encodeURIComponent(id)}`),

  timelineBuild: (path, limit = 25000, forceRefresh = false) =>
    request('/api/timeline/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, limit, force_refresh: forceRefresh }),
    }),
  timelineFilter: (body) =>
    request('/api/timeline/filter', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  timelineRegion: (path, start_sec, end_sec) =>
    request('/api/timeline/region', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, start_sec, end_sec }) }),
  timelineStepFrame: (sessionId, delta, use_iframe = false) =>
    request('/api/timeline/step-frame', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, delta, use_iframe }) }),
  timelineAudioChannels: (path) => request(`/api/timeline/audio/channels?path=${encodeURIComponent(path)}`),
  timelineAvOffset: (path) => request(`/api/timeline/audio/stream-offset?path=${encodeURIComponent(path)}`),
  timelineLoadSecondary: (sessionId, path, label = 'secondary') =>
    request('/api/timeline/video/secondary', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, path, label }) }),

  markupListAnnotations: (mediaId, frameIndex = null) => {
    let q = `?media_id=${encodeURIComponent(mediaId)}`;
    if (frameIndex != null) q += `&frame_index=${frameIndex}`;
    return request(`/api/markup/annotations${q}`);
  },
  markupAddAnnotation: (body) =>
    request('/api/markup/annotations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  markupDeleteAnnotation: (mediaId, annotationId) =>
    request(`/api/markup/annotations/${encodeURIComponent(annotationId)}?media_id=${encodeURIComponent(mediaId)}`, { method: 'DELETE' }),
  markupRender: (sessionId, mediaId, frameIndex = 0) =>
    request('/api/markup/render', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, media_id: mediaId, frame_index: frameIndex }) }),
  markupRedact: (sessionId, regions, mode = 'pixelate') =>
    request('/api/markup/redact', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, regions, mode }) }),
  markupMeasure: (body) =>
    request('/api/markup/measure', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  markupListMeasurements: (mediaId) =>
    request(`/api/markup/measurements?media_id=${encodeURIComponent(mediaId)}`),
};

export function previewDataUrl(base64) {
  return `data:image/jpeg;base64,${base64}`;
}
