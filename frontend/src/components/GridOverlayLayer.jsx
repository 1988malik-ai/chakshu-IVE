import { useMemo } from 'react';
import { presetConfig } from '../lib/gridOverlay';

/**
 * Non-destructive grid overlay on top of a frame preview (Examination Lab).
 */
export default function GridOverlayLayer({ preset = '8x8', opacity = 0.55, className = '' }) {
  const cfg = presetConfig(preset);
  const lines = useMemo(() => {
    const major = 'rgba(0, 220, 200, 0.95)';
    const minor = 'rgba(180, 200, 210, 0.75)';
    const out = [];

    if (cfg.style === 'thirds') {
      [33.333, 66.666].forEach((pct) => {
        out.push({ x1: pct, y1: 0, x2: pct, y2: 100, stroke: major, sw: 0.35 });
        out.push({ x1: 0, y1: pct, x2: 100, y2: pct, stroke: major, sw: 0.35 });
      });
      return out;
    }

    if (cfg.style === 'center') {
      out.push({ x1: 50, y1: 0, x2: 50, y2: 100, stroke: major, sw: 0.4 });
      out.push({ x1: 0, y1: 50, x2: 100, y2: 50, stroke: major, sw: 0.4 });
      return out;
    }

    const n = cfg.divisions || 8;
    for (let i = 1; i < n; i += 1) {
      const pct = (i / n) * 100;
      const isMajor = i % 4 === 0;
      const stroke = isMajor ? major : minor;
      const sw = isMajor ? 0.3 : 0.18;
      out.push({ x1: pct, y1: 0, x2: pct, y2: 100, stroke, sw });
      out.push({ x1: 0, y1: pct, x2: 100, y2: pct, stroke, sw });
    }
    return out;
  }, [cfg]);

  return (
    <svg
      className={`fx-grid-overlay ${className}`.trim()}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      aria-hidden
      style={{ opacity }}
    >
      {lines.map((ln, i) => (
        <line
          key={i}
          x1={ln.x1}
          y1={ln.y1}
          x2={ln.x2}
          y2={ln.y2}
          stroke={ln.stroke}
          strokeWidth={ln.sw}
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  );
}
