import { useCallback, useState } from 'react';
import { api } from '../api/client';

function emptyRegion() {
  return { id: crypto.randomUUID(), start: 0, end: 5 };
}

export default function AudioRedactionPanel({
  t = (k, d) => d,
  inputPath,
  outputDir,
  playheadSec = 0,
  selectionStart,
  selectionEnd,
  setStatus,
  setError,
}) {
  const [regions, setRegions] = useState([emptyRegion()]);
  const [audioOut, setAudioOut] = useState(`${outputDir}/audio-redacted.aac`);
  const [videoOut, setVideoOut] = useState(`${outputDir}/video-audio-redacted.mp4`);
  const [exportVideo, setExportVideo] = useState(true);

  const mutePayload = useCallback(() => ({
    input_path: inputPath,
    mute_regions: regions.map((r) => [Number(r.start) || 0, Number(r.end) || 0]),
    mode: 'mute',
  }), [inputPath, regions]);

  const runRedact = async (output_path) => {
    if (!inputPath) throw new Error(t('audio_redact.no_input', 'Load or set source media path first'));
    setError('');
    const body = { ...mutePayload(), output_path };
    const r = await api.capAudioRedact(body);
    if (!r.success) throw new Error(r.error || r.stderr || t('audio_redact.failed', 'Audio redaction failed'));
    setStatus(
      `${t('audio_redact.done', 'Audio redacted')}: ${r.output || output_path} · ${r.region_count ?? regions.length} ${t('audio_redact.regions', 'region(s)')}`,
    );
    return r;
  };

  const addRegion = () => setRegions((list) => [...list, emptyRegion()]);

  const removeRegion = (id) => setRegions((list) => (list.length <= 1 ? list : list.filter((r) => r.id !== id)));

  const patchRegion = (id, key, value) => {
    setRegions((list) => list.map((r) => (r.id === id ? { ...r, [key]: value } : r)));
  };

  const useTimelineSelection = () => {
    const a = Math.min(selectionStart ?? 0, selectionEnd ?? 0);
    const b = Math.max(selectionStart ?? 0, selectionEnd ?? 0);
    if (b <= a) {
      setError(t('audio_redact.bad_selection', 'Set a valid timeline region (end > start)'));
      return;
    }
    setRegions([{ id: crypto.randomUUID(), start: a, end: b }]);
    setStatus(t('audio_redact.selection_applied', 'Timeline region applied to mute list'));
  };

  const markFromPlayhead = () => {
    const start = Math.max(0, playheadSec);
    setRegions((list) => [
      ...list,
      { id: crypto.randomUUID(), start, end: start + 5 },
    ]);
  };

  return (
    <div className="fx-panel fx-audio-redact-panel">
      <div className="fx-panel-head">{t('audio_redact.title', 'Audio Redaction (R-114)')}</div>
      <div className="fx-panel-body fx-export-form">
        <p className="fx-export-hint">
          {t(
            'audio_redact.hint',
            'Define time ranges to mute in the audio track. Export redacted audio only (.aac) or full video with muted audio (.mp4).',
          )}
        </p>

        <div className="fx-export-actions-row">
          <button type="button" className="fx-btn" onClick={addRegion} disabled={!inputPath}>
            {t('audio_redact.add_region', 'Add region')}
          </button>
          <button type="button" className="fx-btn" onClick={useTimelineSelection} disabled={!inputPath}>
            {t('audio_redact.use_timeline', 'Use timeline selection')}
          </button>
          <button type="button" className="fx-btn" onClick={markFromPlayhead} disabled={!inputPath}>
            {t('audio_redact.from_playhead', 'Add 5s from playhead')}
          </button>
        </div>

        <ul className="fx-audio-redact-list">
          {regions.map((r, i) => (
            <li key={r.id}>
              <span className="fx-audio-redact-idx">#{i + 1}</span>
              <label>
                {t('audio_redact.start', 'Start (s)')}
                <input
                  type="number"
                  className="fx-input"
                  min={0}
                  step={0.01}
                  value={r.start}
                  onChange={(e) => patchRegion(r.id, 'start', e.target.value)}
                />
              </label>
              <label>
                {t('audio_redact.end', 'End (s)')}
                <input
                  type="number"
                  className="fx-input"
                  min={0}
                  step={0.01}
                  value={r.end}
                  onChange={(e) => patchRegion(r.id, 'end', e.target.value)}
                />
              </label>
              <button type="button" className="fx-btn fx-btn-danger" onClick={() => removeRegion(r.id)} aria-label="Remove">
                ×
              </button>
            </li>
          ))}
        </ul>

        <label className="fx-export-field" style={{ marginTop: 10 }}>
          {t('audio_redact.audio_out', 'Redacted audio output')}
          <input className="fx-input fx-input-mono" value={audioOut} onChange={(e) => setAudioOut(e.target.value)} />
        </label>

        <div className="fx-a11y-row" style={{ marginTop: 8 }}>
          <input
            id="fx-redact-video"
            type="checkbox"
            checked={exportVideo}
            onChange={(e) => setExportVideo(e.target.checked)}
          />
          <label htmlFor="fx-redact-video">{t('audio_redact.include_video', 'Also export video with redacted audio')}</label>
        </div>

        {exportVideo && (
          <label className="fx-export-field">
            {t('audio_redact.video_out', 'Redacted video output')}
            <input className="fx-input fx-input-mono" value={videoOut} onChange={(e) => setVideoOut(e.target.value)} />
          </label>
        )}

        <div className="fx-export-actions-row" style={{ marginTop: 12 }}>
          <button
            type="button"
            className="fx-btn fx-btn-primary"
            disabled={!inputPath}
            onClick={() => runRedact(audioOut).catch((e) => setError(e.message))}
          >
            {t('audio_redact.export_audio', 'Export redacted audio')}
          </button>
          {exportVideo && (
            <button
              type="button"
              className="fx-btn"
              disabled={!inputPath}
              onClick={() => runRedact(videoOut).catch((e) => setError(e.message))}
            >
              {t('audio_redact.export_video', 'Export redacted video')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
