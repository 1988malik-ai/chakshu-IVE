/** Default quadrilateral corners for perspective correction (TL, TR, BR, BL). */

export const CORNER_LABELS = ['TL', 'TR', 'BR', 'BL'];

export function defaultCorners(width, height, inset = 0.08) {
  const w = Math.max(1, width);
  const h = Math.max(1, height);
  const mx = w * inset;
  const my = h * inset;
  return [
    [mx, my],
    [w - mx, my],
    [w - mx, h - my],
    [mx, h - my],
  ];
}

export function fullFrameCorners(width, height) {
  const w = Math.max(1, width);
  const h = Math.max(1, height);
  return [
    [0, 0],
    [w - 1, 0],
    [w - 1, h - 1],
    [0, h - 1],
  ];
}

export function cornersToParams(corners) {
  return {
    src_corners: corners.map(([x, y]) => [Math.round(x * 100) / 100, Math.round(y * 100) / 100]),
  };
}

export function loadPerspectiveCorners(mediaKey) {
  if (!mediaKey) return null;
  try {
    const raw = localStorage.getItem(`chakshu.perspective.${mediaKey}`);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return null;
}

export function savePerspectiveCorners(mediaKey, corners) {
  if (!mediaKey) return;
  try {
    localStorage.setItem(`chakshu.perspective.${mediaKey}`, JSON.stringify(corners));
  } catch {
    /* ignore */
  }
}
