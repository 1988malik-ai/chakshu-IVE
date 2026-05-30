import { useMemo } from 'react';

const TYPE_COLORS = { I: '#22c55e', P: '#3b82f6', B: '#f59e0b', '?': '#6b7280' };

export default function VideoTimeline({
  frames = [],
  duration = 0,
  currentTime = 0,
  vfr = null,
  indexSource = null,
  onSelectFrame,
}) {
  const effectiveDuration = duration > 0
    ? duration
    : (frames.length ? Math.max(...frames.map((f) => f.pts), 0.1) : 0);

  const markers = useMemo(() => {
    if (!frames.length) return [];
    return frames.slice(0, 2000);
  }, [frames]);

  if (!markers.length) {
    return (
      <div style={{ fontSize: '0.75rem', color: 'var(--fx-muted)', padding: 8 }}>
        No frame index yet. Ingest a video, set the full path, then click <strong>Build Timeline</strong>.
        <br />
        Works with ffmpeg-only (<code>pip install imageio-ffmpeg</code>) — I/P/B types need ffprobe or ffmpeg showinfo.
      </div>
    );
  }

  const sourceNote = indexSource === 'opencv-cfr'
    ? 'CFR index (OpenCV) — frame types shown as ?'
    : indexSource === 'ffmpeg-showinfo'
      ? 'Indexed via ffmpeg showinfo'
      : indexSource === 'ffprobe'
        ? 'Indexed via ffprobe'
        : null;

  return (
    <div className="fx-timeline">
      <div style={{ display: 'flex', gap: 12, fontSize: '0.65rem', marginBottom: 6, color: 'var(--fx-muted)' }}>
        {Object.entries(TYPE_COLORS).filter(([k]) => k !== '?').map(([k, c]) => (
          <span key={k}><span style={{ color: c, fontWeight: 700 }}>{k}</span> frames</span>
        ))}
        {vfr?.vfr && <span style={{ color: '#f59e0b' }}>VFR detected</span>}
        {vfr?.avg_fps && <span>{vfr.avg_fps.toFixed(2)} avg fps</span>}
        {sourceNote && <span style={{ color: '#94a3b8' }}>{sourceNote}</span>}
      </div>
      <div
        className="fx-timeline-track"
        style={{
          position: 'relative',
          height: 28,
          background: '#1a1a1a',
          borderRadius: 4,
          border: '1px solid var(--fx-border)',
          overflow: 'hidden',
        }}
      >
        {effectiveDuration > 0 && (
          <div
            style={{
              position: 'absolute',
              left: `${Math.min(100, (currentTime / effectiveDuration) * 100)}%`,
              top: 0,
              bottom: 0,
              width: 2,
              background: '#fff',
              zIndex: 2,
            }}
          />
        )}
        {markers.map((f) => {
          const pct = effectiveDuration > 0 ? (f.pts / effectiveDuration) * 100 : (f.index / markers.length) * 100;
          const color = TYPE_COLORS[f.type] || TYPE_COLORS['?'];
          return (
            <button
              key={`${f.index}-${f.pts}`}
              type="button"
              title={`#${f.index} ${f.type} @ ${f.pts.toFixed(3)}s`}
              onClick={() => onSelectFrame?.(f)}
              style={{
                position: 'absolute',
                left: `${Math.min(99.5, Math.max(0, pct))}%`,
                top: f.type === 'I' ? 2 : 10,
                width: f.type === 'I' ? 3 : 2,
                height: f.type === 'I' ? 24 : 14,
                padding: 0,
                border: 'none',
                background: color,
                opacity: 0.85,
                cursor: 'pointer',
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
