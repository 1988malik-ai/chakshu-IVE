import CompareFrameView from './CompareFrameView';

/**
 * Full-width original vs enhanced preview dock (Tools, Export, etc.).
 */
export default function ExamCompareDock({
  visible,
  originalSrc,
  enhancedSrc,
  filterChain,
  filterLabel,
  lastAction,
  pathLabel,
  autoOpenLab,
  onAutoOpenLabChange,
  onOpenLab,
  onIngest,
  hasPreview,
  mediaType = 'image',
  showOriginal = false,
  onShowOriginalChange,
  isEnhanced = false,
  gridOverlay = null,
  onGridOverlayToggle,
  t = (k, d) => d,
}) {
  if (!visible) return null;

  const isImage = mediaType === 'image';
  const canCompare = Boolean(originalSrc || enhancedSrc);

  return (
    <section className="fx-compare-dock" aria-label={canCompare ? 'Original versus enhanced preview' : 'Frame preview'}>
      <div className="fx-compare-dock-main">
        <CompareFrameView
          originalSrc={originalSrc}
          enhancedSrc={enhancedSrc}
          flash={Boolean(lastAction)}
          variant="dock"
          compareEnabled={canCompare}
          isEnhanced={isEnhanced}
          showOriginal={showOriginal}
          onShowOriginalChange={onShowOriginalChange}
          gridOverlay={gridOverlay}
          onGridOverlayToggle={onGridOverlayToggle}
          t={t}
        />
      </div>
      <aside className="fx-compare-dock-side">
        {lastAction && <p className="fx-compare-dock-action">{lastAction}</p>}
        {pathLabel && (
          <p className="fx-compare-dock-path" title={pathLabel}>{pathLabel}</p>
        )}
        {filterChain?.length > 0 ? (
          <div className="fx-compare-dock-pipeline">
            <span className="fx-compare-dock-pipeline-title">Pipeline</span>
            {filterChain.map((id, i) => (
              <span key={`${id}-${i}`} className="fx-workflow-chip" title={id}>
                {i + 1}. {filterLabel ? filterLabel(id) : id}
              </span>
            ))}
          </div>
        ) : (
          <p className="fx-compare-dock-hint">
            {isImage
              ? t('compare.dock_hint_image', 'Apply filters or AI tools to see enhancement vs original.')
              : t('compare.dock_hint_video', 'Load a frame at the playhead, then enable Show original to compare enhanced vs source. Use Video overlays panel for dual-file compare.')}
          </p>
        )}
        <label className="fx-workflow-option">
          <input
            type="checkbox"
            checked={autoOpenLab}
            onChange={(e) => onAutoOpenLabChange(e.target.checked)}
          />
          Open Examination Lab after apply
        </label>
        <div className="fx-compare-dock-btns">
          <button type="button" className="fx-btn fx-btn-primary" onClick={onOpenLab}>
            Examination Lab
          </button>
          {!hasPreview && (
            <button type="button" className="fx-btn" onClick={onIngest}>
              Ingest evidence
            </button>
          )}
        </div>
      </aside>
    </section>
  );
}
