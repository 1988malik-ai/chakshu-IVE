import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

const TYPE = {
  I: { color: '#34d399', glow: 'rgba(52,211,153,0.45)', label: 'I-Frame' },
  P: { color: '#60a5fa', glow: 'rgba(96,165,250,0.35)', label: 'P-Frame' },
  B: { color: '#fbbf24', glow: 'rgba(251,191,36,0.35)', label: 'B-Frame' },
  '?': { color: '#64748b', glow: 'rgba(100,116,139,0.25)', label: 'Unknown' },
};

const LANES = { I: 36, P: 68, B: 100, '?': 68 };
const MAIN_H = 168;
const MINI_H = 28;

function formatTc(sec, fps = 30) {
  if (sec == null || Number.isNaN(sec)) return '00:00:00:00';
  const s = Math.max(0, sec);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const ss = Math.floor(s % 60);
  const fr = Math.floor((s % 1) * fps);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}:${String(fr).padStart(2, '0')}`;
}

function formatClock(sec) {
  const m = Math.floor(sec / 60);
  const s = (sec % 60).toFixed(2);
  return `${m}:${s.padStart(5, '0')}`;
}

function formatDur(sec) {
  if (!sec) return '0:00';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  if (h) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export default function ForensicTimeline({
  timeline = null,
  currentTime = 0,
  onSeek,
  onRegionSelect,
  loading = false,
}) {
  const canvasRef = useRef(null);
  const miniRef = useRef(null);
  const rootRef = useRef(null);
  const wrapRef = useRef(null);
  const [zoom, setZoom] = useState(1);
  const [scroll, setScroll] = useState(0);
  const [filter, setFilter] = useState({ I: true, P: true, B: true, '?': true });
  const [region, setRegion] = useState(null);
  const dragRef = useRef(null);

  const frames = timeline?.frames || [];
  const duration = timeline?.duration || 0;
  const fps = timeline?.fps || timeline?.vfr?.avg_fps || 30;
  const summary = timeline?.summary || {};

  const viewStart = scroll;
  const viewEnd = Math.min(duration, scroll + duration / zoom);

  const visibleFrames = useMemo(() => {
    if (!frames.length) return [];
    return frames.filter((f) => {
      if (!filter[f.type] && !(f.type === '?' && filter['?'])) return false;
      return f.pts >= viewStart - 0.05 && f.pts <= viewEnd + 0.05;
    });
  }, [frames, filter, viewStart, viewEnd]);

  const maxSize = useMemo(() => {
    const sizes = frames.filter((f) => f.size).map((f) => f.size);
    return sizes.length ? Math.max(...sizes) : 1;
  }, [frames]);

  const layoutWidth = useCallback(() => {
    const el = wrapRef.current || rootRef.current;
    if (!el) return 0;
    return Math.max(0, Math.floor(el.clientWidth));
  }, []);

  const paintCanvas = useCallback((canvas, cssW, cssH, drawFn) => {
    if (!canvas || cssW <= 0) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawFn(ctx, cssW, cssH);
  }, []);

  const drawMini = useCallback(() => {
    const canvas = miniRef.current;
    const w = layoutWidth();
    if (!canvas || !w || !duration) return;

    paintCanvas(canvas, w, MINI_H, (ctx, cw) => {
      ctx.clearRect(0, 0, cw, MINI_H);

      const grad = ctx.createLinearGradient(0, 0, 0, MINI_H);
      grad.addColorStop(0, '#1e293b');
      grad.addColorStop(1, '#0f172a');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, cw, MINI_H);

      const xOf = (t) => (t / duration) * cw;
      frames.forEach((f) => {
        if (f.type !== 'I' && !f.key_frame) return;
        const x = xOf(f.pts);
        ctx.fillStyle = TYPE.I.color;
        ctx.fillRect(x, 8, 2, 12);
      });

      const vx1 = xOf(viewStart);
      const vx2 = xOf(viewEnd);
      ctx.fillStyle = 'rgba(59,130,246,0.22)';
      ctx.fillRect(vx1, 0, Math.max(2, vx2 - vx1), MINI_H);
      ctx.strokeStyle = 'rgba(59,130,246,0.6)';
      ctx.lineWidth = 1;
      ctx.strokeRect(vx1, 0, Math.max(2, vx2 - vx1), MINI_H);

      const px = xOf(currentTime);
      ctx.strokeStyle = '#f8fafc';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(px, 0);
      ctx.lineTo(px, MINI_H);
      ctx.stroke();
    });
  }, [frames, duration, viewStart, viewEnd, currentTime, layoutWidth, paintCanvas]);

  const drawMain = useCallback(() => {
    const canvas = canvasRef.current;
    const w = layoutWidth();
    if (!canvas || !w) return;

    paintCanvas(canvas, w, MAIN_H, (ctx, cw, h) => {
      ctx.clearRect(0, 0, cw, h);

      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, '#111827');
      grad.addColorStop(0.5, '#0b1120');
      grad.addColorStop(1, '#020617');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, cw, h);

      const span = Math.max(0.001, viewEnd - viewStart);
      const xOf = (t) => ((t - viewStart) / span) * cw;

      ctx.fillStyle = 'rgba(15,23,42,0.95)';
      ctx.fillRect(0, 0, cw, 26);
      const tickStep = span > 120 ? 10 : span > 30 ? 5 : span > 10 ? 1 : 0.25;
      ctx.strokeStyle = 'rgba(148,163,184,0.25)';
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px ui-monospace, SF Mono, monospace';
      for (let t = Math.floor(viewStart / tickStep) * tickStep; t <= viewEnd; t += tickStep) {
        const x = xOf(t);
        const major = Math.abs((t / tickStep) % 5) < 0.01 || tickStep >= 5;
        ctx.beginPath();
        ctx.moveTo(x, major ? 14 : 20);
        ctx.lineTo(x, 26);
        ctx.stroke();
        if (major && x + 48 < cw) ctx.fillText(formatClock(t), x + 3, 11);
      }

      Object.entries(LANES).forEach(([type, y]) => {
        ctx.fillStyle = type === 'I' ? 'rgba(52,211,153,0.04)' : 'rgba(30,41,59,0.45)';
        ctx.fillRect(28, y, cw - 28, 24);
      });
      ctx.strokeStyle = 'rgba(255,255,255,0.04)';
      [32, 64, 96, 128].forEach((y) => {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(cw, y);
        ctx.stroke();
      });

      const iframes = visibleFrames.filter((f) => f.type === 'I' || f.key_frame);
      ctx.strokeStyle = 'rgba(52,211,153,0.15)';
      ctx.lineWidth = 1;
      for (let i = 0; i < iframes.length - 1; i += 1) {
        const a = xOf(iframes[i].pts);
        const b = xOf(iframes[i + 1].pts);
        if (b - a > 4) ctx.strokeRect(a, 34, b - a, 90);
      }

      visibleFrames.forEach((f) => {
        const meta = TYPE[f.type] || TYPE['?'];
        if (!filter[f.type] && !(f.type === '?' && filter['?'])) return;
        const x = xOf(f.pts);
        const laneY = LANES[f.type] ?? LANES['?'];
        const sizeRatio = f.size ? f.size / maxSize : 0.5;
        const barH = f.type === 'I' ? 16 + sizeRatio * 6 : 8 + sizeRatio * 4;
        const barW = f.type === 'I' ? 3 : 2;
        ctx.shadowColor = meta.glow;
        ctx.shadowBlur = f.type === 'I' ? 6 : 2;
        ctx.fillStyle = meta.color;
        ctx.globalAlpha = f.type === 'I' ? 1 : 0.82;
        ctx.fillRect(x, laneY + (24 - barH) / 2, barW, barH);
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
      });

      if (region) {
        const x1 = xOf(region[0]);
        const x2 = xOf(region[1]);
        const left = Math.min(x1, x2);
        const width = Math.abs(x2 - x1);
        ctx.fillStyle = 'rgba(59,130,246,0.12)';
        ctx.fillRect(left, 28, width, 112);
        ctx.strokeStyle = 'rgba(59,130,246,0.55)';
        ctx.setLineDash([4, 3]);
        ctx.strokeRect(left, 28, width, 112);
        ctx.setLineDash([]);
      }

      if (duration > 0) {
        const px = xOf(currentTime);
        ctx.strokeStyle = '#f8fafc';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(px, 0);
        ctx.lineTo(px, h);
        ctx.stroke();
        ctx.fillStyle = '#f8fafc';
        ctx.beginPath();
        ctx.moveTo(px - 7, 0);
        ctx.lineTo(px + 7, 0);
        ctx.lineTo(px, 10);
        ctx.fill();
        ctx.fillStyle = 'rgba(248,250,252,0.9)';
        ctx.font = '9px ui-monospace, monospace';
        ctx.fillText(formatTc(currentTime, fps), Math.min(px + 4, cw - 72), 24);
      }

      ctx.font = '600 9px system-ui,sans-serif';
      [['I', '#34d399'], ['P', '#60a5fa'], ['B', '#fbbf24']].forEach(([label, color]) => {
        ctx.fillStyle = color;
        ctx.fillText(label, 8, (LANES[label] ?? 68) + 15);
      });
    });
  }, [visibleFrames, viewStart, viewEnd, currentTime, duration, filter, region, fps, maxSize, layoutWidth, paintCanvas]);

  const redraw = useCallback(() => {
    drawMini();
    drawMain();
  }, [drawMini, drawMain]);

  useEffect(() => { redraw(); }, [redraw, timeline, zoom, scroll]);

  useEffect(() => {
    const ro = new ResizeObserver(redraw);
    if (rootRef.current) ro.observe(rootRef.current);
    return () => ro.disconnect();
  }, [redraw]);

  const clientToTime = (clientX) => {
    const wrap = wrapRef.current;
    if (!wrap || !duration) return 0;
    const rect = wrap.getBoundingClientRect();
    const ratio = (clientX - rect.left) / rect.width;
    const span = Math.max(0.001, viewEnd - viewStart);
    return Math.max(0, Math.min(duration, viewStart + ratio * span));
  };

  const miniToTime = (clientX) => {
    const wrap = wrapRef.current;
    if (!wrap || !duration) return 0;
    const rect = wrap.getBoundingClientRect();
    const ratio = (clientX - rect.left) / rect.width;
    return Math.max(0, Math.min(duration, ratio * duration));
  };

  const commitRegion = (r) => {
    if (!r) return;
    const a = Math.min(r[0], r[1]);
    const b = Math.max(r[0], r[1]);
    if (b - a > 0.05) onRegionSelect?.(a, b);
  };

  const onPointerDown = (e) => {
    const t = clientToTime(e.clientX);
    if (e.shiftKey) {
      dragRef.current = { mode: 'region', start: t, surface: 'main' };
      setRegion([t, t]);
      return;
    }
    dragRef.current = { mode: 'seek', start: t, surface: 'main' };
    onSeek?.(t);
  };

  const onMiniDown = (e) => {
    const t = miniToTime(e.clientX);
    dragRef.current = { mode: 'pan', start: t, surface: 'mini' };
    const span = duration / zoom;
    setScroll(Math.max(0, Math.min(duration - span, t - span / 2)));
    onSeek?.(t);
  };

  const onPointerMove = (e) => {
    if (!dragRef.current) return;
    if (dragRef.current.surface === 'mini') {
      const t = miniToTime(e.clientX);
      const span = duration / zoom;
      setScroll(Math.max(0, Math.min(duration - span, t - span / 2)));
      onSeek?.(t);
      return;
    }
    const t = clientToTime(e.clientX);
    if (dragRef.current.mode === 'region') {
      setRegion([dragRef.current.start, t]);
    } else {
      onSeek?.(t);
    }
  };

  const onPointerUp = () => {
    if (dragRef.current?.mode === 'region' && region) commitRegion(region);
    dragRef.current = null;
  };

  const onWheel = (e) => {
    e.preventDefault();
    if (e.ctrlKey || e.metaKey) {
      setZoom((z) => Math.min(48, Math.max(1, z * (e.deltaY < 0 ? 1.12 : 0.89))));
    } else {
      setScroll((s) => Math.max(0, Math.min(Math.max(0, duration - duration / zoom), s + e.deltaY * 0.015)));
    }
  };

  const fitView = () => {
    setZoom(1);
    setScroll(0);
  };

  if (loading) {
    return (
      <div className="ftl-root ftl-loading">
        <div className="ftl-spinner" />
        <span>Building forensic frame index…</span>
        <p className="ftl-loading-sub">Scanning I/P/B structure · up to 25,000 frames</p>
      </div>
    );
  }

  if (!frames.length) {
    return (
      <div className="ftl-root ftl-empty">
        <div className="ftl-empty-icon">▶</div>
        <h3>Forensic Timeline</h3>
        <p>Upload video evidence — a deep index runs automatically. Use <strong>Deep Index</strong> to rebuild or refresh.</p>
      </div>
    );
  }

  const pct = duration ? ((currentTime / duration) * 100).toFixed(1) : 0;

  return (
    <div className="ftl-root" ref={rootRef}>
      <div className="ftl-header">
        <div className="ftl-tc-block">
          <div className="ftl-tc">{formatTc(currentTime, fps)}</div>
          <div className="ftl-tc-sub">{pct}% · {formatDur(duration)} total</div>
        </div>
        <div className="ftl-chips">
          {['I', 'P', 'B'].map((k) => (
            <button
              key={k}
              type="button"
              className={`ftl-chip ftl-chip-${k.toLowerCase()} ${filter[k] ? 'on' : ''}`}
              onClick={() => setFilter((f) => ({ ...f, [k]: !f[k] }))}
            >
              {k} <strong>{summary[k] ?? 0}</strong>
            </button>
          ))}
          <span className={`ftl-quality ftl-quality-${timeline?.index_quality || 'standard'}`}>
            {timeline?.index_quality === 'forensic' ? 'FORENSIC INDEX' : 'STANDARD INDEX'}
          </span>
          {timeline?.vfr?.vfr && <span className="ftl-chip ftl-chip-vfr">VFR</span>}
          {timeline?.from_cache && <span className="ftl-chip ftl-chip-cache">cached</span>}
        </div>
        <div className="ftl-zoom">
          <button type="button" title="Fit" onClick={fitView}>⊡</button>
          <button type="button" onClick={() => setZoom((z) => Math.max(1, z / 1.5))}>−</button>
          <span>{zoom.toFixed(1)}×</span>
          <button type="button" onClick={() => setZoom((z) => Math.min(48, z * 1.5))}>+</button>
        </div>
      </div>

      <div
        ref={wrapRef}
        className="ftl-stack"
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        onWheel={onWheel}
      >
        <div
          className="ftl-minimap"
          onPointerDown={onMiniDown}
          role="presentation"
        >
          <canvas ref={miniRef} className="ftl-canvas" />
        </div>
        <div
          className="ftl-canvas-wrap"
          onPointerDown={onPointerDown}
          role="presentation"
        >
          <canvas ref={canvasRef} className="ftl-canvas" />
        </div>
      </div>

      <div className="ftl-footer">
        <span>{timeline?.frame_sample_count?.toLocaleString()} frames</span>
        <span>{timeline?.iframe_count} keyframes</span>
        <span>{timeline?.codec || '—'} · {timeline?.width}×{timeline?.height}</span>
        <span>{fps ? `${fps.toFixed(2)} fps` : '—'}</span>
        <span className="ftl-src" title={timeline?.index_source}>{timeline?.index_source}</span>
        <span className="ftl-hint">Shift+drag region · scroll pan · ⌘/ctrl+scroll zoom</span>
        {region && (
          <span className="ftl-region">
            Region {formatClock(Math.min(...region))} → {formatClock(Math.max(...region))}
          </span>
        )}
      </div>
    </div>
  );
}

export { formatTc };
