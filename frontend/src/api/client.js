const API_BASE = import.meta.env.VITE_API_URL || '';

export function parseApiError(data, fallback = 'Request failed') {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
  return data?.error || data?.message || fallback;
}

export const LOG_FILE_HINT = '~/.ai-ive/chakshu.log';

function logClientError(context, err, detail = '') {
  const message = String(err?.message || err || 'unknown error');
  fetch(`${API_BASE}/api/diagnostics/log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ context, message, detail }),
  }).catch(() => {});
}

async function request(path, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${path}`, options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(parseApiError(data, res.statusText));
      logClientError(path, err, `HTTP ${res.status}`);
      throw err;
    }
    return data;
  } catch (err) {
    if (err?.name === 'TypeError' || /fetch|network/i.test(String(err?.message))) {
      logClientError(path, err, 'network');
    }
    throw err;
  }
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
  uploadSubtitle: async (file, sessionId = '') => {
    const form = new FormData();
    form.append('file', file);
    const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    const res = await fetch(`${API_BASE}/api/subtitles/upload${q}`, {
      method: 'POST',
      body: form,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(parseApiError(data, res.statusText));
    return data;
  },
  stageMedia: async (file, sessionId = '') => {
    const form = new FormData();
    form.append('file', file);
    const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    const res = await fetch(`${API_BASE}/api/media/stage${q}`, {
      method: 'POST',
      body: form,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(parseApiError(data, res.statusText));
      logClientError('/api/media/stage', err, `HTTP ${res.status}`);
      throw err;
    }
    return data;
  },
  diagnosticsLogTail: (lines = 80) =>
    request(`/api/diagnostics/log-tail?lines=${lines}`),
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
  projectExportSettings: (body) =>
    request('/api/project/export-settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
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
  projectNotes: () => request('/api/project/notes'),
  projectNoteAdd: (body) =>
    request('/api/project/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  projectNoteDelete: (noteId) =>
    request(`/api/project/notes/${encodeURIComponent(noteId)}`, { method: 'DELETE' }),
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
  exportVideo: (body) =>
    request('/api/export', {
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
  reportPreview: () => request('/api/reports/preview'),
  reportTemplates: () => request('/api/reports/templates'),
  i18nLocales: () => request('/api/i18n/locales'),
  i18nStrings: (locale) => request(`/api/i18n/${encodeURIComponent(locale)}`),
  a11yOptions: () => request('/api/accessibility/options'),
  a11yTheme: (highContrast, colorBlind) =>
    request(`/api/accessibility/theme?high_contrast=${highContrast ? 'true' : 'false'}&color_blind=${encodeURIComponent(colorBlind || 'none')}`),

  aiStatus: () => request('/api/ai/status'),
  aiTools: () => request('/api/ai/tools'),
  aiModels: () => request('/api/ai/models'),
  aiEnhanceSession: (body) =>
    request('/api/ai/enhance/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  aiImportModel: async (file, meta = {}) => {
    const form = new FormData();
    form.append('file', file);
    if (meta.model_id) form.append('model_id', meta.model_id);
    if (meta.name) form.append('name', meta.name);
    if (meta.task) form.append('task', meta.task);
    if (meta.description) form.append('description', meta.description);
    const res = await fetch(`${API_BASE}/api/ai/models/import`, { method: 'POST', body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(parseApiError(data, res.statusText));
    return data;
  },
  aiImportModelPath: (body) =>
    request('/api/ai/models/import-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  aiDeleteModel: (modelId) =>
    request(`/api/ai/models/${encodeURIComponent(modelId)}`, { method: 'DELETE' }),

  forensicsActiveCase: () => request('/api/forensics/cases/active'),
  forensicsCreateCase: (body) =>
    request('/api/forensics/cases', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  forensicsCustody: (caseId) => request(`/api/forensics/cases/${caseId}/custody`),
  forensicsApplyFilter: (sessionId, filterId, params, opts = {}) =>
    request('/api/forensics/examination/apply-filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        filter_id: filterId,
        params,
        insert_at: opts.insertAt,
      }),
    }),
  forensicsPreviewFilter: (sessionId, filterId, params, opts = {}) =>
    request('/api/forensics/examination/preview-filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        filter_id: filterId,
        params,
        replace_filter_prefixes: opts.replaceFilterPrefixes,
      }),
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
  forensicsPreview: (sessionId) =>
    request(`/api/forensics/examination/preview?session_id=${encodeURIComponent(sessionId)}`),
  forensicsAnalyzeVideo: (path) =>
    request(`/api/forensics/examination/analyze-video?path=${encodeURIComponent(path)}`, { method: 'POST' }),
  forensicsHash: (path, algorithm = 'all') =>
    request(`/api/forensics/examination/hash?path=${encodeURIComponent(path)}&algorithm=${algorithm}`),

  forensicsSecureMediaScan: (rootPath, verifyManifest = true) =>
    request('/api/forensics/secure-media/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ root_path: rootPath, verify_manifest: verifyManifest }),
    }),
  forensicsSecureMediaLoad: (rootPath, actor = 'examiner', caseId = null) =>
    request('/api/forensics/secure-media/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ root_path: rootPath, actor, case_id: caseId }),
    }),
  forensicsSecureMediaBatchExport: (body) =>
    request('/api/forensics/secure-media/batch-export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  browseFolder: (initialDir = '') =>
    request('/api/forensics/system/browse-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        initial_dir: initialDir || undefined,
        title: 'Select secure media folder',
      }),
    }),

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
  capAudioStreams: (path) =>
    request(`/api/capabilities/audio/streams?path=${encodeURIComponent(path)}`),
  capAudioDurationCompare: (videoPath, audioPath) =>
    request(
      `/api/capabilities/audio/duration-compare?video_path=${encodeURIComponent(videoPath)}&audio_path=${encodeURIComponent(audioPath)}`,
    ),
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
  capCompareGet: (sessionId) =>
    request(`/api/capabilities/compare/${encodeURIComponent(sessionId)}`),
  capCompareRender: (body) =>
    request('/api/capabilities/compare/render', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capMpegViz: (path, time_sec, mode = 'macroblock') =>
    request(`/api/capabilities/mpeg/visualize?mode=${mode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, time_sec }) }),
  capMetadataExport: (path, output_path) =>
    request(`/api/capabilities/metadata/export?path=${encodeURIComponent(path)}&output_path=${encodeURIComponent(output_path)}`, { method: 'POST' }),
  capCaptureDevices: () => request('/api/capture/devices'),
  /** MJPEG must hit the API directly — Vite proxy breaks multipart streams. */
  captureStreamUrl: (device = 0, filterId = null, cacheBust = 0) => {
    const port = import.meta.env.VITE_API_PORT || '9450';
    const base = import.meta.env.VITE_API_URL || `http://127.0.0.1:${port}`;
    let url = `${base}/api/capture/stream/mjpeg?device=${device}&fps=12`;
    if (filterId) url += `&filter_id=${encodeURIComponent(filterId)}`;
    if (cacheBust) url += `&_=${cacheBust}`;
    return url;
  },
  capStopCaptureStream: (device = null) => {
    const port = import.meta.env.VITE_API_PORT || '9450';
    const base = import.meta.env.VITE_API_URL || `http://127.0.0.1:${port}`;
    const q = device != null ? `?device=${device}` : '';
    return fetch(`${base}/api/capture/stream/stop${q}`, { method: 'POST' }).then((r) => r.json());
  },
  capProcessFrame: (filterId, previewBase64) =>
    request('/api/capture/process-frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filter_id: filterId, preview_base64: previewBase64 }),
    }),
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

  capClipboardFrame: (sessionId, includeHash = true) =>
    request(`/api/capabilities/clipboard/frame?session_id=${encodeURIComponent(sessionId)}&include_hash=${includeHash}`),
  capClipboardText: (text) =>
    request('/api/capabilities/clipboard/text', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) }),
  subtitlesParse: (path, limit = 2000) =>
    request('/api/capabilities/subtitles/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, limit }),
    }),
  subtitlesOverlaySession: (body) =>
    request('/api/capabilities/subtitles/overlay-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  subtitlesCueAtTime: (path, timeSec) =>
    request(`/api/capabilities/subtitles/cue-at-time?path=${encodeURIComponent(path)}&time_sec=${timeSec}`),
  capSubtitleBurn: (body) =>
    request('/api/capabilities/subtitles/burn', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capMergeAv: (body) =>
    request('/api/capabilities/merge/av', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capMergeVideos: (body) =>
    request('/api/capabilities/merge/videos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capStreamSync: (body) =>
    request('/api/capabilities/sync/similarity', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capAdvancedFps: (body) =>
    request('/api/capabilities/advanced/fps-adjust', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capAdvancedReverse: (body) =>
    request('/api/capabilities/advanced/reverse', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capAdvancedStabilize: (body) =>
    request('/api/capabilities/advanced/stabilize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capAdvancedTrackingStabilize: (body) =>
    request('/api/capabilities/advanced/tracking-stabilize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capPanoramaConvert: (body) =>
    request('/api/capabilities/advanced/panorama-convert', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  capPanoramaSession: (body) =>
    request('/api/capabilities/advanced/panorama-session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),

  trackingRun: (body) =>
    request('/api/tracking/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  trackingStabilize: (body) =>
    request('/api/tracking/stabilize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  trackingSession: (trackingSessionId) =>
    request(`/api/tracking/session/${encodeURIComponent(trackingSessionId)}`),

  markupListAnnotations: (mediaId, frameIndex = null) => {
    let q = `?media_id=${encodeURIComponent(mediaId)}`;
    if (frameIndex != null) q += `&frame_index=${frameIndex}`;
    return request(`/api/markup/annotations${q}`);
  },
  markupAddAnnotation: (body) =>
    request('/api/markup/annotations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  markupDeleteAnnotation: (mediaId, annotationId) =>
    request(`/api/markup/annotations/${encodeURIComponent(annotationId)}?media_id=${encodeURIComponent(mediaId)}`, { method: 'DELETE' }),
  markupRender: (sessionId, mediaId, frameIndex = 0, persist = false) =>
    request('/api/markup/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, media_id: mediaId, frame_index: frameIndex, persist }),
    }),
  markupRedact: (sessionId, regions, mode = 'pixelate') =>
    request('/api/markup/redact', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, regions, mode }) }),
  markupMeasure: (body) =>
    request('/api/markup/measure', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  markupListMeasurements: (mediaId) =>
    request(`/api/markup/measurements?media_id=${encodeURIComponent(mediaId)}`),

  bookmarksList: (mediaPath) => {
    const q = mediaPath ? `?media_path=${encodeURIComponent(mediaPath)}` : '';
    return request(`/api/bookmarks${q}`);
  },
  bookmarksAdd: (body) =>
    request('/api/bookmarks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  bookmarksUpdate: (bookmarkId, body) =>
    request(`/api/bookmarks/${encodeURIComponent(bookmarkId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  bookmarksDelete: (bookmarkId) =>
    request(`/api/bookmarks/${encodeURIComponent(bookmarkId)}`, { method: 'DELETE' }),
};

export function previewDataUrl(base64) {
  return `data:image/jpeg;base64,${base64}`;
}
