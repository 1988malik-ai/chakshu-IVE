import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api/client';

export default function SubtitlePanel({
  t = (k, d) => d,
  videoPath,
  outputDir = '',
  sessionId,
  playheadSec = 0,
  fontSize = 22,
  marginV = 28,
  onFontSizeChange,
  onMarginVChange,
  outputPath: outputPathProp,
  onOutputPathChange,
  onApplyPreview,
  setStatus,
  setError,
  notify,
  onBlockingChange,
}) {
  const [subtitlePath, setSubtitlePath] = useState('');
  const [outputPathLocal, setOutputPathLocal] = useState('~/Desktop/chakshu-subtitled.mp4');
  const outputPath = outputPathProp ?? outputPathLocal;
  const setOutputPath = onOutputPathChange ?? setOutputPathLocal;

  useEffect(() => {
    if (subtitlePath) return;
    const stored = localStorage.getItem('chakshu.subtitlePath');
    if (stored) setSubtitlePath(stored);
  }, [subtitlePath]);

  useEffect(() => {
    if (subtitlePath) localStorage.setItem('chakshu.subtitlePath', subtitlePath);
  }, [subtitlePath]);
  const [parsed, setParsed] = useState(null);
  const [overlayOn, setOverlayOn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [burning, setBurning] = useState(false);
  const fileRef = useRef(null);
  const [customOutputDir, setCustomOutputDir] = useState(outputDir || '~/Desktop/chakshu-export');
  const [outputName, setOutputName] = useState('chakshu-subtitled.mp4');

  const splitOutputPath = useCallback((fullPath) => {
    const p = String(fullPath || '').trim();
    if (!p) return { dir: outputDir || '~/Desktop/chakshu-export', name: 'chakshu-subtitled.mp4' };
    const slash = p.lastIndexOf('/');
    if (slash < 0) return { dir: outputDir || '.', name: p };
    return { dir: p.slice(0, slash) || '.', name: p.slice(slash + 1) || 'chakshu-subtitled.mp4' };
  }, [outputDir]);

  const buildOutputPath = useCallback((dir, name) => {
    const d = String(dir || '').trim().replace(/\/+$/, '');
    const n = String(name || '').trim();
    if (!d) return n || 'chakshu-subtitled.mp4';
    return `${d}/${n || 'chakshu-subtitled.mp4'}`;
  }, []);

  const activeCue = parsed?.cues?.find(
    (c) => playheadSec >= c.start && playheadSec <= c.end,
  );

  const loadParse = useCallback(async () => {
    if (!subtitlePath.trim()) {
      setError(t('subtitle.no_path', 'Enter subtitle file path (.srt or .smi)'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const r = await api.subtitlesParse(subtitlePath.trim());
      setParsed(r);
      setStatus(
        `${t('subtitle.loaded', 'Loaded')} ${r.format?.toUpperCase() || 'SRT'} · ${r.count} ${t('subtitle.cues', 'cues')}`,
      );
      notify?.(t('subtitle.toast_loaded', 'Subtitles loaded successfully'), 'success');
    } catch (e) {
      setError(e.message);
      setParsed(null);
    } finally {
      setLoading(false);
    }
  }, [subtitlePath, setError, setStatus, t, notify]);

  const overlayFrame = useCallback(async () => {
    if (!sessionId) throw new Error(t('subtitle.need_session', 'Load video in Examination Lab first'));
    if (!subtitlePath.trim()) throw new Error(t('subtitle.no_path', 'Enter subtitle file path'));
    const r = await api.subtitlesOverlaySession({
      session_id: sessionId,
      subtitle_path: subtitlePath.trim(),
      time_sec: playheadSec,
      font_size: fontSize,
      margin_v: marginV,
    });
    onApplyPreview?.(r, r.subtitle_active
      ? `${t('subtitle.rendered', 'Subtitle rendered')}: ${r.subtitle_text?.slice(0, 60)}`
      : t('subtitle.no_cue', 'No cue at current time'));
    return r;
  }, [sessionId, subtitlePath, playheadSec, fontSize, marginV, onApplyPreview, t]);

  const burnIn = useCallback(async () => {
    if (!videoPath) throw new Error(t('subtitle.need_video', 'Set source video path'));
    if (!subtitlePath.trim()) throw new Error(t('subtitle.no_path', 'Enter subtitle file path'));
    const r = await api.capSubtitleBurn({
      video_path: videoPath,
      subtitle_path: subtitlePath.trim(),
      output_path: outputPath,
      font_size: fontSize,
      margin_v: marginV,
    });
    if (!r.success) throw new Error(r.stderr || r.error || t('subtitle.burn_failed', 'Burn-in failed'));
    setStatus(`${t('subtitle.burn_done', 'Burned subtitles')}: ${r.output || outputPath}`);
    notify?.(`${t('subtitle.toast_saved', 'Burned video saved')}: ${r.output || outputPath}`, 'success');
    return r;
  }, [videoPath, subtitlePath, outputPath, fontSize, marginV, setStatus, t, notify]);

  const handleBurn = useCallback(async () => {
    setBurning(true);
    onBlockingChange?.(true, {
      message: t('subtitle.burning', 'Burning subtitles into video…'),
      detail: outputPath,
    });
    setError('');
    try {
      await burnIn();
    } catch (e) {
      setError(e.message);
      notify?.(e.message, 'error');
    } finally {
      setBurning(false);
      onBlockingChange?.(false);
    }
  }, [burnIn, onBlockingChange, outputPath, setError, t, notify]);

  const toggleOverlay = async () => {
    const next = !overlayOn;
    setOverlayOn(next);
    if (next) {
      try {
        if (!parsed) await loadParse();
        await overlayFrame();
      } catch (e) {
        setOverlayOn(false);
        setError(e.message);
      }
    }
  };

  const importSubtitleFile = useCallback(async (file) => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const r = await api.uploadSubtitle(file, sessionId || '');
      setSubtitlePath(r.path);
      const parsedRes = await api.subtitlesParse(r.path);
      setParsed(parsedRes);
      setStatus(
        `${t('subtitle.imported', 'Subtitle imported')}: ${r.filename} (${parsedRes.count} ${t('subtitle.cues', 'cues')})`,
      );
      notify?.(t('subtitle.toast_imported', 'Subtitle file imported successfully'), 'success');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }, [sessionId, setError, setStatus, t, notify]);

  useEffect(() => {
    if (!overlayOn || !sessionId || !subtitlePath.trim()) return undefined;
    const timer = setTimeout(() => {
      overlayFrame().catch(() => {});
    }, 250);
    return () => clearTimeout(timer);
  }, [overlayOn, playheadSec, sessionId, subtitlePath, fontSize, marginV]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const parts = splitOutputPath(outputPath);
    setCustomOutputDir(parts.dir);
    setOutputName(parts.name);
  }, [outputPath, splitOutputPath]);

  return (
    <div className="fx-panel fx-subtitle-panel">
      <div className="fx-panel-head">{t('subtitle.title', 'Subtitles — SRT & SMI (R-120)')}</div>
      <div className="fx-panel-body fx-export-form">
        <p className="fx-export-hint">
          {t(
            'subtitle.hint',
            'Load SubRip (.srt) or SAMI (.smi) files. Preview cues on the examination frame or burn into a new video.',
          )}
        </p>

        <label className="fx-export-field">
          {t('subtitle.file', 'Subtitle file')}
          <input
            className="fx-input fx-input-mono"
            placeholder="/path/to/captions.srt or captions.smi"
            value={subtitlePath}
            onChange={(e) => setSubtitlePath(e.target.value)}
          />
        </label>
        <input
          ref={fileRef}
          type="file"
          accept=".srt,.smi"
          style={{ display: 'none' }}
          onChange={(e) => importSubtitleFile(e.target.files?.[0])}
        />

        <div className="fx-export-actions-row">
          <button
            type="button"
            className="fx-btn"
            disabled={loading}
            onClick={() => fileRef.current?.click()}
          >
            {t('subtitle.import_btn', 'Import subtitle file')}
          </button>
          <button type="button" className="fx-btn fx-btn-primary" disabled={loading} onClick={loadParse}>
            {loading ? t('subtitle.loading', 'Loading…') : t('subtitle.parse', 'Load & parse')}
          </button>
          <button
            type="button"
            className="fx-btn"
            disabled={!sessionId || !subtitlePath}
            onClick={() => overlayFrame().catch((e) => setError(e.message))}
          >
            {t('subtitle.render_once', 'Render at playhead')}
          </button>
        </div>

        <div className="fx-a11y-row" style={{ marginTop: 8 }}>
          <input
            id="fx-sub-overlay"
            type="checkbox"
            checked={overlayOn}
            onChange={toggleOverlay}
            disabled={!sessionId}
          />
          <label htmlFor="fx-sub-overlay">
            {t('subtitle.auto_overlay', 'Auto-render cue on examination frame when time changes')}
          </label>
        </div>

        {(activeCue || parsed) && (
          <div className="fx-subtitle-now">
            <strong>{t('subtitle.at_playhead', 'At playhead')}</strong>
            {activeCue ? (
              <p>
                <span className="fx-subtitle-time">
                  {activeCue.start.toFixed(2)}s – {activeCue.end.toFixed(2)}s
                </span>
                <br />
                {activeCue.text}
              </p>
            ) : (
              <p className="fx-export-hint">{t('subtitle.no_cue', 'No cue at current time')}</p>
            )}
          </div>
        )}

        {parsed?.cues?.length > 0 && (
          <div className="fx-subtitle-cue-list">
            <div className="fx-subtitle-cue-head">
              {parsed.format?.toUpperCase()} · {parsed.count} {t('subtitle.cues', 'cues')}
            </div>
            <ul>
              {parsed.cues.slice(0, 12).map((c) => (
                <li key={`${c.start}-${c.index}`} className={activeCue === c ? 'active' : ''}>
                  <span>{c.start.toFixed(1)}–{c.end.toFixed(1)}s</span>
                  <span>{c.text}</span>
                </li>
              ))}
            </ul>
            {parsed.count > 12 && (
              <p className="fx-export-hint">{t('subtitle.more_cues', '…and more cues in file')}</p>
            )}
          </div>
        )}

        <div className="fx-settings-section" style={{ marginTop: 14 }}>
          <h3 className="fx-settings-section-title">{t('subtitle.burn_title', 'Burn-in export (R-121)')}</h3>
          <div className="fx-export-grid-2">
            <label className="fx-export-field">
              {t('subtitle.output_dir', 'Output directory')}
              <input
                className="fx-input fx-input-mono"
                value={customOutputDir}
                onChange={(e) => setCustomOutputDir(e.target.value)}
              />
            </label>
            <label className="fx-export-field">
              {t('subtitle.output_name', 'Output filename')}
              <input
                className="fx-input fx-input-mono"
                value={outputName}
                onChange={(e) => setOutputName(e.target.value)}
              />
            </label>
          </div>
          <div className="fx-export-actions-row">
            <button
              type="button"
              className="fx-btn"
              onClick={() => {
                const p = buildOutputPath(customOutputDir, outputName);
                setOutputPath(p);
                setStatus(`${t('subtitle.output_applied', 'Output path set')}: ${p}`);
              }}
            >
              {t('subtitle.apply_output', 'Apply output path')}
            </button>
            <button
              type="button"
              className="fx-btn"
              onClick={() => {
                const p = buildOutputPath(outputDir || customOutputDir, outputName);
                setCustomOutputDir(outputDir || customOutputDir);
                setOutputPath(p);
                setStatus(`${t('subtitle.output_applied', 'Output path set')}: ${p}`);
              }}
            >
              {t('subtitle.use_export_dir', 'Use Export output directory')}
            </button>
          </div>
          <label className="fx-export-field">
            {t('subtitle.video_out', 'Output video')}
            <input className="fx-input fx-input-mono" value={outputPath} onChange={(e) => setOutputPath(e.target.value)} />
          </label>
          <div className="fx-export-grid-2">
            <label>
              {t('subtitle.font_size', 'Font size')}
              <input
                type="number"
                className="fx-input"
                min={10}
                max={72}
                value={fontSize}
                onChange={(e) => onFontSizeChange?.(Number(e.target.value) || 22)}
              />
            </label>
            <label>
              {t('subtitle.margin_v', 'Bottom margin')}
              <input
                type="number"
                className="fx-input"
                min={0}
                max={120}
                value={marginV}
                onChange={(e) => onMarginVChange?.(Number(e.target.value) || 28)}
              />
            </label>
          </div>
          <button
            type="button"
            className="fx-btn fx-btn-primary"
            style={{ marginTop: 8 }}
            disabled={!videoPath || burning || loading}
            onClick={handleBurn}
          >
            {burning ? t('subtitle.burning_btn', 'Burning…') : t('subtitle.burn_btn', 'Burn subtitles into video')}
          </button>
        </div>
      </div>
    </div>
  );
}
