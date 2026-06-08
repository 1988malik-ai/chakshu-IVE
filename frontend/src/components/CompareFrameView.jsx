import { useState } from 'react';

/**
 * Frame preview with optional original vs enhanced comparison (images only).
 */
export default function CompareFrameView({
  originalSrc,
  enhancedSrc,
  flash = false,
  variant = 'lab',
  showSliderToggle = true,
  compareEnabled = true,
  showOriginal = false,
  onShowOriginalChange,
  t = (k, d) => d,
}) {
  const [mode, setMode] = useState('split');
  const [sliderPos, setSliderPos] = useState(50);

  const rootClass = `fx-compare fx-compare-${variant}${flash ? ' fx-compare-flash' : ''}`;

  if (!originalSrc && !enhancedSrc) {
    return (
      <div className={rootClass}>
        <div className="fx-compare-empty">
          {compareEnabled
            ? t('compare.ingest', 'Ingest evidence to compare original vs enhanced')
            : t('compare.ingest_video', 'Ingest video and load a frame to preview')}
        </div>
      </div>
    );
  }

  const enhanced = enhancedSrc || originalSrc;
  const original = originalSrc || enhancedSrc;
  const identical = original === enhanced;
  const canCompare = compareEnabled && showOriginal && !identical;
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
        {compareEnabled && showOriginal && identical && (
          <span className="fx-compare-hint">
            {t('compare.no_enhancement', 'No enhancement yet — apply filters or AI tools')}
          </span>
        )}
      </div>

      {canCompare && mode === 'slider' ? (
        <div className="fx-compare-slider-wrap">
          <img src={original} alt="Original" className="fx-compare-slider-base" />
          <div className="fx-compare-slider-top" style={{ width: `${sliderPos}%` }}>
            <img src={enhanced} alt="Enhanced" />
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
        <div className="fx-compare-split">
          <div className="fx-compare-pane">
            <span className="fx-compare-pane-label">{t('compare.original', 'Original')}</span>
            <img src={original} alt="Original evidence frame" />
          </div>
          <div className="fx-compare-divider" aria-hidden />
          <div className="fx-compare-pane">
            <span className="fx-compare-pane-label fx-compare-pane-label-enh">
              {t('compare.enhanced', 'Enhanced')}
            </span>
            <img src={enhanced} alt="Enhanced evidence frame" className={flash ? 'fx-workflow-flash' : ''} />
          </div>
        </div>
      ) : (
        <div className="fx-compare-single">
          <span className="fx-compare-pane-label fx-compare-pane-label-enh">
            {compareEnabled ? t('compare.enhanced', 'Enhanced') : t('compare.current_frame', 'Current frame')}
          </span>
          <img src={enhanced} alt="Evidence frame" className={flash ? 'fx-workflow-flash' : ''} />
        </div>
      )}
    </div>
  );
}
