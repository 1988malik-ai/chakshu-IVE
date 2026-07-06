export const GRID_PRESETS = [
  { id: 'thirds', label: 'Rule of thirds', style: 'thirds', divisions: 3 },
  { id: 'center', label: 'Center cross', style: 'center' },
  { id: '4x4', label: '4 × 4', style: 'uniform', divisions: 4 },
  { id: '8x8', label: '8 × 8', style: 'uniform', divisions: 8 },
  { id: '16x16', label: '16 × 16', style: 'uniform', divisions: 16 },
  { id: '50px', label: '50 px (burn-in)', style: 'uniform', step: 50 },
];

export const GRID_OVERLAY_DEFAULTS = {
  enabled: false,
  preset: '8x8',
  opacity: 0.55,
  burnTimestamp: false,
};

export function loadGridOverlaySettings() {
  try {
    const raw = localStorage.getItem('chakshu.gridOverlay');
    if (raw) return { ...GRID_OVERLAY_DEFAULTS, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return { ...GRID_OVERLAY_DEFAULTS };
}

export function saveGridOverlaySettings(settings) {
  try {
    localStorage.setItem('chakshu.gridOverlay', JSON.stringify(settings));
  } catch {
    /* ignore */
  }
}

export function presetConfig(presetId) {
  return GRID_PRESETS.find((p) => p.id === presetId) || GRID_PRESETS.find((p) => p.id === '8x8');
}

export function overlayBurnPayload(presetId, timestampText = '', timestampPosition = 'bottom-right') {
  const preset = presetConfig(presetId);
  const body = { grid: true };
  if (timestampText) {
    body.timestamp_text = timestampText;
    body.timestamp_position = timestampPosition;
  }
  if (preset.style === 'thirds') {
    body.grid_style = 'thirds';
  } else if (preset.style === 'center') {
    body.grid_style = 'center';
  } else if (preset.divisions) {
    body.grid_style = 'uniform';
    body.grid_divisions = preset.divisions;
  } else if (preset.step) {
    body.grid_style = 'uniform';
    body.grid_step = preset.step;
  }
  return body;
}
