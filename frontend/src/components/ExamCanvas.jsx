import { useCallback, useEffect, useRef, useState } from 'react';
import { api, previewDataUrl } from '../api/client';

const TOOLS = [
  { id: 'arrow', label: 'Arrow' },
  { id: 'rect', label: 'Rectangle' },
  { id: 'line', label: 'Line' },
  { id: 'text', label: 'Text' },
  { id: 'measure', label: 'Measure' },
  { id: 'redact', label: 'Redact' },
];

const COLORS = {
  arrow: '#22d3ee',
  rect: '#22d3ee',
  line: '#a78bfa',
  text: '#f472b6',
  measure: '#fbbf24',
  redact: '#ef4444',
};

function drawShape(ctx, ann, scale) {
  const pts = ann.points || [];
  if (pts.length < 1) return;
  const color = ann.type === 'measure' ? COLORS.measure : COLORS[ann.type] || '#22d3ee';
  ctx.strokeStyle = color;
  ctx.fillStyle = ann.type === 'redact' ? 'rgba(239,68,68,0.25)' : 'transparent';
  ctx.lineWidth = 2;
  const s = (p) => [p[0] * scale.x, p[1] * scale.y];
  if (ann.type === 'arrow' && pts.length >= 2) {
    const [a, b] = [s(pts[0]), s(pts[1])];
    ctx.beginPath();
    ctx.moveTo(a[0], a[1]);
    ctx.lineTo(b[0], b[1]);
    ctx.stroke();
    const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    ctx.beginPath();
    ctx.moveTo(b[0], b[1]);
    ctx.lineTo(b[0] - 10 * Math.cos(ang - 0.4), b[1] - 10 * Math.sin(ang - 0.4));
    ctx.lineTo(b[0] - 10 * Math.cos(ang + 0.4), b[1] - 10 * Math.sin(ang + 0.4));
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
  } else if ((ann.type === 'rect' || ann.type === 'redact') && pts.length >= 2) {
    const [a, b] = [s(pts[0]), s(pts[1])];
    const w = b[0] - a[0];
    const h = b[1] - a[1];
    ctx.fillRect(a[0], a[1], w, h);
    ctx.strokeRect(a[0], a[1], w, h);
  } else if ((ann.type === 'line' || ann.type === 'measure') && pts.length >= 2) {
    const [a, b] = [s(pts[0]), s(pts[1])];
    ctx.beginPath();
    ctx.moveTo(a[0], a[1]);
    ctx.lineTo(b[0], b[1]);
    ctx.stroke();
    if (ann.text) {
      ctx.fillStyle = COLORS.measure;
      ctx.font = '12px monospace';
      ctx.fillText(ann.text, a[0], a[1] - 4);
    }
  } else if (ann.type === 'text' && pts.length >= 1) {
    const [a] = [s(pts[0])];
    ctx.fillStyle = COLORS.text;
    ctx.font = '14px sans-serif';
    ctx.fillText(ann.text || 'Label', a[0], a[1]);
  }
}

export default function ExamCanvas({
  imageSrc,
  sessionId,
  mediaId,
  frameIndex = 0,
  timeSec = 0,
  onPreviewUpdate,
  onStatus,
  onError,
  pixelsPerUnit = 1,
  unitName = 'px',
  deltaTimeSec = null,
}) {
  const [tool, setTool] = useState('arrow');
  const [snap, setSnap] = useState(true);
  const [groupId, setGroupId] = useState('');
  const [annotations, setAnnotations] = useState([]);
  const [groups, setGroups] = useState([]);
  const [draft, setDraft] = useState(null);
  const [measurements, setMeasurements] = useState([]);
  const imgRef = useRef(null);
  const canvasRef = useRef(null);
  const snapGrid = snap ? 10 : 0;

  const getScale = useCallback(() => {
    const img = imgRef.current;
    if (!img || !img.clientWidth) return { x: 1, y: 1 };
    return {
      x: img.clientWidth / (img.naturalWidth || img.clientWidth),
      y: img.clientHeight / (img.naturalHeight || img.clientHeight),
    };
  }, []);

  const toImageCoords = useCallback((e) => {
    const img = imgRef.current;
    if (!img) return { x: 0, y: 0 };
    const rect = img.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * (img.naturalWidth || rect.width);
    const y = ((e.clientY - rect.top) / rect.height) * (img.naturalHeight || rect.height);
    return { x: Math.round(x), y: Math.round(y) };
  }, []);

  const refreshList = useCallback(async () => {
    if (!mediaId) return;
    try {
      const data = await api.markupListAnnotations(mediaId, frameIndex);
      setAnnotations(data.annotations || []);
      setGroups(data.groups || []);
      const m = await api.markupListMeasurements(mediaId);
      setMeasurements(m.measurements || []);
    } catch (e) {
      // Non-fatal — annotations may still have been saved
      console.warn('Markup list refresh:', e.message);
    }
  }, [mediaId, frameIndex]);

  useEffect(() => { refreshList(); }, [refreshList]);

  const paint = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img || !img.clientWidth || !img.clientHeight) return;
    const w = img.clientWidth;
    const h = img.clientHeight;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const scale = getScale();
    annotations.forEach((a) => drawShape(ctx, a, scale));
    if (draft?.start && draft?.end) {
      drawShape(ctx, { type: draft.type, points: [[draft.start.x, draft.start.y], [draft.end.x, draft.end.y]], text: draft.text || '' }, scale);
    }
    if (snap) {
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      for (let x = 0; x < canvas.width; x += 10 * scale.x) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 10 * scale.y) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }
    }
  }, [annotations, draft, getScale, snap]);

  useEffect(() => {
    paint();
  }, [paint, imageSrc, draft]);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return undefined;
    const ro = new ResizeObserver(() => paint());
    ro.observe(img);
    return () => ro.disconnect();
  }, [paint]);

  const finishShape = async (start, end) => {
    if (!sessionId || !mediaId) return;
    const img = imgRef.current;
    const w = img?.naturalWidth || 0;
    const h = img?.naturalHeight || 0;
    const points = [[start.x, start.y], [end.x, end.y]];

    try {
      if (tool === 'redact') {
        const r = await api.markupRedact(sessionId, [{
          x1: Math.min(start.x, end.x),
          y1: Math.min(start.y, end.y),
          x2: Math.max(start.x, end.x),
          y2: Math.max(start.y, end.y),
          mode: 'pixelate',
        }]);
        onPreviewUpdate?.(previewDataUrl(r.preview));
        onStatus?.('Redaction applied to master frame');
        return;
      }
      if (tool === 'measure') {
        const r = await api.markupMeasure({
          session_id: sessionId,
          media_id: mediaId,
          frame_index: frameIndex,
          time_sec: timeSec,
          p1: points[0],
          p2: points[1],
          pixels_per_unit: pixelsPerUnit,
          unit_name: unitName,
          delta_time_sec: deltaTimeSec,
          group_id: groupId || null,
          snap_grid: snapGrid,
          image_width: w,
          image_height: h,
        });
        onPreviewUpdate?.(previewDataUrl(r.preview));
        onStatus?.(`Measured: ${r.measurement?.distance?.toFixed(2)} ${r.measurement?.unit}`);
        await refreshList();
        return;
      }
      if (tool === 'text') {
        const text = window.prompt('Annotation text:', '') || '';
        if (!text) return;
        await api.markupAddAnnotation({
          media_id: mediaId,
          type: 'text',
          frame_index: frameIndex,
          time_sec: timeSec,
          points: [[start.x, start.y]],
          text,
          group_id: groupId || null,
          snap_grid: snapGrid,
          image_width: w,
          image_height: h,
        });
      } else {
        await api.markupAddAnnotation({
          media_id: mediaId,
          type: tool,
          frame_index: frameIndex,
          time_sec: timeSec,
          points,
          group_id: groupId || null,
          snap_grid: snapGrid,
          image_width: w,
          image_height: h,
        });
      }
      const rendered = await api.markupRender(sessionId, mediaId, frameIndex, false);
      onPreviewUpdate?.(previewDataUrl(rendered.preview));
      onStatus?.(`Added ${tool} annotation`);
      await refreshList();
    } catch (e) {
      onError?.(e.message);
    }
  };

  const onMouseDown = (e) => {
    if (tool === 'text') {
      const p = toImageCoords(e);
      finishShape(p, p);
      return;
    }
    setDraft({ type: tool === 'redact' ? 'redact' : tool, start: toImageCoords(e), end: null });
  };

  const onMouseMove = (e) => {
    if (!draft?.start) return;
    setDraft((d) => ({ ...d, end: toImageCoords(e) }));
    requestAnimationFrame(paint);
  };

  const onMouseUp = (e) => {
    if (!draft?.start) return;
    const end = toImageCoords(e);
    finishShape(draft.start, end);
    setDraft(null);
  };

  const burnAnnotations = async () => {
    try {
      const r = await api.markupRender(sessionId, mediaId, frameIndex, true);
      onPreviewUpdate?.(previewDataUrl(r.preview));
      setAnnotations([]);
      onStatus?.('Annotations burned into master frame');
    } catch (err) {
      onError?.(err.message);
    }
  };

  return (
    <div className="fx-markup">
      <div className="fx-markup-toolbar">
        {TOOLS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`fx-btn ${tool === t.id ? 'fx-btn-primary' : ''}`}
            onClick={() => setTool(t.id)}
          >
            {t.label}
          </button>
        ))}
        <label style={{ marginLeft: 8, fontSize: '0.75rem', color: 'var(--fx-muted)' }}>
          <input type="checkbox" checked={snap} onChange={(e) => setSnap(e.target.checked)} /> Snap 10px
        </label>
        <input
          className="fx-input"
          placeholder="Group ID (optional)"
          value={groupId}
          onChange={(e) => setGroupId(e.target.value)}
          style={{ width: 120, marginLeft: 8 }}
        />
        <button type="button" className="fx-btn" onClick={burnAnnotations}>Apply to Frame</button>
      </div>
      <div className="fx-markup-stage">
        {imageSrc ? (
          <div className="fx-markup-frame">
            <img ref={imgRef} src={imageSrc} alt="Examination" onLoad={paint} draggable={false} />
            <canvas
              ref={canvasRef}
              className="fx-markup-canvas"
              onMouseDown={onMouseDown}
              onMouseMove={onMouseMove}
              onMouseUp={onMouseUp}
              onMouseLeave={() => setDraft(null)}
            />
          </div>
        ) : (
          <span style={{ color: '#555', padding: 40 }}>Load evidence to begin markup</span>
        )}
      </div>
      <div className="fx-markup-side">
        <div style={{ fontSize: '0.7rem', color: 'var(--fx-muted)', marginBottom: 6 }}>Annotations (frame #{frameIndex})</div>
        <ul className="fx-markup-list">
          {annotations.map((a) => (
            <li key={a.id}>
              <span>{a.type}</span>
              {a.group_id && <span className="fx-badge fx-badge-cat">{a.group_id}</span>}
              <button type="button" className="fx-btn fx-btn-danger" style={{ padding: '2px 6px', fontSize: '0.65rem' }} onClick={async () => {
                await api.markupDeleteAnnotation(mediaId, a.id);
                await refreshList();
                onStatus?.('Annotation removed');
              }}>×</button>
            </li>
          ))}
        </ul>
        {measurements.length > 0 && (
          <>
            <div style={{ fontSize: '0.7rem', color: 'var(--fx-muted)', marginTop: 10 }}>Measurements</div>
            <ul className="fx-markup-list">
              {measurements.filter((m) => m.frame_index === frameIndex).map((m) => (
                <li key={m.id}>{m.label || `${m.result?.distance?.toFixed(2)} ${m.result?.unit}`}</li>
              ))}
            </ul>
          </>
        )}
        {groups.length > 0 && (
          <div style={{ fontSize: '0.65rem', color: 'var(--fx-muted)', marginTop: 8 }}>Groups: {groups.join(', ')}</div>
        )}
      </div>
    </div>
  );
}
