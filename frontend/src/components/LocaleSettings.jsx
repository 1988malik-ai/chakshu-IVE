import { useLocale } from '../i18n/LocaleContext';

const COLOR_BLIND_KEYS = {
  none: 'settings.color_blind.none',
  protanopia: 'settings.color_blind.protanopia',
  deuteranopia: 'settings.color_blind.deuteranopia',
  tritanopia: 'settings.color_blind.tritanopia',
};

export default function LocaleSettings() {
  const { locale, setLocale, locales, t, a11y, setA11y } = useLocale();

  return (
    <div className="fx-panel fx-settings-panel">
      <div className="fx-panel-head">{t('nav.settings', 'Settings')}</div>
      <div className="fx-panel-body fx-settings-body">
        <label htmlFor="chakshu-locale">{t('settings.language', 'Language')}</label>
        <select
          id="chakshu-locale"
          value={locale}
          onChange={(e) => setLocale(e.target.value)}
          aria-label={t('settings.language', 'Language')}
        >
          {(locales.length ? locales : [{ code: 'en', name: 'English' }]).map((l) => (
            <option key={l.code} value={l.code}>{l.name}</option>
          ))}
        </select>

        <div className="fx-settings-section">
          <h3 className="fx-settings-section-title">{t('settings.accessibility', 'Accessibility')}</h3>

        <div className="fx-a11y-row">
          <input
            id="chakshu-hc"
            type="checkbox"
            checked={a11y.highContrast}
            onChange={(e) => setA11y({ highContrast: e.target.checked })}
          />
          <label htmlFor="chakshu-hc">{t('settings.high_contrast', 'High contrast')}</label>
        </div>

        <label htmlFor="chakshu-cb">{t('settings.color_blind', 'Color vision mode')}</label>
        <select
          id="chakshu-cb"
          value={a11y.colorBlind}
          onChange={(e) => setA11y({ colorBlind: e.target.value })}
        >
          {Object.entries(COLOR_BLIND_KEYS).map(([id, key]) => (
            <option key={id} value={id}>{t(key, id)}</option>
          ))}
        </select>

        <label htmlFor="chakshu-fs">{t('settings.font_scale', 'Text size')} ({a11y.fontScale}%)</label>
        <input
          id="chakshu-fs"
          type="range"
          min={100}
          max={150}
          step={5}
          value={a11y.fontScale}
          onChange={(e) => setA11y({ fontScale: Number(e.target.value) })}
        />

        <div className="fx-a11y-row">
          <input
            id="chakshu-rm"
            type="checkbox"
            checked={a11y.reduceMotion}
            onChange={(e) => setA11y({ reduceMotion: e.target.checked })}
          />
          <label htmlFor="chakshu-rm">{t('settings.reduce_motion', 'Reduce motion')}</label>
        </div>

        <div className="fx-a11y-row">
          <input
            id="chakshu-fv"
            type="checkbox"
            checked={a11y.focusVisible}
            onChange={(e) => setA11y({ focusVisible: e.target.checked })}
          />
          <label htmlFor="chakshu-fv">{t('settings.focus_visible', 'Enhanced focus outlines')}</label>
        </div>
        </div>
      </div>
    </div>
  );
}
