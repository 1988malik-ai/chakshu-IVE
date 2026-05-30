import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, previewDataUrl } from './api/client';
import AudioPlayer from './components/AudioPlayer';
import ForensicTimeline, { formatTc } from './components/ForensicTimeline';
import ExamCanvas from './components/ExamCanvas';
import LiveCapture from './components/LiveCapture';
import { PRODUCT_FULL, PRODUCT_TAGLINE } from './brand';

const NAV = [
  { id: 'command', label: 'Command Center' },
  { id: 'examine', label: 'Examination Lab' },
  { id: 'capture', label: 'Live Capture' },
  { id: 'markup', label: 'Markup Studio' },
  { id: 'timeline', label: 'Timeline Pro' },
  { id: 'tools', label: 'Forensic Tools' },
  { id: 'custody', label: 'Chain of Custody' },
  { id: 'export', label: 'Legal Export' },
  { id: 'reports', label: 'Case Reports' },
];

export default function ForensicApp() {
  const [page, setPage] = useState('examine');
  const [sessionId, setSessionId] = useState(null);
  const [filters, setFilters] = useState([]);
  const [filterSearch, setFilterSearch] = useState('');
  const [selectedFilter, setSelectedFilter] = useState(null);
  const [preview, setPreview] = useState(null);
  const [filterChain, setFilterChain] = useState([]);
  const [forensicCase, setForensicCase] = useState(null);
  const [custody, setCustody] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [evidenceId, setEvidenceId] = useState(null);
  const [evidenceHash, setEvidenceHash] = useState('');
  const [allHashes, setAllHashes] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [notes, setNotes] = useState([]);
  const [noteText, setNoteText] = useState('');
  const [compareId, setCompareId] = useState(null);
  const [status, setStatus] = useState('Initializing forensic services…');
  const [error, setError] = useState('');
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
  const fileRef = useRef(null);
  const videoRef = useRef(null);

  const [exportForm, setExportForm] = useState({
    input_path: '',
    output_dir: '~/Desktop/chakshu-export',
    pdf_path: '~/Desktop/chakshu-frames.pdf',
    i_frames_dir: '~/Desktop/chakshu-i-frames',
    audio_out: '~/Desktop/audio.aac',
  });

  const init = useCallback(async () => {
    try {
      const { session_id } = await api.createSession();
      setSessionId(session_id);
      const [flt, fc] = await Promise.all([
        api.fetchFilters(),
        api.forensicsActiveCase(),
      ]);
      setFilters(flt.filters || []);
      setForensicCase(fc);
      setStatus(`Case ${fc.case_number} · ${flt.implemented_count || 0} forensic filters ready`);
    } catch (e) {
      setError(e.message);
      setStatus('API offline — start: python -m aive.api.server');
    }
  }, []);

  useEffect(() => { init(); }, [init]);

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
    if (data.filter_chain) setFilterChain(data.filter_chain);
  };

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
      handlePreview(data);
      setStatus(`Applied: ${selectedFilter.name}`);
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

  const seekToTime = async (t) => {
    setSeekTime(t);
    if (videoRef.current) videoRef.current.currentTime = t;
    const near = timeline?.frames?.reduce((best, f) => (
      !best || Math.abs(f.pts - t) < Math.abs(best.pts - t) ? f : best
    ), null);
    if (near) setCurrentFrameMeta(near);
    if (!sessionId) return;
    try {
      const r = await api.seekVideo(sessionId, t);
      handlePreview(r);
      setFrameIndex(r.frame_index ?? near?.index ?? 0);
    } catch { /* scrub only */ }
  };

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
  }, [page, forensicCase?.case_id]);

  const handleLiveIngest = (data) => {
    handlePreview(data);
    if (data.storage_path) setStoragePath(data.storage_path);
    setMediaType(data.media_type || 'image');
    setPage('examine');
  };

  const markupMediaId = useMemo(
    () => evidenceId || storagePath || sessionId || 'default',
    [evidenceId, storagePath, sessionId],
  );

  const mediaIdLabel = () => {
    const id = storagePath || mediaPath || '—';
    return id.length > 40 ? `…${id.slice(-36)}` : id;
  };

  return (
    <div className="fx-app">
      <aside className="fx-sidebar">
        <div className="fx-brand">
          <h1>{PRODUCT_FULL}</h1>
          <p>{PRODUCT_TAGLINE}</p>
        </div>
        <nav className="fx-nav">
          {NAV.map((n) => (
            <button
              key={n.id}
              type="button"
              className={`fx-nav-btn ${page === n.id ? 'active' : ''}`}
              onClick={() => setPage(n.id)}
            >
              {n.label}
            </button>
          ))}
        </nav>
        <div style={{ padding: 12, fontSize: '0.7rem', color: 'var(--fx-muted)' }}>
          <div className="case-id">{forensicCase?.case_number || '—'}</div>
          <div>{forensicCase?.examiner || 'Examiner'}</div>
        </div>
      </aside>

      <div className="fx-main">
        <header className="fx-topbar">
          <div>
            <strong>{forensicCase?.title || 'Examination'}</strong>
            <span className="case-id" style={{ marginLeft: 12 }}>{forensicCase?.case_id?.slice(0, 8)}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="fx-btn" onClick={() => fileRef.current?.click()}>Ingest Evidence</button>
            <button type="button" className="fx-btn fx-btn-primary" onClick={() => setPage('examine')}>Examination Lab</button>
          </div>
        </header>

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
          <div className="fx-content fx-grid-3">
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
              <div className="fx-preview">
                {preview ? <img src={preview} alt="Evidence frame" /> : <span style={{ color: '#555' }}>Ingest evidence to begin examination</span>}
              </div>
              {mediaType === 'video' && storagePath && (
                <div className="fx-panel-body" style={{ borderTop: '1px solid var(--fx-border)' }}>
                  <video
                    ref={videoRef}
                    src={api.mediaServeUrl(storagePath)}
                    controls
                    style={{ width: '100%', maxHeight: 180, background: '#000' }}
                    onTimeUpdate={(e) => setSeekTime(e.target.currentTime)}
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
                      onChange={(e) => setSeekTime(Number(e.target.value))}
                    />
                    <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                      <button
                        type="button"
                        className="fx-btn fx-btn-primary"
                        onClick={async () => {
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
                      onTimeUpdate={(e) => setSeekTime(e.target.currentTime)}
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
                  <button type="button" className="fx-btn" onClick={() => stepFrame(-1)} disabled={!sessionId}>◀</button>
                  <button type="button" className="fx-btn" onClick={() => stepFrame(1)} disabled={!sessionId}>▶</button>
                  <button type="button" className="fx-btn" onClick={() => stepFrame(1, true)} disabled={!sessionId}>I</button>
                </div>
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
              </div>
            </div>
          </div>
        )}

        {page === 'tools' && (
          <div className="fx-content" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
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
                      if (r.preview) setPreview(previewDataUrl(r.preview));
                      setStatus(`Frame at ${seekTime}s`);
                    } catch (e) { setError(e.message); }
                  }}>Seek Time</button>
                  <button type="button" className="fx-btn" onClick={async () => {
                    try {
                      const r = await api.capSeekIframe(exportForm.input_path, seekTime);
                      if (r.preview) setPreview(previewDataUrl(r.preview));
                      setStatus(`I-frame near ${seekTime}s (pts ${r.iframe_pts})`);
                    } catch (e) { setError(e.message); }
                  }}>Nearest I-Frame</button>
                </div>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={async () => {
                  try {
                    const r = await api.capMpegViz(exportForm.input_path, seekTime, 'macroblock');
                    if (r.preview) setPreview(previewDataUrl(r.preview));
                    setStatus('Macroblock overlay');
                  } catch (e) { setError(e.message); }
                }}>MPEG Macroblock Overlay</button>
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Examination Notes</div>
              <div className="fx-panel-body">
                <textarea className="fx-input" rows={3} value={noteText} onChange={(e) => setNoteText(e.target.value)} placeholder="Observation…" />
                <button type="button" className="fx-btn fx-btn-primary" style={{ marginTop: 6 }} onClick={async () => {
                  if (!forensicCase?.case_id || !noteText.trim()) return;
                  await api.capAddNote({ case_id: forensicCase.case_id, author: forensicCase.examiner, body: noteText });
                  const n = await api.capNotes(forensicCase.case_id);
                  setNotes(n.notes || []);
                  setNoteText('');
                  setStatus('Note saved');
                }}>Save Note</button>
                <ul style={{ marginTop: 10, fontSize: '0.75rem', color: 'var(--fx-muted)' }}>
                  {notes.map((n) => <li key={n.note_id}>{n.timestamp}: {n.body}</li>)}
                </ul>
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
                      if (r.preview) setPreview(previewDataUrl(r.preview));
                    } catch (e) { setError(e.message); }
                  }}>Render Compare</button>
                )}
                <button type="button" className="fx-btn" style={{ marginTop: 8, display: 'block' }} onClick={async () => {
                  if (!sessionId) return;
                  try {
                    const r = await api.capOverlay(sessionId, { timestamp_text: new Date().toISOString(), grid: true });
                    handlePreview(r);
                  } catch (e) { setError(e.message); }
                }}>Apply Timestamp + Grid</button>
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
          <div className="fx-content" style={{ gridTemplateColumns: '1fr 1fr', display: 'grid', gap: 16 }}>
            <div className="fx-panel">
              <div className="fx-panel-head">Legal Export — I-Frames & Audio</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn fx-btn-primary" style={{ marginBottom: 8 }} onClick={() => api.exportIFrames({ input_path: exportForm.input_path, output_dir: exportForm.i_frames_dir })}>Export I-Frames Only</button>
                <button type="button" className="fx-btn" onClick={() => api.extractAudio({ input_path: exportForm.input_path, output_path: exportForm.audio_out })}>Extract Audio Stream</button>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={() => api.capTrim({
                  input_path: exportForm.input_path,
                  output_path: `${exportForm.output_dir}/trim.mp4`,
                  start_sec: 0,
                  end_sec: 30,
                })}>Trim Segment (stream copy)</button>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={() => api.capAudioRedact({
                  input_path: exportForm.input_path,
                  output_path: `${exportForm.output_dir}/audio-redacted.aac`,
                  mute_regions: [[5, 10]],
                })}>Audio Redact (mute 5–10s)</button>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={() => api.capMetadataExport(exportForm.input_path, `${exportForm.output_dir}/metadata.json`)}>Export Metadata Bundle</button>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={() => api.exportPdfFrames({ session_id: sessionId, output_path: exportForm.pdf_path, columns: 2, rows: 2 })}>Export Frames to PDF</button>
              </div>
            </div>
            <div className="fx-panel">
              <div className="fx-panel-head">Original + Processed Bundle</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn" onClick={() => api.exportMediaBundle({
                  input_path: exportForm.input_path,
                  output_dir: exportForm.output_dir,
                  include_original: true,
                  include_processed: true,
                })}>Export Examination Bundle</button>
              </div>
            </div>
          </div>
        )}

        {page === 'reports' && (
          <div className="fx-content">
            <div className="fx-panel" style={{ maxWidth: 520 }}>
              <div className="fx-panel-head">Forensic Case Report</div>
              <div className="fx-panel-body">
                <button type="button" className="fx-btn fx-btn-primary" onClick={() => api.generateReport({
                  output_dir: '~/Desktop/AI-IVE-reports',
                  title: `Forensic Report — ${forensicCase?.case_number}`,
                  author: forensicCase?.examiner || '',
                  formats: ['html', 'pdf', 'docx'],
                  template: 'detailed',
                  paper_size: 'A4',
                })}>Generate HTML / PDF / DOCX</button>
                <p style={{ color: 'var(--fx-muted)', marginTop: 12, fontSize: '0.8rem' }}>
                  Includes workflow steps, filter settings, and references for court-ready documentation.
                </p>
              </div>
            </div>
          </div>
        )}

        <footer className="fx-statusbar">
          {status}
          {error && <span style={{ color: 'var(--fx-danger)' }}> | {error}</span>}
        </footer>
      </div>

      <input ref={fileRef} type="file" accept="image/*,video/*" style={{ display: 'none' }} onChange={onUpload} />
    </div>
  );
}
