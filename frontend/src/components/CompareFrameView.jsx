import { useState } from 'react';
import GridOverlayLayer from './GridOverlayLayer';

function FrameWithGrid({ src, alt, className, wrapperClassName = '', gridOverlay }) {
  if (!src) return null;
  if (!gridOverlay?.enabled) {
    return <img src={src} alt={alt} className={className} />;
  }
  return (
    <div className={`fx-compare-frame-wrap ${wrapperClassName}`.trim()}>
      <img src={src} alt={alt} className={className} />
      <GridOverlayLayer preset={gridOverlay.preset} opacity={gridOverlay.opacity} />
    </div>
  );
}

/**
 * Frame preview with original vs enhanced comparison and optional dual-source preview.
 */
export default function CompareFrameView({
  originalSrc,
  enhancedSrc,
  flash = false,
  variant = 'lab',
  showSliderToggle = true,
  compareEnabled = true,
  isEnhanced = false,
  showOriginal = false,
  onShowOriginalChange,
  gridOverlay = null,
  onGridOverlayToggle,
  t = (k, d) => d,
}) {
  const [mode, setMode] = useState('split');
  const [sliderPos, setSliderPos] = useState(50);
  const [zoom, setZoom] = useState(1);

  const rootClass = `fx-compare fx-compare-${variant}${flash ? ' fx-compare-flash' : ''}`;

  if (!originalSrc && !enhancedSrc) {
    return (
      <div className={rootClass}>
        <div className="fx-compare-empty">
          <div className="fx-compare-empty-art" aria-hidden="true" />
          <div className="fx-compare-empty-copy">
            <strong>
              {compareEnabled
                ? t('compare.empty_title', 'Evidence workspace ready')
                : t('compare.frame_ready', 'Frame workspace ready')}
            </strong>
            <span>
              {compareEnabled
                ? t('compare.ingest', 'Ingest evidence to compare original vs enhanced')
                : t('compare.ingest_video', 'Ingest video and load a frame to preview')}
            </span>
          </div>
        </div>
      </div>
    );
  }

  const enhanced = enhancedSrc || originalSrc;
  const original = originalSrc || enhancedSrc;
  const identical = Boolean(originalSrc && enhancedSrc && originalSrc === enhancedSrc);
  const canCompare = compareEnabled && showOriginal && isEnhanced && Boolean(original) && Boolean(enhanced);
  const title = compareEnabled
    ? t('compare.title', 'Original vs Enhanced')
    : t('compare.frame_preview', 'Frame preview');

  return (
    <div className={rootClass}>
      <div className="fx-compare-toolbar">
        <span className="fx-compare-title">{title}</span>
        {compareEnabled && onShowOriginalChange && (
          <label className="fx-compare-toggle">
            <input
              type="checkbox"
              checked={showOriginal}
              onChange={(e) => onShowOriginalChange(e.target.checked)}
            />
            {t('compare.show_original', 'Show original')}
          </label>
        )}
        {canCompare && showSliderToggle && (
          <div className="fx-compare-modes">
            <button
              type="button"
              className={mode === 'split' ? 'active' : ''}
              onClick={() => setMode('split')}
            >
              {t('compare.side_by_side', 'Side by side')}
            </button>
            <button
              type="button"
              className={mode === 'slider' ? 'active' : ''}
              onClick={() => setMode('slider')}
            >
              {t('compare.slider', 'Slider')}
            </button>
          </div>
        )}
        {compareEnabled && showOriginal && !isEnhanced && (
          <span className="fx-compare-hint">
            {t('compare.no_enhancement', 'No enhancement yet — apply filters or AI tools')}
          </span>
        )}
        {compareEnabled && showOriginal && isEnhanced && identical && (
          <span className="fx-compare-hint">
            {t('compare.same_preview', 'Previews match — re-apply a filter or reset and try again')}
          </span>
        )}
        {onGridOverlayToggle && (
          <label className="fx-compare-toggle fx-grid-quick-toggle">
            <input
              type="checkbox"
              checked={Boolean(gridOverlay?.enabled)}
              onChange={(e) => onGridOverlayToggle(e.target.checked)}
            />
            {t('grid.show', 'Show grid overlay')}
          </label>
        )}
        <label className="fx-compare-zoom" title={t('compare.zoom_hint', 'Zoom image preview')}>
          <span>{t('compare.zoom', 'Zoom')}</span>
          <input
            type="range"
            min="1"
            max="3"
            step="0.25"
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            aria-label={t('compare.zoom', 'Zoom')}
          />
          <button type="button" onClick={() => setZoom(1)} disabled={zoom === 1}>
            {t('compare.zoom_reset', '1×')}
          </button>
        </label>
      </div>

      {canCompare && mode === 'slider' ? (
        <div className="fx-compare-slider-wrap" style={{ '--compare-zoom': zoom }}>
          <FrameWithGrid
            src={original}
            alt="Original"
            className="fx-compare-slider-base"
            wrapperClassName="fx-compare-slider-base-wrap"
            gridOverlay={gridOverlay}
          />
          <div className="fx-compare-slider-top" style={{ width: `${sliderPos}%` }}>
            <FrameWithGrid src={enhanced} alt="Enhanced" wrapperClassName="fx-compare-slider-top-wrap" gridOverlay={gridOverlay} />
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={sliderPos}
            className="fx-compare-slider-input"
            aria-label={t('compare.slider_aria', 'Compare original and enhanced')}
            onChange={(e) => setSliderPos(Number(e.target.value))}
          />
          <span className="fx-compare-label fx-compare-label-left">
            {t('compare.original', 'Original')}
          </span>
          <span className="fx-compare-label fx-compare-label-right">
            {t('compare.enhanced', 'Enhanced')}
          </span>
        </div>
      ) : canCompare ? (
        <div className="fx-compare-split" style={{ '--compare-zoom': zoom }}>
          <div className="fx-compare-pane">
            <span className="fx-compare-pane-label">{t('compare.original', 'Original')}</span>
            <FrameWithGrid src={original} alt="Original evidence frame" gridOverlay={gridOverlay} />
          </div>
          <div className="fx-compare-divider" aria-hidden />
          <div className="fx-compare-pane">
            <span className="fx-compare-pane-label fx-compare-pane-label-enh">
              {t('compare.enhanced', 'Enhanced')}
            </span>
            <FrameWithGrid
              src={enhanced}
              alt="Enhanced evidence frame"
              className={flash ? 'fx-workflow-flash' : ''}
              gridOverlay={gridOverlay}
            />
          </div>
        </div>
      ) : (
        <div className="fx-compare-single" style={{ '--compare-zoom': zoom }}>
          <span className="fx-compare-pane-label fx-compare-pane-label-enh">
            {compareEnabled ? t('compare.enhanced', 'Enhanced') : t('compare.current_frame', 'Current frame')}
          </span>
          <FrameWithGrid
            src={enhanced}
            alt="Evidence frame"
            className={flash ? 'fx-workflow-flash' : ''}
            gridOverlay={gridOverlay}
          />
        </div>
      )}
    </div>
  );
}
