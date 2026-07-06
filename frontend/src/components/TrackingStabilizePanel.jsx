import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import { formatApiError } from '../lib/notify';
import {
  STABILIZE_MODES,
  STABILIZE_TUTORIAL_STEPS,
  TRACKER_TYPES,
  bboxFromRect,
  buildTrackingExportPath,
  defaultCenterBBox,
  stabilizeTutorialProgress,
  stepStatus,
} from '../lib/trackingStabilize';

function stampLog(type, message, detail = '') {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    type,
    message,
    detail,
    at: new Date().toLocaleTimeString(),
  };
}

export default function TrackingStabilizePanel({
  imageSrc,
  videoPath,
  outputDir,
  sessionId,
  onSeekFrame,
  seekTime = 0,
  duration = 0,
  disabled = false,
  setStatus,
  setError,
  notify,
  reportSuccess,
  reportError,
  t = (k, d) => d,
  compactRail = false,
}) {
  const imgRef = useRef(null);
  const dragRef = useRef(null);
  const [active, setActive] = useState(false);
  const [bbox, setBbox] = useState(null);
  const [draft, setDraft] = useState(null);
  const [trackerType, setTrackerType] = useState('KCF');
  const [smoothing, setSmoothing] = useState(15);
  const [mode, setMode] = useState('full');
  const [endSec, setEndSec] = useState(null);
  const [trackDurationSec, setTrackDurationSec] = useState(30);
  const [tracking, setTracking] = useState(false);
  const [stabilizing, setStabilizing] = useState(false);
  const [trackResult, setTrackResult] = useState(null);
  const [trackingSessionId, setTrackingSessionId] = useState(null);
  const [userDrewBox, setUserDrewBox] = useState(false);
  const [panelError, setPanelError] = useState('');
  const [logs, setLogs] = useState([]);
  const [lastExportPath, setLastExportPath] = useState('');
  const [showTutorial, setShowTutorial] = useState(() => {
    if (compactRail) return false;
    try {
      return localStorage.getItem('chakshu.trackTutorial') !== 'hidden';
    } catch {
      return true;
    }
  });

  const pushLog = useCallback((type, message, detail = '') => {
    const entry = stampLog(type, message, detail);
    setLogs((prev) => [entry, ...prev].slice(0, 8));
    if (type === 'error') {
      setPanelError(message);
      setError?.(message);
    }
    return entry;
  }, [setError]);

  const clearTrack = useCallback(() => {
    setTrackResult(null);
    setTrackingSessionId(null);
  }, []);

  const syncDefaultBbox = useCallback(() => {
    const img = imgRef.current;
    if (!img?.naturalWidth) return;
    setBbox(defaultCenterBBox(img.naturalWidth, img.naturalHeight));
    setUserDrewBox(false);
    clearTrack();
    setPanelError('');
  }, [clearTrack]);

  useEffect(() => {
    if (active) syncDefaultBbox();
  }, [imageSrc, active, syncDefaultBbox]);

  useEffect(() => {
    clearTrack();
    setPanelError('');
  }, [seekTime, clearTrack]);

  const canExport = Boolean(trackResult && trackingSessionId && bbox && !tracking);

  const getScale = useCallback(() => {
    const img = imgRef.current;
    if (!img?.clientWidth) return { x: 1, y: 1 };
    return {
      x: img.clientWidth / (img.naturalWidth || img.clientWidth),
      y: img.clientHeight / (img.naturalHeight || img.clientHeight),
    };
  }, []);

  const toImageCoords = useCallback((clientX, clientY) => {
    const img = imgRef.current;
    if (!img) return { x: 0, y: 0 };
    const rect = img.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(img.naturalWidth, ((clientX - rect.left) / rect.width) * img.naturalWidth)),
      y: Math.max(0, Math.min(img.naturalHeight, ((clientY - rect.top) / rect.height) * img.naturalHeight)),
    };
  }, []);

  const onPointerDown = useCallback((e) => {
    if (disabled) return;
    e.preventDefault();
    const pt = toImageCoords(e.clientX, e.clientY);
    dragRef.current = { start: pt };
    setDraft({ start: pt, end: pt });
    e.currentTarget.setPointerCapture(e.pointerId);
  }, [disabled, toImageCoords]);

  const onPointerMove = useCallback((e) => {
    if (!dragRef.current) return;
    const end = toImageCoords(e.clientX, e.clientY);
    setDraft({ start: dragRef.current.start, end });
  }, [toImageCoords]);

  const onPointerUp = useCallback(() => {
    if (!dragRef.current || !draft) {
      dragRef.current = null;
      return;
    }
    const next = bboxFromRect(draft.start, draft.end);
    setBbox(next);
    setDraft(null);
    clearTrack();
    setUserDrewBox(true);
    setPanelError('');
    dragRef.current = null;
  }, [draft, clearTrack]);

  const previewDims = useCallback(() => {
    const img = imgRef.current;
    return {
      preview_width: img?.naturalWidth || null,
      preview_height: img?.naturalHeight || null,
    };
  }, []);

  const syncFrame = useCallback(async () => {
    if (onSeekFrame) {
      return onSeekFrame(seekTime);
    }
    if (!sessionId) return null;
    try {
      return await api.seekVideo(sessionId, seekTime);
    } catch (err) {
      const msg = formatApiError(err, 'Could not sync frame');
      pushLog('error', msg, err?.message || String(err));
      return null;
    }
  }, [onSeekFrame, sessionId, seekTime, pushLog]);

  const frameDims = useCallback((seekMeta) => {
    if (seekMeta?.width && seekMeta?.height) {
      return { preview_width: seekMeta.width, preview_height: seekMeta.height };
    }
    return previewDims();
  }, [previewDims]);

  const resolvedEndSec = useCallback(() => {
    if (endSec != null && endSec > seekTime) return endSec;
    const span = Math.max(1, Number(trackDurationSec) || 30);
    if (duration > 0) return Math.min(duration, seekTime + span);
    return seekTime + span;
  }, [endSec, seekTime, trackDurationSec, duration]);

  const runTrack = useCallback(async () => {
    if (!videoPath || !bbox) {
      const msg = t('track.no_bbox', 'Draw a box around the object first');
      pushLog('warn', msg);
      reportError?.(msg, 'Tracking');
      return;
    }
    const end = resolvedEndSec();
    setTracking(true);
    setPanelError('');
    setError?.('');
    const statusMsg = t('track.running', `Tracking ~${(end - seekTime).toFixed(1)}s of video…`);
    setStatus?.(statusMsg);
    pushLog('info', statusMsg);
    try {
      const seekMeta = await syncFrame();
      const dims = frameDims(seekMeta);
      const r = await api.trackingRun({
        path: videoPath,
        bbox,
        time_sec: seekTime,
        end_sec: end,
        tracker_type: trackerType,
        tracking_session_id: trackingSessionId,
        ...dims,
      });
      setTrackResult(r);
      setTrackingSessionId(r.tracking_session_id);
      const doneMsg = `${t('track.done', 'Tracked')} ${r.frame_count} ${t('track.frames', 'frames')} · ${r.tracker_type}`;
      setStatus?.(doneMsg);
      pushLog('success', doneMsg, `session ${r.tracking_session_id}`);
      notify?.(t('track.ready_export', 'Tracking complete — you can now export'), 'success');
    } catch (e) {
      const msg = formatApiError(e, 'Tracking failed');
      pushLog('error', msg, e?.message || String(e));
      reportError?.(e, 'Tracking failed');
    } finally {
      setTracking(false);
    }
  }, [
    videoPath, bbox, seekTime, resolvedEndSec, trackerType, trackingSessionId,
    syncFrame, frameDims, setStatus, setError, pushLog, reportError, notify, t,
  ]);

  const exportStabilized = useCallback(async () => {
    if (!videoPath || !bbox) return;
    if (!canExport) {
      const msg = t('track.need_track', 'Track the object first — export unlocks after tracking succeeds');
      pushLog('warn', msg);
      reportError?.(msg, 'Stabilization');
      return;
    }
    const out = buildTrackingExportPath(outputDir, { seekTime, mode });
    setStabilizing(true);
    setPanelError('');
    setError?.('');
    const statusMsg = t('track.exporting_cached', 'Exporting stabilized video…');
    setStatus?.(statusMsg);
    pushLog('info', statusMsg, out);
    try {
      const seekMeta = await syncFrame();
      const dims = frameDims(seekMeta);
      const r = await api.trackingStabilize({
        input_path: videoPath,
        output_path: out,
        bbox,
        time_sec: seekTime,
        tracker_type: trackerType,
        smoothing,
        mode,
        tracking_session_id: trackingSessionId,
        ...dims,
      });
      if (r.success === false) {
        const failMsg = r.error || r.stderr || t('track.export_fail', 'Export failed');
        pushLog('error', failMsg, r.stderr || r.error || '');
        reportError?.(failMsg, 'Stabilization export');
        return;
      }
      const successMsg = t('track.saved', `Stabilized video saved: ${r.output_path}`);
      setStatus?.(successMsg);
      setLastExportPath(r.output_path || out);
      pushLog('success', successMsg, r.warning || `${r.frames_written} frames written`);
      reportSuccess?.(successMsg);
      if (r.warning) {
        notify?.(r.warning, 'warn');
        pushLog('warn', r.warning);
      }
    } catch (e) {
      const msg = formatApiError(e, 'Export failed');
      pushLog('error', msg, e?.message || String(e));
      reportError?.(e, 'Stabilization export');
    } finally {
      setStabilizing(false);
    }
  }, [
    videoPath, bbox, outputDir, seekTime, trackerType, smoothing, mode,
    trackingSessionId, canExport, syncFrame, frameDims, setStatus, setError,
    pushLog, reportSuccess, reportError, notify, t,
  ]);

  const scale = getScale();
  const rect = draft ? bboxFromRect(draft.start, draft.end) : bbox;
  const tutorial = stabilizeTutorialProgress({
    userDrewBox,
    trackResult,
    tracking,
    stabilizing,
  });
  const tutorialCtx = { userDrewBox, trackResult, tracking, stabilizing };

  const toggleTutorial = useCallback(() => {
    setShowTutorial((open) => {
      const next = !open;
      try {
        localStorage.setItem('chakshu.trackTutorial', next ? 'shown' : 'hidden');
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const exportHint = !trackResult
    ? t('track.export_locked', 'Run Track object first to unlock export')
    : t('track.export_ready', 'Tracking complete — export is ready');
  const nextExportPath = canExport
    ? buildTrackingExportPath(outputDir, { seekTime, mode })
    : '';

  return (
    <div className={`fx-track-panel${active ? ' fx-track-panel-active' : ''}${compactRail ? ' fx-track-panel-compact' : ''}`}>
      <div className="fx-track-head">
        <label className="fx-grid-toggle">
          <input
            type="checkbox"
            checked={active}
            disabled={disabled || !videoPath}
            onChange={(e) => setActive(e.target.checked)}
          />
          <span>{t('track.title', 'Object-tracking stabilization')}</span>
        </label>
        {active && (
          <button
            type="button"
            className="fx-track-tutorial-toggle"
            onClick={toggleTutorial}
            aria-expanded={showTutorial}
          >
            {showTutorial
              ? t('track.hide_tutorial', 'Hide guide')
              : t('track.show_tutorial', 'Show guide')}
          </button>
        )}
      </div>
      {active && imageSrc && (
        <div className="fx-track-body">
          <div className="fx-track-workspace-main">
            <p className="fx-grid-hint">
              {t('track.hint', 'Track first, then export. Object stays fixed on screen while the scene moves.')}
            </p>
            <div
              className="fx-track-stage"
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerUp}
            >
              <img ref={imgRef} src={imageSrc} alt="" onLoad={syncDefaultBbox} draggable={false} />
              {rect && (
                <div
                  className="fx-track-bbox"
                  style={{
                    left: rect[0] * scale.x,
                    top: rect[1] * scale.y,
                    width: rect[2] * scale.x,
                    height: rect[3] * scale.y,
                  }}
                />
              )}
            </div>
            {trackResult && (
              <div className="fx-track-stats">
                <span>{trackResult.frame_count} frames</span>
                <span>{trackResult.start_frame} → {trackResult.end_frame}</span>
                <span>{trackResult.tracker_type}</span>
              </div>
            )}
          </div>

          <aside className="fx-track-workspace-side">
            {showTutorial && (
              <div className="fx-track-tutorial" role="region" aria-label={t('track.tutorial_title', 'Stabilization guide')}>
                <div className="fx-track-tutorial-next">
                  <span className="fx-track-tutorial-next-label">
                    {t('track.next_label', 'What to do next')}
                  </span>
                  <strong>{t(`track.next.${tutorial.currentId}.title`, tutorial.nextTitle)}</strong>
                  <p>{t(`track.next.${tutorial.currentId}.detail`, tutorial.nextDetail)}</p>
                </div>
                <ol className="fx-track-tutorial-steps">
                  {STABILIZE_TUTORIAL_STEPS.map((step, index) => {
                    const status = stepStatus(step.id, tutorialCtx);
                    return (
                      <li
                        key={step.id}
                        className={`fx-track-tutorial-step fx-track-tutorial-step--${status}`}
                      >
                        <span className="fx-track-tutorial-step-num" aria-hidden="true">
                          {status === 'done' ? '✓' : index + 1}
                        </span>
                        <div>
                          <strong>{t(`track.step.${step.id}.title`, step.title)}</strong>
                          <p>{t(`track.step.${step.id}.detail`, step.detail)}</p>
                        </div>
                      </li>
                    );
                  })}
                </ol>
              </div>
            )}

            <div className="fx-track-controls-card">
              <div className="fx-track-fields">
                <label>
                  <span>{t('track.tracker', 'Tracker')}</span>
                  <select
                    className="fx-input"
                    value={trackerType}
                    onChange={(e) => {
                      setTrackerType(e.target.value);
                      clearTrack();
                    }}
                  >
                    {TRACKER_TYPES.map((tr) => (
                      <option key={tr.id} value={tr.id}>{tr.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>{t('track.mode', 'Export mode')}</span>
                  <select className="fx-input" value={mode} onChange={(e) => setMode(e.target.value)}>
                    {STABILIZE_MODES.map((m) => (
                      <option key={m.id} value={m.id}>{m.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>{t('track.smoothing', `Smoothing ${smoothing}`)}</span>
                  <input
                    type="range"
                    min={1}
                    max={60}
                    value={smoothing}
                    onChange={(e) => setSmoothing(Number(e.target.value))}
                  />
                </label>
                {duration > 0 && (
                  <label>
                    <span>{t('track.duration', `Track span (sec) — ends at ${resolvedEndSec().toFixed(1)}s`)}</span>
                    <input
                      type="number"
                      className="fx-input"
                      step="1"
                      min={1}
                      max={Math.max(1, Math.ceil(duration - seekTime))}
                      value={trackDurationSec}
                      onChange={(e) => {
                        setTrackDurationSec(Number(e.target.value) || 30);
                        setEndSec(null);
                        clearTrack();
                      }}
                    />
                  </label>
                )}
                {duration > 0 && (
                  <label>
                    <span>{t('track.end_sec', 'Exact end time (sec, optional)')}</span>
                    <input
                      type="number"
                      className="fx-input"
                      step="0.1"
                      min={seekTime}
                      max={duration}
                      placeholder={resolvedEndSec().toFixed(1)}
                      value={endSec ?? ''}
                      onChange={(e) => {
                        setEndSec(e.target.value ? Number(e.target.value) : null);
                        clearTrack();
                      }}
                    />
                  </label>
                )}
              </div>
              <div className="fx-export-actions-row">
                <button type="button" className="fx-btn" disabled={disabled || tracking || !bbox} onClick={syncDefaultBbox}>
                  {t('track.reset_box', 'Reset box')}
                </button>
                <button type="button" className="fx-btn" disabled={disabled || tracking || !bbox} onClick={runTrack}>
                  {tracking ? t('track.tracking', 'Tracking…') : t('track.run', 'Track object')}
                </button>
                <button
                  type="button"
                  className="fx-btn fx-btn-primary"
                  disabled={disabled || stabilizing || !canExport}
                  title={exportHint}
                  onClick={exportStabilized}
                >
                  {stabilizing ? t('track.exporting', 'Exporting…') : t('track.export', 'Export stabilized video')}
                </button>
              </div>
              <p className={`fx-track-export-hint${canExport ? ' fx-track-export-hint--ready' : ''}`}>
                {exportHint}
                {nextExportPath && (
                  <span className="fx-track-export-name">
                    {t('track.next_file', 'Next file')}: {nextExportPath.split('/').pop()}
                  </span>
                )}
              </p>
              {lastExportPath && (
                <p className="fx-track-output-hint">
                  {t('track.last_saved', 'Last saved')}: {lastExportPath}
                </p>
              )}
            </div>

            {(panelError || logs.length > 0) && (
              <div className="fx-track-log" role="log" aria-live="polite" aria-label={t('track.log_title', 'Stabilization log')}>
                <div className="fx-track-log-head">
                  <strong>{t('track.log_title', 'Stabilization log')}</strong>
                  {logs.length > 0 && (
                    <button
                      type="button"
                      className="fx-track-log-clear"
                      onClick={() => {
                        setLogs([]);
                        setPanelError('');
                        setError?.('');
                      }}
                    >
                      {t('track.log_clear', 'Clear')}
                    </button>
                  )}
                </div>
                {panelError && (
                  <div className="fx-track-log-error" role="alert">
                    {panelError}
                  </div>
                )}
                <ul className="fx-track-log-list">
                  {logs.map((entry) => (
                    <li key={entry.id} className={`fx-track-log-item fx-track-log-item--${entry.type}`}>
                      <span className="fx-track-log-time">{entry.at}</span>
                      <span className="fx-track-log-msg">{entry.message}</span>
                      {entry.detail && entry.detail !== entry.message && (
                        <code className="fx-track-log-detail">{entry.detail}</code>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
