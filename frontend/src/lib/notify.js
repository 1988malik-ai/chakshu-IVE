/** Toast duration by severity (ms). */
export function toastDuration(type) {
  if (type === 'error') return 9000;
  if (type === 'warn') return 6500;
  return 4000;
}

export function formatApiError(err, fallback = 'Something went wrong') {
  const msg = String(err?.message || fallback).trim();
  if (!msg) return fallback;

  if (/^Session not found|Unknown session/i.test(msg)) {
    return 'Session expired. Refresh the page or ingest evidence again.';
  }
  if (/No frame loaded|No master frame/i.test(msg)) {
    return 'No frame loaded. Upload an image or seek to a video frame first.';
  }
  if (/Unknown filter/i.test(msg)) {
    return 'This filter is not available. Pick one marked FORENSIC in the list.';
  }
  if (/Could not be applied|not supported for this image/i.test(msg)) {
    return msg;
  }
  if (/video sequence|requires.*video|Session is not video/i.test(msg)) {
    return 'This filter needs video evidence. Load a video and seek to a frame first.';
  }
  if (/Unsupported media.*\.heic|Unsupported media.*\.heif/i.test(msg)) {
    return 'HEIC/HEIF is supported — restart Chakshu API so it loads pillow-heif, then re-ingest the file.';
  }
  if (/Could not decode HEIC|pillow-heif/i.test(msg)) {
    return 'HEIC/HEIF needs pillow-heif. Run: pip install pillow-heif in the project venv, then restart Chakshu.';
  }
  if (/opencv|OpenCV|imdecode|Could not decode/i.test(msg)) {
    return 'Image engine error. Try another file format or reinstall Chakshu.';
  }
  if (/Filter index out of range/i.test(msg)) {
    return 'That filter step was already removed from the pipeline.';
  }
  if (/NetworkError|Failed to fetch|Load failed/i.test(msg)) {
    return `Cannot reach Chakshu API. Restart the app, then check ~/.ai-ive/chakshu.log for details.`;
  }
  if (/timeout/i.test(msg)) {
    return 'Operation timed out. Try again with a smaller file or fewer filters.';
  }
  if (/OpenCV not installed|OpenCV required|opencv-python|opencv-contrib/i.test(msg)) {
    return 'Tracking needs OpenCV. In the project folder run: source .venv/bin/activate && pip install opencv-contrib-python-headless — then restart Chakshu.';
  }
  if (/Need at least 2 frames|Tracking failed|Stabilization failed/i.test(msg)) {
    return msg;
  }
  if (/Not found:|Could not open video|Video encode failed/i.test(msg)) {
    return msg;
  }
  return msg;
}
