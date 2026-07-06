import { formatClock, formatTc } from './timecode';

export const TIMESTAMP_MODES = [
  { id: 'timecode', label: 'SMPTE (HH:MM:SS:FF)' },
  { id: 'clock', label: 'Clock (M:SS.mmm)' },
  { id: 'seconds', label: 'Seconds + frame #' },
  { id: 'custom', label: 'Custom text' },
  { id: 'iso', label: 'Wall clock (ISO)' },
];

export const TIMESTAMP_POSITIONS = [
  { id: 'bottom-right', label: 'Bottom right' },
  { id: 'bottom-left', label: 'Bottom left' },
  { id: 'top-right', label: 'Top right' },
  { id: 'top-left', label: 'Top left' },
];

export const TIMESTAMP_DEFAULTS = {
  enabled: true,
  mode: 'timecode',
  position: 'bottom-right',
  customText: '',
  includeFrameIndex: true,
};

export function loadTimestampSettings() {
  try {
    const raw = localStorage.getItem('chakshu.timestampEdit');
    if (raw) return { ...TIMESTAMP_DEFAULTS, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return { ...TIMESTAMP_DEFAULTS };
}

export function saveTimestampSettings(settings) {
  try {
    localStorage.setItem('chakshu.timestampEdit', JSON.stringify(settings));
  } catch {
    /* ignore */
  }
}

/**
 * Resolve display/burn-in timestamp string from settings and playhead context.
 */
export function resolveTimestampText(settings, context = {}) {
  const {
    seekTime = 0,
    fps = 30,
    frameIndex = 0,
    mediaType = 'image',
  } = context;

  if (!settings?.enabled) return '';

  switch (settings.mode) {
    case 'timecode':
      return mediaType === 'video'
        ? formatTc(seekTime, fps)
        : `IMG · ${settings.includeFrameIndex ? `#${frameIndex}` : formatTc(0, fps)}`;
    case 'clock':
      return mediaType === 'video' ? formatClock(seekTime) : `Frame ${frameIndex}`;
    case 'seconds': {
      const base = mediaType === 'video' ? `${seekTime.toFixed(3)}s` : 'still';
      return settings.includeFrameIndex ? `${base} · #${frameIndex}` : base;
    }
    case 'iso':
      return new Date().toISOString();
    case 'custom':
    default:
      return (settings.customText || '').trim();
  }
}

export function overlayTimestampPayload(sessionId, settings, context = {}, extra = {}) {
  const text = resolveTimestampText(settings, context);
  return {
    session_id: sessionId,
    timestamp_text: text,
    timestamp_position: settings.position || 'bottom-right',
    ...extra,
  };
}
