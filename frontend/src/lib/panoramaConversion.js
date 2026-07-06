/** Omnidirectional → panoramic conversion parameters. */

export const FILTER_ID = 'adv_omni_panorama';

export const SOURCE_TYPES = [
  { id: 'fisheye', label: 'Fisheye / omnidirectional lens' },
  { id: 'equirectangular', label: 'Equirectangular (360°)' },
];

export const OUTPUT_TYPES = [
  { id: 'equirectangular', label: 'Equirectangular panorama (2:1)' },
  { id: 'cylindrical', label: 'Cylindrical panorama' },
  { id: 'rectilinear', label: 'Rectilinear view (perspective)' },
];

export const FISHEYE_MODELS = [
  { id: 'equidistant', label: 'Equidistant' },
  { id: 'equisolid', label: 'Equisolid' },
  { id: 'stereographic', label: 'Stereographic' },
];

export const DEFAULT_PANORAMA_SETTINGS = {
  source_type: 'fisheye',
  output_type: 'equirectangular',
  fov_deg: 180,
  fisheye_model: 'equidistant',
  yaw_deg: 0,
  pitch_deg: 0,
  fov_h_deg: 90,
  fov_v_deg: 60,
};

export function panoramaParams(settings) {
  return {
    source_type: settings.source_type,
    output_type: settings.output_type,
    fov_deg: Number(settings.fov_deg),
    fisheye_model: settings.fisheye_model,
    yaw_deg: Number(settings.yaw_deg),
    pitch_deg: Number(settings.pitch_deg),
    fov_h_deg: Number(settings.fov_h_deg),
    fov_v_deg: Number(settings.fov_v_deg),
  };
}

export function buildPanoramaExportPath(outputDir, settings, at = new Date()) {
  const dir = (outputDir || '~/Desktop/chakshu-export').replace(/\/$/, '');
  const pad = (n) => String(n).padStart(2, '0');
  const stamp = [
    at.getFullYear(),
    pad(at.getMonth() + 1),
    pad(at.getDate()),
  ].join('') + `-${pad(at.getHours())}${pad(at.getMinutes())}${pad(at.getSeconds())}`;
  return `${dir}/panorama_${settings.source_type}_to_${settings.output_type}_${stamp}.jpg`;
}

export function showViewControls(settings) {
  return settings.output_type === 'rectilinear';
}

export function showFisheyeControls(settings) {
  return settings.source_type === 'fisheye';
}
