import {
  TIMESTAMP_MODES,
  TIMESTAMP_POSITIONS,
  overlayTimestampPayload,
  resolveTimestampText,
  saveTimestampSettings,
} from '../lib/timestampEdit';

export default function TimestampEditorPanel({
  settings,
  onChange,
  onApply,
  applying = false,
  disabled = false,
  sessionId,
  seekTime = 0,
  fps = 30,
  frameIndex = 0,
  mediaType = 'image',
  t = (k, d) => d,
}) {
  const preview = resolveTimestampText(settings, { seekTime, fps, frameIndex, mediaType });

  const update = (patch) => {
    const next = { ...settings, ...patch };
    saveTimestampSettings(next);
    onChange(next);
  };

  return (
    <div className="fx-timestamp-panel">
      <div className="fx-timestamp-panel-head">
        <label className="fx-grid-toggle">
          <input
            type="checkbox"
            checked={settings.enabled}
            disabled={disabled}
            onChange={(e) => update({ enabled: e.target.checked })}
          />
          <span>{t('timestamp.show', 'Timestamp overlay')}</span>
        </label>
      </div>
      <div className="fx-timestamp-panel-body">
        <label className="fx-grid-field">
          <span>{t('timestamp.mode', 'Timestamp format')}</span>
          <select
            className="fx-input"
            value={settings.mode}
            disabled={disabled}
            onChange={(e) => update({ mode: e.target.value })}
          >
            {TIMESTAMP_MODES.map((m) => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </label>
        {settings.mode === 'custom' && (
          <label className="fx-grid-field">
            <span>{t('timestamp.custom', 'Custom text')}</span>
            <input
              className="fx-input"
              value={settings.customText}
              disabled={disabled}
              placeholder={t('timestamp.custom_ph', 'e.g. Case REF-001 · Examiner note')}
              onChange={(e) => update({ customText: e.target.value })}
            />
          </label>
        )}
        <label className="fx-grid-field">
          <span>{t('timestamp.position', 'Position on frame')}</span>
          <select
            className="fx-input"
            value={settings.position}
            disabled={disabled}
            onChange={(e) => update({ position: e.target.value })}
          >
            {TIMESTAMP_POSITIONS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </label>
        {(settings.mode === 'timecode' || settings.mode === 'seconds') && (
          <label className="fx-grid-toggle">
            <input
              type="checkbox"
              checked={settings.includeFrameIndex}
              disabled={disabled}
              onChange={(e) => update({ includeFrameIndex: e.target.checked })}
            />
            <span>{t('timestamp.include_frame', 'Include frame index on still images')}</span>
          </label>
        )}
        <div className="fx-timestamp-preview">
          <span className="fx-timestamp-preview-label">{t('timestamp.preview', 'Preview')}</span>
          <code>{preview || t('timestamp.empty', '(empty)')}</code>
        </div>
        <p className="fx-grid-hint">
          {t('timestamp.hint', 'Burns timestamp into the session frame. Use with grid overlay or alone for legal export frames.')}
        </p>
        <button
          type="button"
          className={`fx-btn fx-btn-primary${applying ? ' fx-btn-loading' : ''}`}
          disabled={disabled || !sessionId || applying || !preview}
          onClick={() => onApply(overlayTimestampPayload(sessionId, settings, { seekTime, fps, frameIndex, mediaType }))}
        >
          {applying ? t('timestamp.applying', 'Applying…') : t('timestamp.burn', 'Burn timestamp into frame')}
        </button>
      </div>
    </div>
  );
}
