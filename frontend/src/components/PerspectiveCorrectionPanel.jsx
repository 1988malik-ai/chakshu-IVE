import { useCallback, useEffect, useRef, useState } from 'react';
import { api, previewDataUrl } from '../api/client';
import {
  CORNER_LABELS,
  cornersToParams,
  defaultCorners,
  fullFrameCorners,
  loadPerspectiveCorners,
  savePerspectiveCorners,
} from '../lib/perspectiveCorrection';

const FILTER_ID = 'geo_keystone';
const AUTO_FILTER_ID = 'adv_perspective';

function quadPath(corners, scale) {
  if (!corners?.length) return '';
  const pts = corners.map(([x, y]) => `${x * scale.x},${y * scale.y}`);
  return `M ${pts[0]} L ${pts[1]} L ${pts[2]} L ${pts[3]} Z`;
}

export default function PerspectiveCorrectionPanel({
  imageSrc,
  sessionId,
  mediaKey = '',
  disabled = false,
  onPreviewUpdate,
  onApplied,
  setStatus,
  setError,
  t = (k, d) => d,
}) {
  const imgRef = useRef(null);
  const rootRef = useRef(null);
  const dragRef = useRef(null);
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 });
  const [corners, setCorners] = useState([]);
  const [previewing, setPreviewing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [active, setActive] = useState(false);

  const syncSize = useCallback(() => {
    const img = imgRef.current;
    if (!img?.naturalWidth) return;
    const w = img.naturalWidth;
    const h = img.naturalHeight;
    setImgSize({ w, h });
    setCorners((prev) => {
      if (prev.length === 4) return prev;
      const saved = loadPerspectiveCorners(mediaKey);
      if (saved?.length === 4) return saved;
      return defaultCorners(w, h);
    });
  }, [mediaKey]);

  useEffect(() => {
    syncSize();
  }, [imageSrc, syncSize]);

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
    if (!img) return [0, 0];
    const rect = img.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * (img.naturalWidth || rect.width);
    const y = ((clientY - rect.top) / rect.height) * (img.naturalHeight || rect.height);
    return [
      Math.max(0, Math.min(img.naturalWidth || 0, x)),
      Math.max(0, Math.min(img.naturalHeight || 0, y)),
    ];
  }, []);

  const updateCorner = useCallback((index, x, y) => {
    setCorners((prev) => {
      const next = prev.map((c, i) => (i === index ? [x, y] : c));
      savePerspectiveCorners(mediaKey, next);
      return next;
    });
  }, [mediaKey]);

  const onPointerDown = useCallback((index, e) => {
    if (disabled) return;
    e.preventDefault();
    dragRef.current = { index };
    e.currentTarget.setPointerCapture(e.pointerId);
  }, [disabled]);

  const onPointerMove = useCallback((e) => {
    if (!dragRef.current) return;
    const [x, y] = toImageCoords(e.clientX, e.clientY);
    updateCorner(dragRef.current.index, x, y);
  }, [toImageCoords, updateCorner]);

  const onPointerUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  const resetCorners = useCallback((mode = 'inset') => {
    if (!imgSize.w) return;
    const next = mode === 'full' ? fullFrameCorners(imgSize.w, imgSize.h) : defaultCorners(imgSize.w, imgSize.h);
    setCorners(next);
    savePerspectiveCorners(mediaKey, next);
  }, [imgSize, mediaKey]);

  const runPreview = useCallback(async () => {
    if (!sessionId || corners.length < 4) return;
    setPreviewing(true);
    setError?.('');
    try {
      const r = await api.forensicsPreviewFilter(sessionId, FILTER_ID, cornersToParams(corners));
      onPreviewUpdate?.(previewDataUrl(r.preview));
      setStatus?.(t('perspective.previewed', 'Perspective correction preview'));
    } catch (e) {
      setError?.(e.message);
    } finally {
      setPreviewing(false);
    }
  }, [sessionId, corners, onPreviewUpdate, setStatus, setError, t]);

  const applyCorrection = useCallback(async () => {
    if (!sessionId || corners.length < 4) return;
    setApplying(true);
    setError?.('');
    try {
      const r = await api.forensicsApplyFilter(sessionId, FILTER_ID, cornersToParams(corners), { insertAt: 0 });
      onApplied?.(r);
      setStatus?.(t('perspective.applied', 'Perspective correction applied to examination frame'));
    } catch (e) {
      setError?.(e.message);
    } finally {
      setApplying(false);
    }
  }, [sessionId, corners, onApplied, setStatus, setError, t]);

  const autoStraighten = useCallback(async () => {
    if (!sessionId) return;
    setApplying(true);
    setError?.('');
    try {
      const r = await api.forensicsApplyFilter(sessionId, AUTO_FILTER_ID);
      onApplied?.(r);
      setStatus?.(t('perspective.auto', 'Auto perspective straightening applied'));
    } catch (e) {
      setError?.(e.message);
    } finally {
      setApplying(false);
    }
  }, [sessionId, onApplied, setStatus, setError, t]);

  const scale = getScale();

  return (
    <div className={`fx-perspective-panel${active ? ' fx-perspective-panel-active' : ''}`}>
      <div className="fx-perspective-head">
        <label className="fx-grid-toggle">
          <input
            type="checkbox"
            checked={active}
            disabled={disabled || !imageSrc}
            onChange={(e) => setActive(e.target.checked)}
          />
          <span>{t('perspective.title', 'Perspective correction')}</span>
        </label>
      </div>
      {active && imageSrc && (
        <div className="fx-perspective-body">
          <p className="fx-grid-hint">
            {t('perspective.hint', 'Drag the four corners onto the skewed subject (document, plate, screen). Preview or apply to flatten to a rectangle.')}
          </p>
          <div className="fx-perspective-stage" ref={rootRef}>
            <img ref={imgRef} src={imageSrc} alt="" onLoad={syncSize} draggable={false} />
            {corners.length === 4 && (
              <svg className="fx-perspective-overlay" viewBox={`0 0 ${imgRef.current?.clientWidth || 1} ${imgRef.current?.clientHeight || 1}`}>
                <path d={quadPath(corners, scale)} className="fx-perspective-quad" />
                {corners.map(([x, y], i) => (
                  <g key={CORNER_LABELS[i]}>
                    <circle
                      cx={x * scale.x}
                      cy={y * scale.y}
                      r={9}
                      className="fx-perspective-handle"
                      onPointerDown={(e) => onPointerDown(i, e)}
                      onPointerMove={onPointerMove}
                      onPointerUp={onPointerUp}
                      onPointerCancel={onPointerUp}
                    />
                    <text x={x * scale.x + 12} y={y * scale.y + 4} className="fx-perspective-label">{CORNER_LABELS[i]}</text>
                  </g>
                ))}
              </svg>
            )}
          </div>
          <div className="fx-perspective-presets">
            <button type="button" className="fx-btn" disabled={disabled} onClick={() => resetCorners('inset')}>
              {t('perspective.reset_inset', 'Reset (inset)')}
            </button>
            <button type="button" className="fx-btn" disabled={disabled} onClick={() => resetCorners('full')}>
              {t('perspective.reset_full', 'Full frame')}
            </button>
          </div>
          <div className="fx-export-actions-row">
            <button
              type="button"
              className="fx-btn"
              disabled={disabled || !sessionId || previewing || corners.length < 4}
              onClick={runPreview}
            >
              {previewing ? t('perspective.previewing', 'Previewing…') : t('perspective.preview', 'Preview')}
            </button>
            <button
              type="button"
              className="fx-btn fx-btn-primary"
              disabled={disabled || !sessionId || applying || corners.length < 4}
              onClick={applyCorrection}
            >
              {applying ? t('perspective.applying', 'Applying…') : t('perspective.apply', 'Apply correction')}
            </button>
            <button type="button" className="fx-btn" disabled={disabled || !sessionId || applying} onClick={autoStraighten}>
              {t('perspective.auto_btn', 'Auto straighten')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
