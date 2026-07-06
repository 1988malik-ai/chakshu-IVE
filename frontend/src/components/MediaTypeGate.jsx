/**
 * Renders children only when loaded evidence matches the required media type.
 */
export default function MediaTypeGate({
  requires = 'any',
  mediaType = 'image',
  hasEvidence = false,
  children,
}) {
  if (requires === 'any') {
    return hasEvidence ? children : null;
  }
  if (!hasEvidence) return null;
  if (requires === 'video' && mediaType !== 'video') return null;
  if (requires === 'image' && mediaType === 'video') return null;
  return children;
}

export function MediaTypeEmpty({
  requires = 'video',
  mediaType = 'image',
  hasEvidence = false,
  t = (k, d) => d,
}) {
  if (!hasEvidence) {
    return (
      <div className="fx-panel fx-media-empty">
        <div className="fx-panel-head">
          {requires === 'video'
            ? t('media.video_tools', 'Video tools')
            : t('media.image_tools', 'Image tools')}
        </div>
        <div className="fx-panel-body">
          <p>{t('media.ingest_first', 'Ingest evidence first to use these tools.')}</p>
        </div>
      </div>
    );
  }
  if (requires === 'video' && mediaType !== 'video') {
    return (
      <div className="fx-panel fx-media-empty">
        <div className="fx-panel-head">{t('media.video_tools', 'Video tools')}</div>
        <div className="fx-panel-body">
          <p>{t('media.need_video', 'These controls are for video evidence. Ingest or load a video file.')}</p>
        </div>
      </div>
    );
  }
  if (requires === 'image' && mediaType === 'video') {
    return (
      <div className="fx-panel fx-media-empty">
        <div className="fx-panel-head">{t('media.image_tools', 'Image tools')}</div>
        <div className="fx-panel-body">
          <p>{t('media.need_image', 'These controls are for still images. Ingest an image or load a frame from video.')}</p>
        </div>
      </div>
    );
  }
  return null;
}
