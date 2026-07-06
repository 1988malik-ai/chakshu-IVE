import { useCallback } from 'react';
import { api } from '../api/client';
import { formatClock, formatDur, formatTc } from '../lib/timecode';

export default function RegionAnalysisPanel({
  mediaPath,
  regionStart,
  regionEnd,
  onRegionChange,
  seekTime = 0,
  duration = 0,
  fps = 30,
  regionAnalysis,
  onAnalysis,
  onSeek,
  t = (k, d) => d,
  setStatus,
  setError,
  compact = false,
  embedded = false,
}) {
  const isCompact = compact || embedded;
  const patch = (updates) => onRegionChange?.(updates);

  const analyze = useCallback(async () => {
    if (!mediaPath) {
      setError?.(t('region.no_media', 'Load video evidence first'));
      return;
    }
    const start = Math.min(regionStart, regionEnd);
    const end = Math.max(regionStart, regionEnd);
    setError?.('');
    try {
      const r = await api.timelineRegion(mediaPath, start, end);
      onAnalysis?.(r);
      setStatus?.(
        `${t('region.analyzed', 'Region analyzed')}: ${formatTc(start, fps)} – ${formatTc(end, fps)} · ${r.frame_count} frames`,
      );
    } catch (e) {
      setError?.(e.message);
    }
  }, [mediaPath, regionStart, regionEnd, fps, onAnalysis, setStatus, setError, t]);

  const filterIFrames = useCallback(async () => {
    if (!mediaPath) return;
    const start = Math.min(regionStart, regionEnd);
    const end = Math.max(regionStart, regionEnd);
    try {
      const r = await api.timelineFilter({
        path: mediaPath,
        types: ['I'],
        start_sec: start,
        end_sec: end,
        limit: 500,
      });
      setStatus?.(`${t('region.iframes', 'I-frames in region')}: ${r.count ?? r.frames?.length ?? 0}`);
    } catch (e) {
      setError?.(e.message);
    }
  }, [mediaPath, regionStart, regionEnd, setStatus, setError, t]);

  const copyFrameList = useCallback(async () => {
    if (!regionAnalysis?.frames?.length) return;
    const lines = regionAnalysis.frames.map(
      (f) => `#${f.index}\t${f.type}\t${f.pts?.toFixed(4)}s\t${formatTc(f.pts, fps)}`,
    );
    const header = `Region ${regionAnalysis.start_sec?.toFixed(3)}s – ${regionAnalysis.end_sec?.toFixed(3)}s`;
    await navigator.clipboard.writeText([header, ...lines].join('\n'));
    setStatus?.(t('region.copied', 'Region frame list copied to clipboard'));
  }, [regionAnalysis, fps, setStatus, t]);

  const start = Math.min(regionStart, regionEnd);
  const end = Math.max(regionStart, regionEnd);

  return (
    <div className={`fx-panel fx-region-panel${isCompact ? ' fx-region-panel-compact' : ''}${embedded ? ' fx-region-panel-embedded' : ''}`}>
      {embedded ? (
        <div className="ftl-section-label">{t('region.title', 'Region-based analysis')}</div>
      ) : (
        <div className="fx-panel-head">{t('region.title', 'Region-based analysis')}</div>
      )}
      <div className={embedded ? 'ftl-analysis-body' : 'fx-panel-body'}>
        <p className="fx-export-hint">
          {t('region.hint', 'Select a time range on the timeline (Shift+drag) or edit start/end below, then analyze I/P/B frame distribution in that region.')}
        </p>

        <div className="fx-region-time-row">
          <label>
            <span>{t('region.start', 'Start (sec)')}</span>
            <input
              type="number"
              className="fx-input"
              step="0.001"
              min={0}
              max={duration || undefined}
              value={regionStart}
              onChange={(e) => patch({ regionStart: Number(e.target.value) })}
            />
            <code>{formatTc(start, fps)}</code>
          </label>
          <label>
            <span>{t('region.end', 'End (sec)')}</span>
            <input
              type="number"
              className="fx-input"
              step="0.001"
              min={0}
              max={duration || undefined}
              value={regionEnd}
              onChange={(e) => patch({ regionEnd: Number(e.target.value) })}
            />
            <code>{formatTc(end, fps)}</code>
          </label>
        </div>

        <div className="fx-region-presets">
          <button type="button" className="fx-btn" disabled={!onSeek} onClick={() => patch({ regionStart: seekTime })}>
            {t('region.set_start_playhead', 'Start = playhead')}
          </button>
          <button type="button" className="fx-btn" disabled={!onSeek} onClick={() => patch({ regionEnd: seekTime })}>
            {t('region.set_end_playhead', 'End = playhead')}
          </button>
          <button
            type="button"
            className="fx-btn"
            disabled={!duration}
            onClick={() => patch({
              regionStart: Math.max(0, seekTime - 5),
              regionEnd: Math.min(duration, seekTime + 5),
            })}
          >
            {t('region.window_10s', '±5s around playhead')}
          </button>
          {duration > 0 && (
            <button type="button" className="fx-btn" onClick={() => patch({ regionStart: 0, regionEnd: duration })}>
              {t('region.full_clip', 'Full clip')}
            </button>
          )}
        </div>

        <div className="fx-export-actions-row">
          <button type="button" className="fx-btn fx-btn-primary" disabled={!mediaPath} onClick={analyze}>
            {t('region.analyze', 'Analyze region')}
          </button>
          <button type="button" className="fx-btn" disabled={!mediaPath} onClick={filterIFrames}>
            {t('region.list_iframes', 'List I-frames in region')}
          </button>
          {onSeek && (
            <>
              <button type="button" className="fx-btn" onClick={() => onSeek(start)}>{t('region.seek_start', 'Go to start')}</button>
              <button type="button" className="fx-btn" onClick={() => onSeek(end)}>{t('region.seek_end', 'Go to end')}</button>
            </>
          )}
        </div>

        {regionAnalysis && (
          <div className="fx-region-results">
            <div className="fx-region-stats">
              <div><strong>{t('region.duration', 'Duration')}</strong> {formatDur(regionAnalysis.duration_sec ?? (end - start))}</div>
              <div><strong>{t('region.frames', 'Frames')}</strong> {regionAnalysis.frame_count}</div>
              <div><strong>I</strong> {regionAnalysis.types?.I ?? 0}</div>
              <div><strong>P</strong> {regionAnalysis.types?.P ?? 0}</div>
              <div><strong>B</strong> {regionAnalysis.types?.B ?? 0}</div>
              {regionAnalysis.keyframe_count != null && (
                <div><strong>{t('region.keyframes', 'Keyframes')}</strong> {regionAnalysis.keyframe_count}</div>
              )}
              {regionAnalysis.avg_pkt_size != null && (
                <div><strong>{t('region.avg_size', 'Avg size')}</strong> {Math.round(regionAnalysis.avg_pkt_size)} B</div>
              )}
            </div>
            {regionAnalysis.frames?.length > 0 && (
              <>
                <table className="fx-table fx-region-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>{t('region.col_type', 'Type')}</th>
                      <th>{t('region.col_pts', 'PTS')}</th>
                      <th>{t('region.col_tc', 'Timecode')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {regionAnalysis.frames.slice(0, isCompact ? 8 : 20).map((f) => (
                      <tr key={`${f.index}-${f.pts}`}>
                        <td>{f.index}</td>
                        <td><span className={`fx-region-type fx-region-type-${f.type}`}>{f.type}</span></td>
                        <td>{f.pts?.toFixed(4)}s</td>
                        <td>{formatTc(f.pts, fps)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button type="button" className="fx-btn" style={{ marginTop: 8 }} onClick={copyFrameList}>
                  {t('region.copy_list', 'Copy frame list')}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
