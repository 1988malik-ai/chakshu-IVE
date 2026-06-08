/** Playback transport — forward (HTML5) and reverse (forensic frame step). */

export default function ForensicVideoTransport({
  t = (k, d) => d,
  direction,
  speed,
  onSpeedChange,
  onPlayForward,
  onPlayReverse,
  onPause,
  onStepBack,
  onStepForward,
  onStepIframe,
  disabled = false,
  compact = false,
}) {
  const playingFwd = direction === 'forward';
  const playingRev = direction === 'reverse';

  return (
    <div className={`fx-playback-transport${compact ? ' fx-playback-compact' : ''}`}>
      <div className="fx-playback-buttons">
        <button type="button" className="fx-btn" disabled={disabled} onClick={onStepBack} title={t('playback.step_back', 'Previous frame')}>
          ◀
        </button>
        <button
          type="button"
          className={`fx-btn${playingFwd ? ' fx-btn-primary' : ''}`}
          disabled={disabled}
          onClick={playingFwd ? onPause : onPlayForward}
          title={t('playback.play_forward', 'Play forward')}
        >
          {playingFwd ? '⏸' : '▶'}
        </button>
        <button
          type="button"
          className={`fx-btn${playingRev ? ' fx-btn-primary' : ''}`}
          disabled={disabled}
          onClick={playingRev ? onPause : onPlayReverse}
          title={t('playback.play_reverse', 'Play reverse (frame-accurate)')}
        >
          {playingRev ? '⏸' : '◀◀'}
        </button>
        <button type="button" className="fx-btn" disabled={disabled} onClick={onStepForward} title={t('playback.step_forward', 'Next frame')}>
          ▶
        </button>
        {!compact && (
          <button type="button" className="fx-btn" disabled={disabled} onClick={onStepIframe} title={t('playback.next_iframe', 'Next I-frame')}>
            I▶
          </button>
        )}
        {(playingFwd || playingRev) && (
          <button type="button" className="fx-btn" disabled={disabled} onClick={onPause}>
            {t('playback.stop', 'Stop')}
          </button>
        )}
      </div>
      <label className="fx-playback-speed">
        <span>{t('playback.speed', 'Speed')}</span>
        <select
          value={speed}
          disabled={disabled}
          onChange={(e) => onSpeedChange(Number(e.target.value))}
          aria-label={t('playback.speed', 'Speed')}
        >
          <option value={0.25}>0.25×</option>
          <option value={0.5}>0.5×</option>
          <option value={1}>1×</option>
          <option value={1.5}>1.5×</option>
          <option value={2}>2×</option>
        </select>
      </label>
      {playingRev && (
        <span className="fx-playback-badge">{t('playback.reverse_active', 'Reverse playback')}</span>
      )}
    </div>
  );
}
