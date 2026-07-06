import { useCallback, useEffect, useRef, useState } from 'react';
import { api, previewDataUrl } from '../api/client';
import {
  COMPARE_MODES,
  DEFAULT_COMPARE,
  DEFAULT_PIP,
  OVERLAY_TUTORIAL_STEPS,
  PIP_POSITIONS,
  compareRenderBody,
  overlayStepStatus,
  overlayTutorialProgress,
  pipOverlayPayload,
} from '../lib/videoOverlayCompare';

function PathBrowseField({
  label,
  value,
  onChange,
  onBrowseFile,
  browsing = false,
  browseLabel = 'Browse…',
  placeholder = '',
  accept = 'image/*,video/*',
  fileRef,
}) {
  return (
    <label className="fx-voc-field">
      <span>{label}</span>
      <div className="fx-voc-path-row">
        <input
          className="fx-input fx-voc-path-input"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <button
          type="button"
          className="fx-btn fx-voc-browse-btn"
          disabled={browsing}
          onClick={() => fileRef.current?.click()}
        >
          {browsing ? '…' : browseLabel}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept={accept}
          style={{ display: 'none' }}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onBrowseFile(file);
            e.target.value = '';
          }}
        />
      </div>
    </label>
  );
}

export default function VideoOverlayComparePanel({
  leftPath,
  sessionId,
  seekTime = 0,
  duration = 0,
  gridOverlay,
  timestampSettings,
  timestampContext,
  disabled = false,
  onPreviewUpdate,
  onApplied,
  setStatus,
  setError,
  notify,
  reportSuccess,
  reportError,
  t = (k, d) => d,
}) {
  const [active, setActive] = useState(false);
  const [compare, setCompare] = useState(DEFAULT_COMPARE);
  const [pip, setPip] = useState(DEFAULT_PIP);
  const [compareSessionId, setCompareSessionId] = useState(null);
  const [rendering, setRendering] = useState(false);
  const [applyingPip, setApplyingPip] = useState(false);
  const [lastPreview, setLastPreview] = useState(null);
  const [stagingRight, setStagingRight] = useState(false);
  const [stagingInset, setStagingInset] = useState(false);
  const [pipApplied, setPipApplied] = useState(false);
  const [showTutorial, setShowTutorial] = useState(() => {
    try {
      return localStorage.getItem('chakshu.overlayTutorial') !== 'hidden';
    } catch {
      return true;
    }
  });
  const rightFileRef = useRef(null);
  const insetFileRef = useRef(null);

  const patchCompare = useCallback((next) => {
    setCompare((prev) => ({ ...prev, ...next }));
  }, []);

  const patchPip = useCallback((next) => {
    setPip((prev) => ({ ...prev, ...next }));
  }, []);

  const stageAuxiliaryFile = useCallback(async (file, onStaged, { clearCompareSession = false } = {}) => {
    if (!file) return;
    try {
      const r = await api.stageMedia(file, sessionId || '');
      onStaged(r.storage_path);
      if (clearCompareSession) setCompareSessionId(null);
      reportSuccess?.(
        t('voc.staged', `Staged: ${r.filename}`),
      );
    } catch (e) {
      reportError?.(e, t('voc.browse_failed', 'File browse'));
    }
  }, [sessionId, reportSuccess, reportError, t]);

  const browseRightFile = useCallback(async (file) => {
    setStagingRight(true);
    try {
      await stageAuxiliaryFile(file, (path) => patchCompare({ rightPath: path }), { clearCompareSession: true });
    } finally {
      setStagingRight(false);
    }
  }, [stageAuxiliaryFile, patchCompare]);

  const browseInsetFile = useCallback(async (file) => {
    setStagingInset(true);
    setPipApplied(false);
    try {
      await stageAuxiliaryFile(file, (path) => patchPip({ insetPath: path }));
    } finally {
      setStagingInset(false);
    }
  }, [stageAuxiliaryFile, patchPip]);

  const tutorialCtx = {
    leftPath,
    rightPath: compare.rightPath,
    lastPreview,
    insetPath: pip.insetPath,
    pipApplied,
    rendering,
    applyingPip,
    seekTime,
  };
  const tutorial = overlayTutorialProgress(tutorialCtx);

  const toggleTutorial = useCallback(() => {
    setShowTutorial((open) => {
      const next = !open;
      try {
        localStorage.setItem('chakshu.overlayTutorial', next ? 'shown' : 'hidden');
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (compare.syncTimes) {
      setCompare((c) => ({ ...c, rightTime: seekTime }));
    }
  }, [seekTime, compare.syncTimes]);

  const ensureCompareSession = useCallback(async () => {
    if (compareSessionId) return compareSessionId;
    if (!leftPath || !compare.rightPath) {
      throw new Error(t('voc.need_paths', 'Set left (primary) and right file paths'));
    }
    const r = await api.capCompareCreate(leftPath, compare.rightPath);
    setCompareSessionId(r.session_id);
    return r.session_id;
  }, [compareSessionId, leftPath, compare.rightPath, t]);

  const renderCompare = useCallback(async () => {
    setRendering(true);
    setError?.('');
    try {
      const sid = await ensureCompareSession();
      const r = await api.capCompareRender(
        compareRenderBody(sid, seekTime, compare.rightTime, compare),
      );
      const url = previewDataUrl(r.preview);
      setLastPreview(url);
      onPreviewUpdate?.(url);
      setStatus?.(
        t('voc.rendered', `Compare rendered (${r.width}×${r.height}) · ${compare.mode}`),
      );
    } catch (e) {
      reportError?.(e, 'Compare render');
    } finally {
      setRendering(false);
    }
  }, [
    ensureCompareSession, seekTime, compare, onPreviewUpdate, setStatus, reportError, t,
  ]);

  const applyCompareToSession = useCallback(async () => {
    if (!sessionId) return;
    setRendering(true);
    try {
      const sid = await ensureCompareSession();
      const r = await api.capCompareRender(
        compareRenderBody(sid, seekTime, compare.rightTime, compare),
      );
      onApplied?.({ preview: r.preview, preview_original: r.preview });
      reportSuccess?.(t('voc.applied_compare', 'Comparison applied to examination frame'));
    } catch (e) {
      reportError?.(e, 'Apply compare');
    } finally {
      setRendering(false);
    }
  }, [
    sessionId, ensureCompareSession, seekTime, compare, onApplied, reportSuccess, reportError, t,
  ]);

  const applyPipOverlay = useCallback(async () => {
    if (!sessionId || !pip.insetPath) {
      reportError?.(t('voc.need_inset', 'Enter an inset file path for PiP'), 'PiP overlay');
      return;
    }
    setApplyingPip(true);
    setError?.('');
    try {
      const payload = pipOverlayPayload(sessionId, pip);
      const r = await api.capOverlay(sessionId, payload);
      onApplied?.(r);
      setPipApplied(true);
      reportSuccess?.(t('voc.applied_pip', 'Picture-in-picture overlay applied'));
    } catch (e) {
      reportError?.(e, 'PiP overlay');
    } finally {
      setApplyingPip(false);
    }
  }, [sessionId, pip, onApplied, reportSuccess, reportError, setError, t]);

  const applyFullOverlay = useCallback(async () => {
    if (!sessionId) return;
    setApplyingPip(true);
    try {
      const { resolveTimestampText } = await import('../lib/timestampEdit');
      const { overlayBurnPayload } = await import('../lib/gridOverlay');
      const timestampText = resolveTimestampText(
        { ...timestampSettings, enabled: true },
        timestampContext,
      );
      const base = overlayBurnPayload(
        gridOverlay?.preset,
        timestampText,
        timestampSettings?.position,
      );
      const payload = {
        ...base,
        ...(pip.insetPath ? pipOverlayPayload(sessionId, pip) : {}),
      };
      const r = await api.capOverlay(sessionId, payload);
      onApplied?.(r);
      notify?.(t('voc.applied_full', 'Overlays applied to frame'), 'success');
    } catch (e) {
      reportError?.(e, 'Overlay apply');
    } finally {
      setApplyingPip(false);
    }
  }, [
    sessionId, pip, gridOverlay, timestampSettings, timestampContext,
    onApplied, notify, reportError, t,
  ]);

  return (
    <div className={`fx-voc-panel${active ? ' fx-voc-panel-active' : ''}`}>
      <div className="fx-voc-head">
        <label className="fx-grid-toggle">
          <input
            type="checkbox"
            checked={active}
            disabled={disabled || !leftPath}
            onChange={(e) => setActive(e.target.checked)}
          />
          <span>{t('voc.title', 'Video overlays & side-by-side compare')}</span>
        </label>
        {active && (
          <button
            type="button"
            className="fx-voc-tutorial-toggle"
            onClick={toggleTutorial}
            aria-expanded={showTutorial}
          >
            {showTutorial
              ? t('voc.hide_tutorial', 'Hide tour')
              : t('voc.show_tutorial', 'Show tour')}
          </button>
        )}
      </div>
      {active && (
        <div className="fx-voc-body">
          {showTutorial && (
            <div className="fx-voc-tutorial" role="region" aria-label={t('voc.tutorial_title', 'Overlay test tour')}>
              <div className="fx-voc-tutorial-next">
                <span className="fx-voc-tutorial-next-label">
                  {t('voc.next_label', 'What to do next')}
                </span>
                <strong>{t(`voc.next.${tutorial.currentId}.title`, tutorial.nextTitle)}</strong>
                <p>{t(`voc.next.${tutorial.currentId}.detail`, tutorial.nextDetail)}</p>
              </div>
              <ol className="fx-voc-tutorial-steps">
                {OVERLAY_TUTORIAL_STEPS.map((step, index) => {
                  const status = overlayStepStatus(step.id, tutorialCtx);
                  return (
                    <li
                      key={step.id}
                      className={`fx-voc-tutorial-step fx-voc-tutorial-step--${status}`}
                    >
                      <span className="fx-voc-tutorial-step-num" aria-hidden="true">
                        {status === 'done' ? '✓' : index + 1}
                      </span>
                      <div>
                        <strong>{t(`voc.step.${step.id}.title`, step.title)}</strong>
                        <p>{t(`voc.step.${step.id}.detail`, step.detail)}</p>
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}
          <section className="fx-voc-section">
            <h4>{t('voc.compare_title', 'Side-by-side comparison')}</h4>
            <p className="fx-grid-hint">
              {t(
                'voc.compare_hint',
                'Compare two videos or images. Left uses primary evidence; scrub the timeline for left time. Browse or paste the right file path, then set time independently or sync.',
              )}
            </p>
            <label className="fx-voc-field">
              <span>{t('voc.left_path', 'Left (primary)')}</span>
              <input className="fx-input" readOnly value={leftPath || ''} />
            </label>
            <PathBrowseField
              label={t('voc.right_path', 'Right file path')}
              value={compare.rightPath}
              placeholder="/path/to/compare.mp4"
              browseLabel={t('voc.browse', 'Browse…')}
              browsing={stagingRight}
              fileRef={rightFileRef}
              onChange={(path) => {
                patchCompare({ rightPath: path });
                setCompareSessionId(null);
              }}
              onBrowseFile={browseRightFile}
            />
            <div className="fx-voc-fields-row">
              <label>
                <span>{t('voc.left_time', `Left time ${seekTime.toFixed(2)}s`)}</span>
                <input className="fx-input" readOnly value={seekTime.toFixed(2)} />
              </label>
              <label>
                <span>{t('voc.right_time', 'Right time (sec)')}</span>
                <input
                  type="number"
                  className="fx-input"
                  step="0.05"
                  min={0}
                  max={duration || 99999}
                  disabled={compare.syncTimes}
                  value={compare.syncTimes ? seekTime.toFixed(2) : compare.rightTime}
                  onChange={(e) => patchCompare({ rightTime: Number(e.target.value), syncTimes: false })}
                />
              </label>
            </div>
            <label className="fx-grid-toggle fx-voc-sync">
              <input
                type="checkbox"
                checked={compare.syncTimes}
                onChange={(e) => patchCompare({ syncTimes: e.target.checked, rightTime: seekTime })}
              />
              {t('voc.sync', 'Sync right time to playhead')}
            </label>
            <div className="fx-voc-fields-row">
              <label>
                <span>{t('voc.mode', 'Layout')}</span>
                <select className="fx-input" value={compare.mode} onChange={(e) => patchCompare({ mode: e.target.value })}>
                  {COMPARE_MODES.map((m) => (
                    <option key={m.id} value={m.id}>{m.label}</option>
                  ))}
                </select>
              </label>
              {compare.mode === 'pip' && (
                <>
                  <label>
                    <span>{t('voc.pip_scale', `Inset scale ${compare.pipScale}`)}</span>
                    <input
                      type="range"
                      min={0.12}
                      max={0.5}
                      step={0.02}
                      value={compare.pipScale}
                      onChange={(e) => patchCompare({ pipScale: Number(e.target.value) })}
                    />
                  </label>
                  <label>
                    <span>{t('voc.pip_pos', 'Inset position')}</span>
                    <select className="fx-input" value={compare.pipPosition} onChange={(e) => patchCompare({ pipPosition: e.target.value })}>
                      {PIP_POSITIONS.map((p) => (
                        <option key={p.id} value={p.id}>{p.label}</option>
                      ))}
                    </select>
                  </label>
                </>
              )}
            </div>
            <div className="fx-export-actions-row">
              <button type="button" className="fx-btn" disabled={disabled || rendering || !compare.rightPath} onClick={renderCompare}>
                {rendering ? t('voc.rendering', 'Rendering…') : t('voc.preview', 'Preview compare')}
              </button>
              <button type="button" className="fx-btn fx-btn-primary" disabled={disabled || rendering || !sessionId || !compare.rightPath} onClick={applyCompareToSession}>
                {t('voc.apply_compare', 'Apply to examination frame')}
              </button>
            </div>
          </section>

          <section className="fx-voc-section">
            <h4>{t('voc.pip_title', 'Picture-in-picture on current frame')}</h4>
            <p className="fx-grid-hint">
              {t('voc.pip_hint', 'Overlay a second video or image inset on the current examination frame. Browse or paste the inset file path.')}
            </p>
            <PathBrowseField
              label={t('voc.inset_path', 'Inset file path')}
              value={pip.insetPath}
              placeholder="/path/to/inset.mp4"
              browseLabel={t('voc.browse', 'Browse…')}
              browsing={stagingInset}
              fileRef={insetFileRef}
              onChange={(path) => patchPip({ insetPath: path })}
              onBrowseFile={browseInsetFile}
            />
            <div className="fx-voc-fields-row">
              <label>
                <span>{t('voc.inset_time', 'Inset time (sec)')}</span>
                <input
                  type="number"
                  className="fx-input"
                  step="0.05"
                  min={0}
                  value={pip.insetTime}
                  onChange={(e) => patchPip({ insetTime: Number(e.target.value) })}
                />
              </label>
              <label>
                <span>{t('voc.inset_scale', `Scale ${pip.pipScale}`)}</span>
                <input
                  type="range"
                  min={0.12}
                  max={0.5}
                  step={0.02}
                  value={pip.pipScale}
                  onChange={(e) => patchPip({ pipScale: Number(e.target.value) })}
                />
              </label>
              <label>
                <span>{t('voc.inset_pos', 'Position')}</span>
                <select className="fx-input" value={pip.pipPosition} onChange={(e) => patchPip({ pipPosition: e.target.value })}>
                  {PIP_POSITIONS.map((p) => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="fx-export-actions-row">
              <button type="button" className="fx-btn" disabled={disabled || applyingPip || !sessionId || !pip.insetPath} onClick={applyPipOverlay}>
                {applyingPip ? t('voc.applying', 'Applying…') : t('voc.apply_pip', 'Apply PiP overlay')}
              </button>
              <button type="button" className="fx-btn" disabled={disabled || applyingPip || !sessionId} onClick={applyFullOverlay}>
                {t('voc.apply_all', 'PiP + grid + timestamp')}
              </button>
            </div>
          </section>

          {lastPreview && (
            <p className="fx-voc-preview-hint">{t('voc.preview_active', 'Compare preview shown above — use Apply to commit to the session.')}</p>
          )}
        </div>
      )}
    </div>
  );
}
