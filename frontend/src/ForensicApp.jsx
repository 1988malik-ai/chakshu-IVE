import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, previewDataUrl } from './api/client';
import AudioPlayer from './components/AudioPlayer';
import ForensicTimeline, { formatTc } from './components/ForensicTimeline';
import ExamCanvas from './components/ExamCanvas';
import LiveCapture from './components/LiveCapture';
import LocaleSettings from './components/LocaleSettings';
import ExamCompareDock from './components/ExamCompareDock';
import ProjectNotesPanel from './components/ProjectNotesPanel';
import LegalExportPanel from './components/LegalExportPanel';
import ForensicVideoTransport from './components/ForensicVideoTransport';
import AudioRedactionPanel from './components/AudioRedactionPanel';
import AudioStreamPanel from './components/AudioStreamPanel';
import SubtitlePanel from './components/SubtitlePanel';
import BookmarksPanel from './components/BookmarksPanel';
import CaseReportsPanel from './components/CaseReportsPanel';
import SidebarFooter from './components/SidebarFooter';
import { useForensicPlayback } from './hooks/useForensicPlayback';
import CompareFrameView from './components/CompareFrameView';
import { useLocale } from './i18n/LocaleContext';
import { PRODUCT_FULL } from './brand';
import {
  derivePathsFromOutputDir,
  loadExportFormFromStorage,
  mergeExportSettings,
  outputDirForCase,
  saveExportFormToStorage,
} from './lib/exportPaths';

const NAV_KEYS = [
  { id: 'command', key: 'nav.command' },
  { id: 'examine', key: 'nav.examine' },
  { id: 'capture', key: 'nav.capture' },
  { id: 'markup', key: 'nav.markup' },
  { id: 'timeline', key: 'nav.timeline' },
  { id: 'tools', key: 'nav.tools' },
  { id: 'custody', key: 'nav.custody' },
  { id: 'export', key: 'nav.export' },
  { id: 'reports', key: 'nav.reports' },
  { id: 'settings', key: 'nav.settings' },
];

export default function ForensicApp() {
  const { t, locale } = useLocale();
  const [page, setPage] = useState('examine');
  const [sessionId, setSessionId] = useState(null);
  const [filters, setFilters] = useState([]);
  const [filterSearch, setFilterSearch] = useState('');
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewOriginal, setPreviewOriginal] = useState(null);
  const [filterChain, setFilterChain] = useState([]);
  const [forensicCase, setForensicCase] = useState(null);
  const [custody, setCustody] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [evidenceId, setEvidenceId] = useState(null);
  const [evidenceHash, setEvidenceHash] = useState('');
  const [allHashes, setAllHashes] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [notes, setNotes] = useState([]);
  const [projectMeta, setProjectMeta] = useState({ project_id: null, name: 'Examination' });
  const [notesCollapsed, setNotesCollapsed] = useState(
    () => localStorage.getItem('chakshu.notesCollapsed') === '1',
  );
  const [compareId, setCompareId] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [toasts, setToasts] = useState([]);
  const [blockingOverlay, setBlockingOverlay] = useState(null);
  const [mediaPath, setMediaPath] = useState('');
  const [storagePath, setStoragePath] = useState('');
  const [mediaType, setMediaType] = useState('image');
  const [videoMeta, setVideoMeta] = useState(null);
  const [seekTime, setSeekTime] = useState(0);
  const [timeline, setTimeline] = useState(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [currentFrameMeta, setCurrentFrameMeta] = useState(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [audioChannels, setAudioChannels] = useState(null);
  const [regionStart, setRegionStart] = useState(0);
  const [regionEnd, setRegionEnd] = useState(10);
  const [regionAnalysis, setRegionAnalysis] = useState(null);
  const [calibration, setCalibration] = useState({ pixelsPerUnit: 1, unitName: 'px', deltaTime: null });
  const [examples, setExamples] = useState([]);
  const [selectedExample, setSelectedExample] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [subtitleForm, setSubtitleForm] = useState({
    subtitle_path: '',
    output_path: '~/Desktop/chakshu-subtitled.mp4',
    font_size: 22,
    margin_v: 28,
  });
  const [aiStatus, setAiStatus] = useState(null);
  const [aiTools, setAiTools] = useState([]);
  const [aiModels, setAiModels] = useState([]);
  const [aiTool, setAiTool] = useState('auto_enhance');
  const [aiModelId, setAiModelId] = useState('');
  const [aiStrength, setAiStrength] = useState(1.0);
  const [labFlash, setLabFlash] = useState('');
  const [autoOpenLab, setAutoOpenLab] = useState(
    () => localStorage.getItem('chakshu.autoOpenLab') !== '0',
  );
  const [showOriginalPreview, setShowOriginalPreview] = useState(
    () => localStorage.getItem('chakshu.showOriginalPreview') === '1',
  );
  const aiModelFileRef = useRef(null);
  const fileRef = useRef(null);
  const videoRef = useRef(null);
  const seekTimeRef = useRef(0);

  const [exportForm, setExportForm] = useState(loadExportFormFromStorage);

  const notify = useCallback((message, type = 'success') => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const setBlocking = useCallback((active, opts = {}) => {
    if (!active) {
      setBlockingOverlay(null);
      return;
    }
    setBlockingOverlay({
      message: opts.message || t('subtitle.burning', 'Processing…'),
      detail: opts.detail || '',
    });
  }, [t]);

  const refreshProjectNotes = useCallback(async () => {
    try {
      const r = await api.projectNotes();
      setNotes(r.notes || []);
      setProjectMeta({ project_id: r.project_id, name: r.project_name || 'Examination' });
    } catch {
      /* API may be offline */
    }
  }, []);

  const init = useCallback(async () => {
    try {
      const { session_id } = await api.createSession();
      setSessionId(session_id);
      const [flt, fc, proj] = await Promise.all([
        api.fetchFilters(),
        api.forensicsActiveCase(),
        api.projectCurrent(),
      ]);
      setFilters(flt.filters || []);
      setForensicCase(fc);
      if (proj?.export_settings) {
        setExportForm((f) => mergeExportSettings(f, proj.export_settings));
      }
      await refreshProjectNotes();
      setStatus(`${fc.display_id || fc.case_number} · ${flt.implemented_count || 0} forensic filters ready`);
    } catch (e) {
      setError(e.message);
      setStatus(t('status.api_offline', 'API offline — start: python -m aive.api.server'));
    }
  }, [t, refreshProjectNotes]);

  useEffect(() => { init(); }, [init]);

  useEffect(() => {
    saveExportFormToStorage(exportForm);
  }, [exportForm]);

  useEffect(() => {
    if (!labFlash) return undefined;
    const t = setTimeout(() => setLabFlash(''), 5000);
    return () => clearTimeout(t);
  }, [labFlash]);

  useEffect(() => {
    if (page !== 'examine' || !sessionId) return;
    api.forensicsPreview(sessionId)
      .then(handlePreview)
      .catch(() => {});
  }, [page, sessionId]);

  useEffect(() => {
    if (!status) setStatus(t('status.init', 'Initializing forensic services…'));
  }, [t, status]);

  const forensicFilters = useMemo(() => {
    const q = filterSearch.toLowerCase();
    let list = filters.filter((f) => f.implemented);
    if (!list.length) list = filters;
    if (!q) return list;
    return list.filter((f) => f.name.toLowerCase().includes(q) || f.id.includes(q));
  }, [filters, filterSearch]);

  const filterLabel = useCallback(
    (id) => filters.find((f) => f.id === id)?.name || id,
    [filters],
  );

  const handlePreview = (data) => {
    if (data.preview) setPreview(previewDataUrl(data.preview));
    if (data.preview_original) {
      setPreviewOriginal(previewDataUrl(data.preview_original));
    } else if (data.preview && !data.filter_chain?.length) {
      setPreviewOriginal(previewDataUrl(data.preview));
    }
    if (data.filter_chain) setFilterChain(data.filter_chain);
  };

  const applyToSession = useCallback((data, message, options = {}) => {
    const shouldOpen = options.openLab !== undefined ? options.openLab : autoOpenLab;
    if (data?.preview) handlePreview(data);
    if (data?.filter_chain) setFilterChain(data.filter_chain);
    if (message) {
      setLabFlash(message);
      setStatus(message);
    }
    if (shouldOpen && page !== 'examine') {
      setPage('examine');
    }
  }, [autoOpenLab, page]);

  const syncCapPreviewToSession = useCallback(async (capResult, timeSec, message) => {
    const path = exportForm.input_path || storagePath;
    const samePath = sessionId && storagePath && path
      && (storagePath === path || storagePath.endsWith(path) || path.endsWith(storagePath));
    if (samePath && sessionId != null && timeSec != null) {
      try {
        const r = await api.seekVideo(sessionId, timeSec);
        applyToSession(r, message);
        setSeekTime(timeSec);
        return;
      } catch (e) {
        setError(e.message);
      }
    }
    applyToSession(capResult, message || 'Preview updated — open Examination Lab to sync pipeline', {
      openLab: autoOpenLab,
    });
  }, [sessionId, storagePath, exportForm.input_path, autoOpenLab, applyToSession]);

  const showWorkflowBar = !['examine', 'capture', 'settings'].includes(page);

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setPreview(URL.createObjectURL(file));
    try {
      let sid = sessionId;
      if (!sid) {
        const s = await api.createSession();
        sid = s.session_id;
        setSessionId(sid);
      }
      const data = await api.uploadMedia(sid, file);
      handlePreview(data);
      const saved = data.storage_path || data.source_path || '';
      setStoragePath(saved);
      setMediaPath(file.name);
      setMediaType(data.media_type || 'image');
      if (data.evidence_id) setEvidenceId(data.evidence_id);
      setVideoMeta(data.metadata || null);
      setSeekTime(0);
      setExportForm((f) => ({ ...f, input_path: saved || file.name }));
      const fc = await api.forensicsActiveCase();
      setForensicCase(fc);
      if (fc.evidence?.length) {
        const last = fc.evidence[fc.evidence.length - 1];
        setEvidenceHash(last.sha256);
        setEvidenceId(last.evidence_id || null);
        if (!saved && last.storage_path) {
          setStoragePath(last.storage_path);
          setExportForm((f) => ({ ...f, input_path: last.storage_path }));
        }
      }
      if (data.media_type === 'video' && saved) {
        try {
          setTimelineLoading(true);
          const r = await api.timelineBuild(saved, 25000, false);
          setTimeline(r);
          setVideoMeta({ ...(data.metadata || {}), duration: r.duration, fps: r.fps, vfr: r.vfr });
          setVideoInfo({ duration: r.duration, fps: r.fps, frame_count: r.frame_sample_count });
        } catch { /* optional */ }
        finally { setTimelineLoading(false); }
      }
      const kind = data.media_type === 'video' ? 'Video' : 'Image';
      setStatus(`${kind} ingested: ${file.name}`);
    } catch (err) {
      setError(err.message);
    }
    e.target.value = '';
  };

  const applyFilter = async () => {
    if (!selectedFilter || !sessionId) return setError('Select filter and load evidence');
    try {
      const data = await api.forensicsApplyFilter(sessionId, selectedFilter.id);
      applyToSession(data, `Applied: ${selectedFilter.name}`, { openLab: false });
    } catch (e) {
      setError(e.message);
    }
  };

  const resetEnhancement = async () => {
    if (!sessionId) return;
    const data = await api.forensicsReset(sessionId);
    handlePreview(data);
    setFilterChain([]);
    setStatus('Restored to original master frame (non-destructive)');
  };

  const removeFilterAt = async (index) => {
    if (!sessionId) return;
    try {
      const data = await api.forensicsRemoveFilter(sessionId, index);
      handlePreview(data);
      setStatus(`Removed: ${filterLabel(data.removed_filter_id || filterChain[index])}`);
    } catch (e) {
      setError(e.message);
    }
  };

  const seekToFrame = async (f) => {
    if (!sessionId || !storagePath) return;
    playback.pause();
    try {
      const r = await api.seekVideo(sessionId, f.pts);
      handlePreview(r);
      setSeekTime(f.pts);
      setFrameIndex(f.index);
      setCurrentFrameMeta(f);
      if (videoRef.current) videoRef.current.currentTime = f.pts;
      setStatus(`Frame #${f.index} (${f.type}) @ ${f.pts.toFixed(3)}s`);
    } catch (e) { setError(e.message); }
  };

  const stepFrame = async (delta, useIframe = false) => {
    if (!sessionId) return;
    try {
      const r = await api.timelineStepFrame(sessionId, delta, useIframe);
      handlePreview(r);
      setSeekTime(r.time_sec);
      setFrameIndex(r.frame_index);
      if (r.frame_type || r.type) {
        setCurrentFrameMeta({ index: r.frame_index, pts: r.time_sec, type: r.frame_type || r.type });
      }
      if (videoRef.current) videoRef.current.currentTime = r.time_sec;
      setStatus(`Frame #${r.frame_index} @ ${r.time_sec?.toFixed(3)}s`);
    } catch (e) { setError(e.message); }
  };

  const playbackFps = timeline?.fps || videoMeta?.fps || videoInfo?.fps || 30;
  const videoPlaybackEnabled = mediaType === 'video' && Boolean(sessionId && storagePath);

  seekTimeRef.current = seekTime;

  const playback = useForensicPlayback({
    enabled: videoPlaybackEnabled,
    videoRef,
    fps: playbackFps,
    stepFrame,
    getCurrentTime: () => seekTimeRef.current,
  });

  const handlePlayReverse = useCallback(() => {
    if (seekTimeRef.current <= 0.001) {
      setStatus(t('playback.reverse_at_start', 'Seek forward before reverse playback'));
      return;
    }
    playback.playReverse();
  }, [playback, t]);

  const buildTimeline = async (forceRefresh = false) => {
    if (!storagePath) return setError('Load video first');
    setTimelineLoading(true);
    setError('');
    try {
      const r = await api.timelineBuild(storagePath, 25000, forceRefresh);
      setTimeline(r);
      setVideoMeta((m) => ({ ...m, duration: r.duration, fps: r.fps, vfr: r.vfr }));
      const q = r.index_quality === 'forensic' ? 'FORENSIC' : 'STANDARD';
      setStatus(`${q} index: ${r.frame_sample_count?.toLocaleString()} frames · I:${r.summary?.I} P:${r.summary?.P} B:${r.summary?.B}${r.from_cache ? ' (cache)' : ''}`);
    } catch (e) { setError(e.message); }
    finally { setTimelineLoading(false); }
  };

  const seekToTime = async (t, frameIdxHint = null) => {
    playback.pause();
    setSeekTime(t);
    if (videoRef.current) videoRef.current.currentTime = t;
    const near = timeline?.frames?.reduce((best, f) => (
      !best || Math.abs(f.pts - t) < Math.abs(best.pts - t) ? f : best
    ), null);
    if (near) setCurrentFrameMeta(near);
    if (frameIdxHint != null) setFrameIndex(frameIdxHint);
    if (!sessionId) return;
    try {
      const r = await api.seekVideo(sessionId, t);
      handlePreview(r);
      setFrameIndex(r.frame_index ?? frameIdxHint ?? near?.index ?? 0);
    } catch { /* scrub only */ }
  };

  const handleBookmarkApplyFilter = useCallback(async (filterId, params = {}) => {
    if (!sessionId) throw new Error(t('bookmark.need_session', 'Open Examination Lab with loaded evidence to jump'));
    const data = await api.forensicsApplyFilter(sessionId, filterId, params);
    applyToSession(data, `${t('bookmark.jumped', 'Jumped to bookmark')}: ${filterLabel(filterId)}`, { openLab: false });
  }, [sessionId, applyToSession, filterLabel, t]);

  const loadCustody = async () => {
    if (!forensicCase?.case_id) return;
    const data = await api.forensicsCustody(forensicCase.case_id);
    setCustody(data.entries || []);
  };

  useEffect(() => {
    if (page === 'command') {
      api.capExamples().then((r) => setExamples(r.examples || [])).catch(() => {});
    }
    if (page === 'custody') loadCustody();
    if (page === 'tools') {
      Promise.all([api.aiStatus(), api.aiTools(), api.aiModels()])
        .then(([st, tools, models]) => {
          setAiStatus(st);
          setAiTools(tools.tools || []);
          setAiModels(models.models || []);
        })
        .catch(() => {});
    }
  }, [page, forensicCase?.case_id]);

  const handleLiveIngest = (data) => {
    handlePreview(data);
    if (data.storage_path) setStoragePath(data.storage_path);
    setMediaType(data.media_type || 'image');
    setPage('examine');
  };

  const markupMediaId = useMemo(
    () => storagePath || evidenceId || sessionId || 'default',
    [storagePath, evidenceId, sessionId],
  );

  const caseLabel = forensicCase?.display_id || forensicCase?.case_number || forensicCase?.case_id || '—';

  const mediaIdLabel = () => {
    const id = storagePath || mediaPath || '—';
    return id.length > 40 ? `…${id.slice(-36)}` : id;
  };

  return (
    <div className={`fx-app${blockingOverlay ? ' fx-app-blocked' : ''}`}>
      <aside className="fx-sidebar">
        <div className="fx-brand">
          <h1>{PRODUCT_FULL}</h1>
          <p>{t('app.tagline', 'Digital Media Examination Platform')}</p>
        </div>
        <nav className="fx-nav">
          {NAV_KEYS.map((n) => (
            <button
              key={n.id}
              type="button"
              className={`fx-nav-btn ${page === n.id ? 'active' : ''}`}
              onClick={() => setPage(n.id)}
            >
              {t(n.key, n.id)}
            </button>
          ))}
        </nav>
        <SidebarFooter
          caseLabel={caseLabel}
          caseId={forensicCase?.case_id}
          examiner={forensicCase?.examiner}
          onOpenSettings={() => setPage('settings')}
        />
      </aside>

      <div className="fx-workspace">
      <div className="fx-main-column">
      <div className="fx-main">
        <header className="fx-topbar">
          <div>
            <strong>{forensicCase?.title || 'Examination'}</strong>
            <span className="case-id" style={{ marginLeft: 12 }} title={forensicCase?.case_id}>{caseLabel}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="fx-btn" onClick={() => fileRef.current?.click()}>{t('action.ingest', 'Ingest Evidence')}</button>
            <button type="button" className="fx-btn fx-btn-primary" onClick={() => setPage('examine')}>{t('action.examination_lab', 'Examination Lab')}</button>
          </div>
        </header>

        <ExamCompareDock
          visible={showWorkflowBar}
          originalSrc={previewOriginal || preview}
          enhancedSrc={preview}
          filterChain={filterChain}
          filterLabel={filterLabel}
          lastAction={labFlash}
          pathLabel={mediaIdLabel()}
          hasPreview={Boolean(preview)}
          mediaType={mediaType}
          showOriginal={showOriginalPreview}
          onShowOriginalChange={(v) => {
            setShowOriginalPreview(v);
            localStorage.setItem('chakshu.showOriginalPreview', v ? '1' : '0');
          }}
          t={t}
          autoOpenLab={autoOpenLab}
          onAutoOpenLabChange={(v) => {
            setAutoOpenLab(v);
            localStorage.setItem('chakshu.autoOpenLab', v ? '1' : '0');
          }}
          onOpenLab={() => setPage('examine')}
          onIngest={() => fileRef.current?.click()}
        />

        {page === 'settings' && (
          <div className="fx-content">
            <LocaleSettings />
          </div>
        )}

        {page === 'command' && (
          <div className="fx-content">
            <div className="fx-stat-row">
              <div className="fx-stat"><div className="val">{forensicCase?.evidence?.length || 0}</div><div className="lbl">Evidence Items</div></div>
              <div className="fx-stat"><div className="val">{filters.filter((f) => f.implemented).length}</div><div className="lbl">Forensic Filters</div></div>
              <div className="fx-stat"><div className="val">{filterChain.length}</div><div className="lbl">Pipeline Steps</div></div>
              <div className="fx-stat"><div className="val">{analysis?.summary?.I ?? '—'}</div><div className="lbl">I-Frames (last scan)</div></div>
            </div>
            {evidenceHash && (
              <div className="fx-panel">
                <div className="fx-panel-head">Evidence Integrity (SHA-256)</div>
                <div className="fx-panel-body"><div className="fx-hash">{evidenceHash}</div></div>
              </div>
            )}
            <div className="fx-panel cap-examples">
              <div className="fx-panel-head">Learning & Example Workflows</div>
              <div className="fx-panel-body">
                {examples.map((ex) => (
                  <div
                    key={ex.id}
                    className="cap-example-card"
                    onClick={async () => {
                      try {
                        const r = await api.capExample(ex.id);
                        setSelectedExample(r.workflow || { title: ex.title, steps: ex.steps });
                        setStatus(`Loaded example: ${ex.title}`);
                      } catch (e) { setError(e.message); }
                    }}
                  >
                    <h4>{ex.title}</h4>
                    <p>{ex.description || ex.phase}</p>
                  </div>
                ))}
                {selectedExample && (
                  <div style={{ marginTop: 12, fontSize: '0.75rem', color: 'var(--fx-muted)' }}>
                    <strong>{selectedExample.title}</strong>
                    <ol style={{ paddingLeft: 18, marginTop: 6 }}>
                      {(selectedExample.steps || []).map((s, i) => <li key={i}>{s}</li>)}
                    </ol>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {page === 'capture' && (
          <div className="fx-content">
            <LiveCapture
              sessionId={sessionId}
              filters={filters}
              onIngest={handleLiveIngest}
              onStatus={setStatus}
              onError={setError}
            />
          </div>
        )}

        {page === 'examine' && (
          <div className="fx-content fx-grid-examine">
            <div className="fx-panel">
              <div className="fx-panel-head">Enhancement Pipeline</div>
              <div className="fx-panel-body">
                <input className="fx-input" placeholder="Search filters…" value={filterSearch} onChange={(e) => setFilterSearch(e.target.value)} />
                <div style={{ display: 'flex', gap: 6, margin: '10px 0' }}>
                  <button type="button" className="fx-btn fx-btn-primary" onClick={applyFilter} disabled={!selectedFilter}>Apply</button>
                  <button type="button" className="fx-btn fx-btn-danger" onClick={resetEnhancement}>Reset to Original</button>
                </div>
                <div style={{ maxHeight: 320, overflow: 'auto', border: '1px solid var(--fx-border)', borderRadius: 6 }}>
                  {forensicFilters.slice(0, 100).map((f) => (
                    <div
                      key={f.id}
                      className={`fx-filter-item ${selectedFilter?.id === f.id ? 'selected' : ''}`}
                      onClick={() => setSelectedFilter(f)}
                    >
                      <span>{f.name}</span>
                      <span className={`fx-badge ${f.implemented ? 'fx-badge-live' : 'fx-badge-cat'}`}>
                        {f.implemented ? 'FORENSIC' : 'CAT'}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="fx-pipeline">
                  {filterChain.length === 0 && (
                    <span style={{ fontSize: '0.7rem', color: 'var(--fx-muted)' }}>No filters in pipeline</span>
                  )}
                  {filterChain.map((id, index) => (
                    <span key={`${id}-${index}`} className="fx-pipeline-chip">
                      <span className="fx-pipeline-step">{index + 1}.</span>
                      <span className="fx-pipeline-label" title={id}>{filterLabel(id)}</span>
                      <button
                        type="button"
                        className="fx-pipeline-remove"
                        title={`Remove ${filterLabel(id)}`}
                        aria-label={`Remove filter ${filterLabel(id)}`}
                        onClick={() => removeFilterAt(index)}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="fx-panel">
              <div className="fx-panel-head">
                Frame Examination (Non-destructive)
                {mediaType === 'video' && <span className="fx-badge fx-badge-live" style={{ marginLeft: 8 }}>VIDEO</span>}
              </div>
              <CompareFrameView
                originalSrc={previewOriginal || preview}
                enhancedSrc={preview}
                flash={Boolean(labFlash)}
                variant="lab"
                compareEnabled={mediaType === 'image'}
                showOriginal={showOriginalPreview}
                onShowOriginalChange={mediaType === 'image' ? (v) => {
                  setShowOriginalPreview(v);
                  localStorage.setItem('chakshu.showOriginalPreview', v ? '1' : '0');
                } : undefined}
                t={t}
              />
              {mediaType === 'video' && storagePath && (
                <div className="fx-panel-body" style={{ borderTop: '1px solid var(--fx-border)' }}>
                  <video
                    ref={videoRef}
                    src={api.mediaServeUrl(storagePath)}
                    controls
                    style={{ width: '100%', maxHeight: 180, background: '#000' }}
                    onTimeUpdate={(e) => {
                      if (playback.direction !== 'reverse') setSeekTime(e.target.currentTime);
                    }}
                    onPlay={() => {
                      if (playback.direction === 'reverse') videoRef.current?.pause();
                    }}
                  />
                  <ForensicVideoTransport
                    t={t}
                    direction={playback.direction}
                    speed={playback.speed}
                    onSpeedChange={playback.setSpeed}
                    onPlayForward={playback.playForward}
                    onPlayReverse={handlePlayReverse}
                    onPause={playback.pause}
                    onStepBack={() => { playback.pause(); stepFrame(-1); }}
                    onStepForward={() => { playback.pause(); stepFrame(1); }}
                    onStepIframe={() => { playback.pause(); stepFrame(1, true); }}
                    disabled={!sessionId}
                    compact
                  />
                  <div style={{ marginTop: 8 }}>
                    <label style={{ fontSize: '0.7rem', color: 'var(--fx-muted)' }}>
                      Scrub frame (server) — {seekTime.toFixed(2)}s
                      {videoMeta?.duration ? ` / ${Number(videoMeta.duration).toFixed(1)}s` : ''}
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={videoMeta?.duration || videoInfo?.duration || 120}
                      step={0.05}
                      value={seekTime}
                      style={{ width: '100%' }}
                      onChange={(e) => {
                        playback.pause();
                        setSeekTime(Number(e.target.value));
                      }}
                    />
                    <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                      <button
                        type="button"
                        className="fx-btn fx-btn-primary"
                        onClick={async () => {
                          playback.pause();
                          try {
                            const r = await api.seekVideo(sessionId, seekTime);
                            handlePreview(r);
                            setStatus(`Examining frame at ${seekTime.toFixed(2)}s`);
                          } catch (err) { setError(err.message); }
                        }}
                      >
                        Load Frame at Time
                      </button>
                      <button
                        type="button"
                        className="fx-btn"
                        onClick={async () => {
                          if (!storagePath) return;
                          try {
                            const r = await api.capSeekIframe(storagePath, seekTime);
                            if (r.preview) setPreview(previewDataUrl(r.preview));
                            setStatus(`I-frame near ${seekTime.toFixed(2)}s`);
                          } catch (err) { setError(err.message); }
                        }}
                      >
                        Nearest I-Frame
                      </button>
                    </div>
                  </div>
                  {!storagePath.startsWith('/') && (
                    <p style={{ color: 'var(--fx-danger)', fontSize: '0.7rem', marginTop: 6 }}>
                      Video tools need a saved path. Re-ingest the file or use Load by Path below.
                    </p>
                  )}
                </div>
              )}
              <div className="fx-panel-body">
                <div className="fx-form-row" style={{ marginBottom: 8 }}>
                  <label style={{ color: 'var(--fx-muted)', fontSize: '0.7rem' }}>LOAD BY FULL PATH (video/image)</label>
                  <input
                    className="fx-input"
                    placeholder="/Users/you/Desktop/evidence.mp4"
                    value={exportForm.input_path}
                    onChange={(e) => setExportForm({ ...exportForm, input_path: e.target.value })}
                  />
                  <button
                    type="button"
                    className="fx-btn"
                    style={{ marginTop: 6 }}
                    onClick={async () => {
                      if (!sessionId || !exportForm.input_path) return;
                      try {
                        const r = await api.loadMediaPath(sessionId, exportForm.input_path);
                        handlePreview(r);
                        setStoragePath(r.storage_path || exportForm.input_path);
                        setMediaType(r.media_type || 'image');
                        setVideoMeta(r.metadata || null);
                        setStatus(`Loaded: ${r.media_type}`);
                      } catch (err) { setError(err.message); }
                    }}
                  >
                    Load Path
                  </button>
                </div>
                <AudioPlayer src={mediaType === 'video' && storagePath ? api.mediaServeUrl(storagePath) : null} label="Audio track" />
              </div>
            </div>

            <div className="fx-panel">
              <div className="fx-panel-head">Stream Analysis</div>
              <div className="fx-panel-body">
                <div className="fx-form-row" style={{ marginBottom: 10 }}>
                  <label style={{ color: 'var(--fx-muted)', fontSize: '0.7rem' }}>VIDEO PATH (full path)</label>
                  <input className="fx-input" value={exportForm.input_path} onChange={(e) => setExportForm({ ...exportForm, input_path: e.target.value })} />
                </div>
                <button
                  type="button"
                  className="fx-btn"
                  onClick={async () => {
                    try {
                      const r = await api.forensicsAnalyzeVideo(exportForm.input_path);
                      setAnalysis(r);
                      setStatus(`I:${r.summary?.I} P:${r.summary?.P} B:${r.summary?.B}`);
                    } catch (e) { setError(e.message); }
                  }}
                >
                  Analyze I/P/B Frames
                </button>
                {analysis && (
                  <table className="fx-table" style={{ marginTop: 12 }}>
                    <tbody>
                      {Object.entries(analysis.summary || {}).map(([k, v]) => (
                        <tr key={k}><td>{k}</td><td>{v}</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            <BookmarksPanel
              t={t}
              mediaPath={exportForm.input_path || storagePath}
              sessionId={sessionId}
              frameIndex={frameIndex}
              timeSec={seekTime}
              selectedFilter={selectedFilter}
              filterChain={filterChain}
              filterLabel={filterLabel}
              onSeek={seekToTime}
              onApplyFilter={handleBookmarkApplyFilter}
              setStatus={setStatus}
              setError={setError}
              notify={notify}
            />
          </div>
        )}

        {page === 'markup' && (
          <div className="fx-content">
            <div className="fx-panel">
              <div className="fx-panel-head">Phase 3 — Annotations, Redaction &amp; Measurement</div>
              <div className="fx-panel-body">
                <div style={{ display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Calibration (px per unit)</label>
                    <input
                      type="number"
                      className="fx-input"
                      value={calibration.pixelsPerUnit}
                      onChange={(e) => setCalibration({ ...calibration, pixelsPerUnit: Number(e.target.value) || 1 })}
                      style={{ width: 100 }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Unit</label>
                    <input
                      className="fx-input"
                      value={calibration.unitName}
                      onChange={(e) => setCalibration({ ...calibration, unitName: e.target.value })}
                      style={{ width: 80 }}
                    />
                  </div>
                  {mediaType === 'video' && (
                    <div>
                      <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Δt for speed (sec)</label>
                      <input
                        type="number"
                        step="0.001"
                        className="fx-input"
                        value={calibration.deltaTime ?? ''}
                        onChange={(e) => setCalibration({ ...calibration, deltaTime: e.target.value ? Number(e.target.value) : null })}
                        style={{ width: 100 }}
                      />
                    </div>
                  )}
                  <span style={{ fontSize: '0.7rem', color: 'var(--fx-muted)' }}>
                    Frame #{frameIndex} · {mediaIdLabel()}
                  </span>
                </div>
                <ExamCanvas
                  imageSrc={preview}
                  sessionId={sessionId}
                  mediaId={markupMediaId}
                  frameIndex={frameIndex}
                  timeSec={seekTime}
                  pixelsPerUnit={calibration.pixelsPerUnit}
                  unitName={calibration.unitName}
                  deltaTimeSec={calibration.deltaTime}
                  onPreviewUpdate={setPreview}
                  onStatus={setStatus}
                  onError={setError}
                />
              </div>
            </div>
          </div>
        )}

        {page === 'timeline' && (
          <div className="fx-content ftl-page">
            <ForensicTimeline
              timeline={timeline}
              currentTime={seekTime}
              loading={timelineLoading}
              onSeek={seekToTime}
              onRegionSelect={(a, b) => {
                setRegionStart(Math.round(a * 100) / 100);
                setRegionEnd(Math.round(b * 100) / 100);
                setRegionAnalysis(null);
              }}
            />
            <div className="ftl-studio">
              <div>
                <div className="ftl-viewer">
                  {preview ? (
                    <img src={preview} alt="Frame" />
                  ) : storagePath ? (
                    <video
                      ref={videoRef}
                      src={api.mediaServeUrl(storagePath)}
                      controls
                      style={{ width: '100%', height: '100%' }}
                      onTimeUpdate={(e) => {
                        if (playback.direction !== 'reverse') setSeekTime(e.target.currentTime);
                      }}
                      onPlay={() => {
                        if (playback.direction === 'reverse') videoRef.current?.pause();
                      }}
                    />
                  ) : (
                    <span style={{ color: '#555' }}>Load video evidence</span>
                  )}
                </div>
              </div>
              <div className="ftl-side-card">
                <div className="ftl-transport">
                  <button type="button" className="fx-btn fx-btn-primary" onClick={() => buildTimeline(false)} disabled={!storagePath || timelineLoading}>
                    Deep Index
                  </button>
                  <button type="button" className="fx-btn" onClick={() => buildTimeline(true)} disabled={!storagePath || timelineLoading} title="Rebuild index">↻</button>
                </div>
                <ForensicVideoTransport
                  t={t}
                  direction={playback.direction}
                  speed={playback.speed}
                  onSpeedChange={playback.setSpeed}
                  onPlayForward={playback.playForward}
                  onPlayReverse={handlePlayReverse}
                  onPause={playback.pause}
                  onStepBack={() => { playback.pause(); stepFrame(-1); }}
                  onStepForward={() => { playback.pause(); stepFrame(1); }}
                  onStepIframe={() => { playback.pause(); stepFrame(1, true); }}
                  disabled={!sessionId}
                />
                <div className="ftl-frame-meta">
                  <div><strong>Timecode</strong> {formatTc(seekTime, timeline?.fps || 30)}</div>
                  <div><strong>Frame</strong> #{frameIndex}{currentFrameMeta ? ` · ${currentFrameMeta.type}` : ''}</div>
                  <div><strong>PTS</strong> {seekTime.toFixed(4)}s</div>
                  {currentFrameMeta?.size && <div><strong>Size</strong> {currentFrameMeta.size} B</div>}
                  <div style={{ marginTop: 10 }}><strong>Evidence</strong><br />{mediaIdLabel()}</div>
                </div>
                <div style={{ marginTop: 14 }}>
                  <div className="ftl-section-label">Region Analysis</div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <input type="number" className="fx-input" value={regionStart} onChange={(e) => setRegionStart(Number(e.target.value))} step="0.1" />
                    <input type="number" className="fx-input" value={regionEnd} onChange={(e) => setRegionEnd(Number(e.target.value))} step="0.1" />
                  </div>
                  <button type="button" className="fx-btn fx-btn-primary" style={{ marginTop: 8, width: '100%' }} onClick={async () => {
                    try {
                      const r = await api.timelineRegion(storagePath, regionStart, regionEnd);
                      setRegionAnalysis(r);
                    } catch (e) { setError(e.message); }
                  }}>Analyze Region</button>
                  {regionAnalysis && (
                    <div style={{ marginTop: 8, fontSize: '0.7rem', color: 'var(--fx-muted)', fontFamily: 'var(--fx-mono)' }}>
                      {regionAnalysis.frame_count} frames · I:{regionAnalysis.types?.I ?? 0} P:{regionAnalysis.types?.P ?? 0} B:{regionAnalysis.types?.B ?? 0}
                    </div>
                  )}
                </div>
                <div style={{ marginTop: 14 }}>
                  <div className="ftl-section-label">Audio &amp; Sync</div>
                  <div className="ftl-audio-row">
                    <button type="button" className="fx-btn" onClick={async () => {
                      try {
                        const r = await api.timelineAudioChannels(storagePath);
                        setAudioChannels(r);
                      } catch (e) { setError(e.message); }
                    }}>Probe</button>
                    <button type="button" className="fx-btn" onClick={async () => {
                      try {
                        const r = await api.timelineAvOffset(storagePath);
                        setStatus(`A/V offset: ${r.recommendation_ms} ms`);
                      } catch (e) { setError(e.message); }
                    }}>A/V Offset</button>
                  </div>
                  {audioChannels?.streams?.map((s, i) => (
                    <div key={i} style={{ fontSize: '0.68rem', marginTop: 6, color: 'var(--fx-muted)' }}>
                      Ch {s.index}: {s.codec} · {s.layout} · {s.channels}ch
                    </div>
                  ))}
                  <AudioPlayer src={storagePath ? api.mediaServeUrl(storagePath) : null} label="Synced audio" />
                </div>
                {mediaType === 'video' && storagePath && (
                  <>
                    <AudioRedactionPanel
                      t={t}
                      inputPath={exportForm.input_path || storagePath}
                      outputDir={exportForm.output_dir}
                      playheadSec={seekTime}
                      selectionStart={regionStart}
                      selectionEnd={regionEnd}
                      setStatus={setStatus}
                      setError={setError}
                    />
                    <AudioStreamPanel
                      t={t}
                      videoPath={exportForm.input_path || storagePath}
                      outputDir={exportForm.output_dir}
                      setStatus={setStatus}
                      setError={setError}
                      notify={notify}
                    />
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {page === 'tools' && (
          <div className="fx-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <AudioRedactionPanel
              t={t}
              inputPath={exportForm.input_path}
              outputDir={exportForm.output_dir}
              playheadSec={seekTime}
              selectionStart={regionStart}
              selectionEnd={regionEnd}
              setStatus={setStatus}
              setError={setError}
            />
            <AudioStreamPanel
              t={t}
              videoPath={exportForm.input_path || storagePath}
              outputDir={exportForm.output_dir}
              setStatus={setStatus}
              setError={setError}
              notify={notify}
            />
            <div className="fx-panel" style={{ gridColumn: '1 / -1' }}>
              <div className="fx-panel-head">AI / ML Enhancement (R-090, R-091)</div>
              <div className="fx-panel-body">
                <p style={{ fontSize: '0.75rem', color: 'var(--fx-muted)', marginTop: 0 }}>
                  Built-in AI-style tools work without ONNX. Changes update the live preview bar above and sync to
                  <strong> Examination Lab</strong> (enable “Open Examination Lab after apply” or click the button).
                  {aiStatus && (
                    <span>
                      {' '}ONNX runtime: {aiStatus.onnxruntime_available ? `yes (${aiStatus.onnxruntime_version})` : 'not installed — pip install onnxruntime'}
                    </span>
                  )}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 120px auto', gap: 8, alignItems: 'end', marginTop: 10 }}>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Tool</label>
                    <select className="fx-input" value={aiTool} onChange={(e) => {
                      setAiTool(e.target.value);
                      if (e.target.value !== 'custom_onnx') setAiModelId('');
                    }}>
                      {aiTools.filter((t) => !t.id?.startsWith('model:')).map((t) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Custom model (optional)</label>
                    <select className="fx-input" value={aiModelId} onChange={(e) => {
                      setAiModelId(e.target.value);
                      if (e.target.value) setAiTool('custom_onnx');
                    }}>
                      <option value="">— built-in only —</option>
                      {aiModels.map((m) => (
                        <option key={m.id} value={m.id}>{m.name} ({m.task})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.65rem', color: 'var(--fx-muted)' }}>Strength {aiStrength.toFixed(1)}</label>
                    <input type="range" min={0.1} max={3} step={0.1} value={aiStrength} onChange={(e) => setAiStrength(Number(e.target.value))} style={{ width: '100%' }} />
                  </div>
                  <button type="button" className="fx-btn fx-btn-primary" disabled={!sessionId} onClick={async () => {
                    try {
                      const r = await api.aiEnhanceSession({
                        session_id: sessionId,
                        tool: aiModelId ? 'custom_onnx' : aiTool,
                        model_id: aiModelId,
                        strength: aiStrength,
                      });
                      applyToSession(r, `AI applied: ${aiModelId || aiTool}`);
                    } catch (e) { setError(e.message); }
                  }}>Apply to Frame</button>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                  <button type="button" className="fx-btn" onClick={() => aiModelFileRef.current?.click()}>Import ONNX Model</button>
                  <button type="button" className="fx-btn" onClick={async () => {
                    const p = prompt('Full path to .onnx on this machine:', '');
                    if (!p) return;
                    try {
                      await api.aiImportModelPath({ path: p });
                      const models = await api.aiModels();
                      setAiModels(models.models || []);
                      setStatus('Model imported');
                    } catch (e) { setError(e.message); }
                  }}>Import from Path</button>
                  {aiModelId && (
                    <button type="button" className="fx-btn" onClick={async () => {
                      if (!confirm(`Remove model ${aiModelId}?`)) return;
                      try {
                        await api.aiDeleteModel(aiModelId);
                        setAiModelId('');
                        const models = await api.aiModels();
                        setAiModels(models.models || []);
                        setStatus('Model removed');
                      } catch (e) { setError(e.message); }
                    }}>Delete Selected Model</button>
                  )}
                </div>
                {aiModels.length > 0 && (
                  <ul style={{ marginTop: 10, fontSize: '0.7rem', color: 'var(--fx-muted)' }}>
                    {aiModels.map((m) => (
                      <li key={m.id}><strong>{m.name}</strong> — {m.task} · {m.id}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Multi-Algorithm Hash Verification</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn fx-btn-primary" onClick={async () => {
                  try {
                    const r = await api.capHashFile(exportForm.input_path);
                    setAllHashes(r.hashes);
                    setStatus('Computed MD5, SHA-1, SHA-256, SHA-512');
                  } catch (e) { setError(e.message); }
                }}>Hash Evidence File</button>
                {allHashes && (
                  <div style={{ marginTop: 10, fontSize: '0.7rem' }}>
                    {Object.entries(allHashes).map(([k, v]) => (
                      <div key={k} className="fx-hash"><strong>{k}:</strong> {v}</div>
                    ))}
                  </div>
                )}
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={async () => {
                  try {
                    const r = await api.capSecureCopy({
                      source: exportForm.input_path,
                      destination: `${exportForm.output_dir}/secure-copy`,
                      report_path: `${exportForm.output_dir}/copy-report.json`,
                    });
                    setStatus(r.verified ? 'Secure copy verified' : 'Copy completed — verify hashes');
                  } catch (e) { setError(e.message); }
                }}>Secure Copy + Report</button>
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Video Seek & I-Frame</div>
              <div className="fx-panel-body">
                <input type="range" min={0} max={videoInfo?.duration || 60} step={0.1} value={seekTime} onChange={(e) => setSeekTime(Number(e.target.value))} style={{ width: '100%' }} />
                <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                  <button type="button" className="fx-btn" onClick={async () => {
                    try {
                      const r = await api.capVideoInfo(exportForm.input_path);
                      setVideoInfo(r);
                      setStatus(`Duration: ${r.duration}s · ${r.frame_count} frames`);
                    } catch (e) { setError(e.message); }
                  }}>Probe Video</button>
                  <button type="button" className="fx-btn fx-btn-primary" onClick={async () => {
                    try {
                      const r = await api.capSeekTime(exportForm.input_path, seekTime);
                      await syncCapPreviewToSession(r, seekTime, `Frame at ${seekTime.toFixed(2)}s`);
                    } catch (e) { setError(e.message); }
                  }}>Seek Time</button>
                  <button type="button" className="fx-btn" onClick={async () => {
                    try {
                      const r = await api.capSeekIframe(exportForm.input_path, seekTime);
                      await syncCapPreviewToSession(r, seekTime, `I-frame near ${seekTime.toFixed(2)}s`);
                    } catch (e) { setError(e.message); }
                  }}>Nearest I-Frame</button>
                </div>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={async () => {
                  try {
                    const r = await api.capMpegViz(exportForm.input_path, seekTime, 'macroblock');
                    if (sessionId) {
                      applyToSession(r, 'Macroblock overlay preview');
                    } else {
                      applyToSession(r, 'Macroblock overlay — ingest in Examination Lab to edit', { openLab: true });
                    }
                  } catch (e) { setError(e.message); }
                }}>MPEG Macroblock Overlay</button>
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Compare & Overlay</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn" onClick={async () => {
                  try {
                    const left = exportForm.input_path;
                    const right = prompt('Second file path for comparison:', left) || left;
                    const r = await api.capCompareCreate(left, right);
                    setCompareId(r.session_id);
                    setStatus('Comparison session created');
                  } catch (e) { setError(e.message); }
                }}>Start Side-by-Side</button>
                {compareId && (
                  <button type="button" className="fx-btn fx-btn-primary" style={{ marginLeft: 6 }} onClick={async () => {
                    try {
                      const r = await api.capCompareRender({ session_id: compareId, left_time: seekTime, right_time: seekTime });
                      applyToSession(r, 'Comparison rendered');
                    } catch (e) { setError(e.message); }
                  }}>Render Compare</button>
                )}
                <button type="button" className="fx-btn" style={{ marginTop: 8, display: 'block' }} onClick={async () => {
                  if (!sessionId) return;
                  try {
                    const r = await api.capOverlay(sessionId, { timestamp_text: new Date().toISOString(), grid: true });
                    applyToSession(r, 'Timestamp + grid applied');
                  } catch (e) { setError(e.message); }
                }}>Apply Timestamp + Grid</button>
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Clipboard Export (R-134)</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn fx-btn-primary" disabled={!sessionId} onClick={async () => {
                  try {
                    const r = await api.capClipboardFrame(sessionId, true);
                    await navigator.clipboard.writeText(r.data_url || r.base64);
                    setStatus(`Frame copied (${r.width}×${r.height}) · SHA-256 in response`);
                  } catch (e) { setError(e.message); }
                }}>Copy Frame to Clipboard</button>
                <button type="button" className="fx-btn" style={{ marginLeft: 6 }} disabled={!allHashes} onClick={async () => {
                  try {
                    const text = Object.entries(allHashes || {}).map(([k, v]) => `${k}: ${v}`).join('\n');
                    await navigator.clipboard.writeText(text);
                    setStatus('Hashes copied to clipboard');
                  } catch (e) { setError(e.message); }
                }}>Copy Hashes</button>
              </div>
            </div>
            <BookmarksPanel
              t={t}
              mediaPath={exportForm.input_path || storagePath}
              sessionId={sessionId}
              frameIndex={frameIndex}
              timeSec={seekTime}
              selectedFilter={selectedFilter}
              filterChain={filterChain}
              filterLabel={filterLabel}
              onSeek={seekToTime}
              onApplyFilter={handleBookmarkApplyFilter}
              setStatus={setStatus}
              setError={setError}
              notify={notify}
            />
            <SubtitlePanel
              t={t}
              videoPath={exportForm.input_path}
              outputDir={exportForm.output_dir}
              sessionId={sessionId}
              playheadSec={seekTime}
              fontSize={subtitleForm.font_size}
              marginV={subtitleForm.margin_v}
              onFontSizeChange={(v) => setSubtitleForm((f) => ({ ...f, font_size: v }))}
              onMarginVChange={(v) => setSubtitleForm((f) => ({ ...f, margin_v: v }))}
              outputPath={subtitleForm.output_path}
              onOutputPathChange={(p) => setSubtitleForm((f) => ({ ...f, output_path: p }))}
              onApplyPreview={(data, msg) => applyToSession(data, msg, { openLab: false })}
              setStatus={setStatus}
              setError={setError}
              notify={notify}
              onBlockingChange={setBlocking}
            />
            <div className="fx-panel">
              <div className="fx-panel-head">Stream Sync &amp; Merge (R-172 / R-173)</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn" onClick={async () => {
                  try {
                    const second = prompt('Second video path for sync search:', exportForm.input_path) || exportForm.input_path;
                    const r = await api.capStreamSync({
                      path_a: exportForm.input_path,
                      path_b: second,
                      time_a: seekTime,
                      search_sec: 3,
                    });
                    setSyncResult(r);
                    setStatus(r.recommended_offset_ms != null
                      ? `Best offset: ${r.recommended_offset_ms} ms (score ${r.best_score})`
                      : `Similarity: ${r.similarity?.score}`);
                  } catch (e) { setError(e.message); }
                }}>Find Stream Offset</button>
                {syncResult && (
                  <div style={{ marginTop: 8, fontSize: '0.68rem', fontFamily: 'var(--fx-mono)', color: 'var(--fx-muted)' }}>
                    {JSON.stringify(syncResult, null, 0).slice(0, 200)}…
                  </div>
                )}
                <p className="fx-export-hint" style={{ marginTop: 8 }}>
                  {t('audio_mux.use_panel', 'Add or replace audio tracks using the Add Audio Stream panel above.')}
                </p>
                <button type="button" className="fx-btn" style={{ marginTop: 6, display: 'block' }} onClick={async () => {
                  try {
                    const second = prompt('Second video to append:', exportForm.input_path);
                    if (!second) return;
                    const r = await api.capMergeVideos({
                      paths: [exportForm.input_path, second],
                      output_path: `${exportForm.output_dir}/concat.mp4`,
                    });
                    setStatus(r.success ? `Concatenated ${r.segment_count} clips` : (r.stderr || 'Concat failed'));
                  } catch (e) { setError(e.message); }
                }}>Concat Videos</button>
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Advanced Video (Phase 6)</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn" onClick={async () => {
                  try {
                    const r = await api.capAdvancedStabilize({
                      input_path: exportForm.input_path,
                      output_path: `${exportForm.output_dir}/stabilized.mp4`,
                    });
                    setStatus(r.success ? `Stabilized (${r.method || 'ok'})` : (r.stderr || 'Failed'));
                  } catch (e) { setError(e.message); }
                }}>Stabilize</button>
                <button type="button" className="fx-btn" style={{ marginLeft: 6 }} onClick={async () => {
                  try {
                    const r = await api.capAdvancedReverse({
                      input_path: exportForm.input_path,
                      output_path: `${exportForm.output_dir}/reversed.mp4`,
                    });
                    setStatus(r.success ? 'Reversed video exported' : (r.stderr || 'Failed'));
                  } catch (e) { setError(e.message); }
                }}>Reverse</button>
                <button type="button" className="fx-btn" style={{ marginTop: 6, display: 'block' }} onClick={async () => {
                  try {
                    const fps = Number(prompt('Target FPS:', '15') || '15');
                    const r = await api.capAdvancedFps({
                      input_path: exportForm.input_path,
                      output_path: `${exportForm.output_dir}/fps-adjusted.mp4`,
                      target_fps: fps,
                    });
                    setStatus(r.success ? `FPS adjusted to ${fps}` : (r.stderr || 'Failed'));
                  } catch (e) { setError(e.message); }
                }}>Adjust FPS</button>
              </div>
            </div>
          </div>
        )}

        {page === 'custody' && (
          <div className="fx-content">
            <div className="fx-panel">
              <div className="fx-panel-head">Chain of Custody Log</div>
              <div className="fx-panel-body">
                <table className="fx-table">
                  <thead>
                    <tr><th>Time</th><th>Action</th><th>Actor</th><th>File</th><th>Notes</th></tr>
                  </thead>
                  <tbody>
                    {custody.map((c, i) => (
                      <tr key={i}>
                        <td>{c.timestamp}</td>
                        <td>{c.action}</td>
                        <td>{c.actor}</td>
                        <td>{c.filename}</td>
                        <td>{c.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {page === 'export' && (
          <LegalExportPanel
            exportForm={exportForm}
            setExportForm={setExportForm}
            sessionId={sessionId}
            forensicCase={forensicCase}
            hasPreview={Boolean(preview)}
            t={t}
            setStatus={setStatus}
            setError={setError}
          />
        )}

        {page === 'reports' && (
          <div className="fx-content">
            <CaseReportsPanel
              t={t}
              forensicCase={forensicCase}
              exportForm={exportForm}
              locale={locale}
              setStatus={setStatus}
              setError={setError}
              notify={notify}
            />
          </div>
        )}

        <footer className="fx-statusbar">
          {status}
          {error && <span style={{ color: 'var(--fx-danger)' }}> | {error}</span>}
        </footer>
        {toasts.length > 0 && (
          <div className="fx-toast-stack" aria-live="polite">
            {toasts.map((toast) => (
              <div key={toast.id} className={`fx-toast fx-toast-${toast.type}`}>
                {toast.message}
              </div>
            ))}
          </div>
        )}
      </div>
      </div>

      {blockingOverlay && (
        <div className="fx-blocking-overlay" role="alertdialog" aria-modal="true" aria-busy="true">
          <div className="fx-blocking-card">
            <div className="fx-blocking-spinner" aria-hidden="true" />
            <p className="fx-blocking-title">{blockingOverlay.message}</p>
            <p className="fx-blocking-detail">{t('subtitle.burning_wait', 'Please wait until the file is saved.')}</p>
            {blockingOverlay.detail ? (
              <code className="fx-blocking-path">{blockingOverlay.detail}</code>
            ) : null}
          </div>
        </div>
      )}

      <ProjectNotesPanel
        collapsed={notesCollapsed}
        onToggleCollapse={() => {
          setNotesCollapsed((c) => {
            const next = !c;
            localStorage.setItem('chakshu.notesCollapsed', next ? '1' : '0');
            return next;
          });
        }}
        projectName={projectMeta.name || forensicCase?.title}
        projectId={projectMeta.project_id}
        notes={notes}
        author={forensicCase?.examiner}
        evidenceId={evidenceId}
        frameIndex={frameIndex}
        timeSec={seekTime}
        t={t}
        onRefresh={refreshProjectNotes}
        onAdd={async (payload) => {
          await api.projectNoteAdd({
            ...payload,
            case_id: forensicCase?.case_id,
          });
          await refreshProjectNotes();
          setStatus(t('notes.saved', 'Note saved to project'));
        }}
        onDelete={async (noteId) => {
          await api.projectNoteDelete(noteId);
          await refreshProjectNotes();
          setStatus(t('notes.deleted', 'Note deleted'));
        }}
      />
      </div>

      <input ref={fileRef} type="file" accept="image/*,video/*" style={{ display: 'none' }} onChange={onUpload} />
      <input
        ref={aiModelFileRef}
        type="file"
        accept=".onnx"
        style={{ display: 'none' }}
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          try {
            await api.aiImportModel(file, { name: file.name.replace(/\.onnx$/i, '') });
            const models = await api.aiModels();
            setAiModels(models.models || []);
            setAiModelId(models.models?.[models.models.length - 1]?.id || '');
            setAiTool('custom_onnx');
            setStatus(`Imported ${file.name}`);
          } catch (err) { setError(err.message); }
          e.target.value = '';
        }}
      />
    </div>
  );
}
