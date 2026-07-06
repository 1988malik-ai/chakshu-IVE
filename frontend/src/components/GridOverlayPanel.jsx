import { GRID_PRESETS } from '../lib/gridOverlay';

/**
 * Grid overlay controls for Examination Lab (live preview + optional burn-in).
 */
export default function GridOverlayPanel({
  settings,
  onChange,
  onBurnIn,
  burning = false,
  disabled = false,
  sessionId,
  t = (k, d) => d,
}) {
  const { enabled, preset, opacity, burnTimestamp } = settings;

  return (
    <div className="fx-grid-panel">
      <div className="fx-grid-panel-head">
        <label className="fx-grid-toggle">
          <input
            type="checkbox"
            checked={enabled}
            disabled={disabled}
            onChange={(e) => onChange({ enabled: e.target.checked })}
          />
          <span>{t('grid.show', 'Show grid overlay')}</span>
        </label>
      </div>
      <div className="fx-grid-panel-body">
        <label className="fx-grid-field">
          <span>{t('grid.preset', 'Grid preset')}</span>
          <select
            className="fx-input"
            value={preset}
            disabled={disabled}
            onChange={(e) => onChange({ preset: e.target.value })}
          >
            {GRID_PRESETS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </label>
        <label className="fx-grid-field">
          <span>{t('grid.opacity', 'Opacity')}</span>
          <input
            type="range"
            min={0.15}
            max={1}
            step={0.05}
            value={opacity}
            disabled={disabled || !enabled}
            onChange={(e) => onChange({ opacity: Number(e.target.value) })}
          />
          <span className="fx-grid-opacity-val">{Math.round(opacity * 100)}%</span>
        </label>
        <p className="fx-grid-hint">
          {t('grid.hint_live', 'Live overlay is non-destructive. Burn-in writes grid lines into the session frame for export.')}
        </p>
        <label className="fx-grid-toggle fx-grid-burn-ts">
          <input
            type="checkbox"
            checked={burnTimestamp}
            disabled={disabled || !sessionId}
            onChange={(e) => onChange({ burnTimestamp: e.target.checked })}
          />
          <span>{t('grid.burn_timestamp', 'Include timestamp on burn-in')}</span>
        </label>
        <button
          type="button"
          className={`fx-btn fx-btn-primary${burning ? ' fx-btn-loading' : ''}`}
          disabled={disabled || !sessionId || burning}
          onClick={onBurnIn}
        >
          {burning ? t('grid.burning', 'Burning…') : t('grid.burn_in', 'Burn grid into frame')}
        </button>
      </div>
    </div>
  );
}
