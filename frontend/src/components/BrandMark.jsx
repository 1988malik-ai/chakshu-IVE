import {
  LOGO_ALT,
  LOGO_MARK_PATH,
  LOGO_MARK_SVG,
  LOGO_PATH,
  HERO_PATH,
  PRODUCT_FULL,
  PRODUCT_MOTTO,
  PRODUCT_NAME,
  PRODUCT_TAGLINE,
  PRODUCT_VERSION,
} from '../brand';

/**
 * Brand mark — sidebar uses compact mark + wordmark; hero uses full artwork.
 * Falls back to SVG mark if PNG crops are not yet synced.
 */
export default function BrandMark({ variant = 'sidebar', className = '' }) {
  const cls = ['fx-brand-mark', `fx-brand-mark--${variant}`, className].filter(Boolean).join(' ');

  if (variant === 'sidebar') {
    return (
      <div className={cls}>
        <div className="fx-brand-mark__lockup">
          <img
            src={LOGO_MARK_PATH}
            alt=""
            className="fx-brand-mark__icon"
            draggable={false}
            onError={(e) => {
              e.currentTarget.onerror = null;
              e.currentTarget.src = LOGO_MARK_SVG;
            }}
          />
          <div className="fx-brand-mark__text">
            <span className="fx-brand-mark__name-row">
              <span className="fx-brand-mark__name">{PRODUCT_NAME}</span>
              <span className="fx-brand-mark__sub">Forensic</span>
            </span>
            <span className="fx-brand-mark__version">VER {PRODUCT_VERSION}</span>
            <span className="fx-brand-mark__motto-inline">{PRODUCT_MOTTO}</span>
          </div>
        </div>
      </div>
    );
  }

  if (variant === 'compact') {
    return (
      <div className={cls}>
        <img
          src={LOGO_MARK_PATH}
          alt={LOGO_ALT}
          className="fx-brand-mark__icon fx-brand-mark__icon--solo"
          draggable={false}
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = LOGO_MARK_SVG;
          }}
        />
      </div>
    );
  }

  return (
    <div className={cls}>
      <div className="fx-brand-hero-card">
        <img
          src={HERO_PATH}
          alt={LOGO_ALT}
          className="fx-brand-mark__hero"
          draggable={false}
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = LOGO_PATH;
          }}
        />
      </div>
      <div className="fx-brand-hero-copy">
        <h1 className="fx-brand-hero-title">
          <span className="fx-brand-hero-title-accent">{PRODUCT_NAME}</span>
          {' '}
          FORENSICS
        </h1>
        <p className="fx-brand-hero-tagline">{PRODUCT_TAGLINE}</p>
        <p className="fx-brand-mark__motto">{PRODUCT_MOTTO}</p>
      </div>
    </div>
  );
}
