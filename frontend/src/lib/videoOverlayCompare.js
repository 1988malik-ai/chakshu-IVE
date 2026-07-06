/** Video overlay + side-by-side comparison helpers. */

export const COMPARE_MODES = [
  { id: 'side_by_side', label: 'Side by side' },
  { id: 'pip', label: 'Picture-in-picture (inset)' },
];

export const PIP_POSITIONS = [
  { id: 'top-right', label: 'Top right' },
  { id: 'top-left', label: 'Top left' },
  { id: 'bottom-right', label: 'Bottom right' },
  { id: 'bottom-left', label: 'Bottom left' },
];

export const DEFAULT_COMPARE = {
  rightPath: '',
  rightTime: 0,
  syncTimes: true,
  mode: 'side_by_side',
  pipScale: 0.28,
  pipPosition: 'top-right',
};

export const DEFAULT_PIP = {
  insetPath: '',
  insetTime: 0,
  pipScale: 0.28,
  pipPosition: 'top-right',
};

export function compareRenderBody(sessionId, leftTime, rightTime, settings) {
  return {
    session_id: sessionId,
    left_time: leftTime,
    right_time: settings.syncTimes ? leftTime : rightTime,
    mode: settings.mode,
    pip_scale: Number(settings.pipScale),
    pip_position: settings.pipPosition,
  };
}

export function pipOverlayPayload(sessionId, settings) {
  return {
    session_id: sessionId,
    pip_path: settings.insetPath,
    pip_time_sec: Number(settings.insetTime),
    pip_scale: Number(settings.pipScale),
    pip_position: settings.pipPosition,
  };
}

/** Step-by-step overlay / compare guide in Examination Lab. */
export const OVERLAY_TUTORIAL_STEPS = [
  {
    id: 'ingest',
    title: 'Load primary video',
    detail: 'Top bar → Ingest Evidence → pick your main clip. Then click Examination Lab.',
  },
  {
    id: 'seek',
    title: 'Scrub to a moment',
    detail: 'Drag the timeline scrubber below the preview (e.g. 6 seconds). Left time updates automatically.',
  },
  {
    id: 'browse_compare',
    title: 'Add a second video',
    detail: 'In Side-by-side comparison → Right file path → Browse… → choose your second clip. Wait for the “Staged” toast.',
  },
  {
    id: 'preview_compare',
    title: 'Preview side-by-side',
    detail: 'Layout → Side by side → click Preview compare. Both clips should appear next to each other in the big preview.',
  },
  {
    id: 'browse_pip',
    title: 'Choose inset for PiP',
    detail: 'Scroll to Picture-in-picture → Inset file path → Browse… → pick the same or another file.',
  },
  {
    id: 'apply_pip',
    title: 'Apply PiP overlay',
    detail: 'Set inset time if needed → click Apply PiP overlay. A small inset appears in the corner of the main frame.',
  },
];

export function overlayTutorialProgress({
  leftPath = '',
  rightPath = '',
  lastPreview = null,
  insetPath = '',
  pipApplied = false,
  rendering = false,
  applyingPip = false,
  seekTime = 0,
} = {}) {
  if (applyingPip) {
    return {
      currentId: 'apply_pip',
      nextTitle: 'Applying PiP…',
      nextDetail: 'Compositing the inset onto your examination frame.',
    };
  }
  if (rendering) {
    return {
      currentId: 'preview_compare',
      nextTitle: 'Rendering compare…',
      nextDetail: 'Loading both sources and building the side-by-side preview.',
    };
  }
  if (pipApplied) {
    return {
      currentId: 'apply_pip',
      nextTitle: 'Tour complete',
      nextDetail: 'You tested side-by-side and PiP. Bookmark this frame or continue to Legal Export when ready.',
    };
  }
  if (insetPath) {
    return {
      currentId: 'apply_pip',
      nextTitle: 'Apply PiP overlay',
      nextDetail: 'Click Apply PiP overlay in the PiP section. Adjust scale and position first if you like.',
    };
  }
  if (lastPreview) {
    return {
      currentId: 'browse_pip',
      nextTitle: 'Set up picture-in-picture',
      nextDetail: 'Browse an inset file in the PiP section below, then apply it to the current frame.',
    };
  }
  if (rightPath) {
    return {
      currentId: 'preview_compare',
      nextTitle: 'Preview side-by-side',
      nextDetail: 'Keep Sync right time to playhead checked, choose Side by side, then click Preview compare.',
    };
  }
  if (leftPath && seekTime > 0.05) {
    return {
      currentId: 'browse_compare',
      nextTitle: 'Add the compare video',
      nextDetail: 'Click Browse… next to Right file path and choose your second video.',
    };
  }
  if (leftPath) {
    return {
      currentId: 'seek',
      nextTitle: 'Pick a time on the timeline',
      nextDetail: 'Scrub the timeline to the moment you want to compare, then add the second video.',
    };
  }
  return {
    currentId: 'ingest',
    nextTitle: 'Start here',
    nextDetail: 'Click Ingest Evidence (top right), load a video, then open Examination Lab.',
  };
}

const OVERLAY_STEP_ORDER = OVERLAY_TUTORIAL_STEPS.map((s) => s.id);

export function overlayStepStatus(stepId, ctx) {
  const progress = overlayTutorialProgress(ctx);
  const currentIdx = OVERLAY_STEP_ORDER.indexOf(progress.currentId);
  const stepIdx = OVERLAY_STEP_ORDER.indexOf(stepId);
  if (ctx.pipApplied && stepIdx <= currentIdx) return 'done';
  if (stepIdx < currentIdx) return 'done';
  if (stepIdx === currentIdx) return 'current';
  return 'upcoming';
}
