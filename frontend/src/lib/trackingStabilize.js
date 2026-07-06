/** Bbox helpers for object-tracking stabilization. */

export function bboxFromRect(p1, p2) {
  const x1 = Math.min(p1.x, p2.x);
  const y1 = Math.min(p1.y, p2.y);
  const x2 = Math.max(p1.x, p2.x);
  const y2 = Math.max(p1.y, p2.y);
  return [x1, y1, Math.max(8, x2 - x1), Math.max(8, y2 - y1)];
}

export function defaultCenterBBox(width, height, fraction = 0.35) {
  const w = Math.max(1, width);
  const h = Math.max(1, height);
  const bw = w * fraction;
  const bh = h * fraction;
  return [(w - bw) / 2, (h - bh) / 2, bw, bh];
}

export const TRACKER_TYPES = [
  { id: 'KCF', label: 'KCF (recommended)' },
  { id: 'CSRT', label: 'CSRT (slower, more accurate)' },
];

export const STABILIZE_MODES = [
  { id: 'full', label: 'Full frame (object locked, background moves)' },
  { id: 'crop', label: 'Crop follow (tight on object)' },
];

/** Unique export filename so runs do not overwrite each other. */
export function buildTrackingExportPath(
  outputDir,
  { seekTime = 0, mode = 'full', at = new Date() } = {},
) {
  const dir = (outputDir || '~/Desktop/chakshu-export').replace(/\/$/, '');
  const pad = (n) => String(n).padStart(2, '0');
  const stamp = [
    at.getFullYear(),
    pad(at.getMonth() + 1),
    pad(at.getDate()),
  ].join('') + `-${pad(at.getHours())}${pad(at.getMinutes())}${pad(at.getSeconds())}`;
  const tLabel = Number(seekTime).toFixed(2).replace('.', 'p');
  return `${dir}/tracking-stabilized_t${tLabel}s_${mode}_${stamp}.mp4`;
}

/** Step-by-step guide shown in Examination Lab. */
export const STABILIZE_TUTORIAL_STEPS = [
  {
    id: 'seek',
    title: 'Go to the start frame',
    detail: 'Use the scrub bar below the preview, then click Load Frame at Time so the image matches the moment you want to stabilize from.',
  },
  {
    id: 'box',
    title: 'Draw a box on the object',
    detail: 'Drag on the preview above to outline the person or object that should stay fixed. Tight boxes track more reliably than loose ones.',
  },
  {
    id: 'span',
    title: 'Choose how long to stabilize',
    detail: 'Track span defaults to 30 seconds from the playhead. Increase it for longer clips, or set an exact end time.',
  },
  {
    id: 'track',
    title: 'Track the object (required)',
    detail: 'Click Track object and wait for the frame count. Export is locked until this step succeeds.',
  },
  {
    id: 'export',
    title: 'Export stabilized video',
    detail: 'Click Export stabilized video. Each run gets a unique timestamped filename in your export folder.',
  },
];

export function stabilizeTutorialProgress({
  userDrewBox = false,
  trackResult = null,
  tracking = false,
  stabilizing = false,
} = {}) {
  if (stabilizing) {
    return {
      currentId: 'export',
      nextTitle: 'Export in progress',
      nextDetail: 'Encoding the stabilized clip. This usually takes under a minute for a 30-second span.',
    };
  }
  if (tracking) {
    return {
      currentId: 'track',
      nextTitle: 'Tracking in progress',
      nextDetail: 'Following your object frame by frame. Wait for the frame count to appear before exporting.',
    };
  }
  if (trackResult) {
    return {
      currentId: 'export',
      nextTitle: 'Export stabilized video',
      nextDetail: 'Tracking is complete. Click Export stabilized video — the button is now enabled.',
    };
  }
  if (userDrewBox) {
    return {
      currentId: 'track',
      nextTitle: 'Track before export',
      nextDetail: 'Click Track object first. Export stays disabled until tracking finishes successfully.',
    };
  }
  return {
    currentId: 'seek',
    nextTitle: 'Start here',
    nextDetail: 'Scrub to the first frame where the object is visible, click Load Frame at Time, then draw a box on the object.',
  };
}

export function stepStatus(stepId, { userDrewBox, trackResult, tracking, stabilizing }) {
  const order = ['seek', 'box', 'span', 'track', 'export'];
  const progress = stabilizeTutorialProgress({ userDrewBox, trackResult, tracking, stabilizing });
  const currentIdx = order.indexOf(progress.currentId);
  const stepIdx = order.indexOf(stepId);
  if (stepIdx < currentIdx) return 'done';
  if (stepIdx === currentIdx) return 'current';
  return 'upcoming';
}
