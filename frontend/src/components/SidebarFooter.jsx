import { useLocale } from '../i18n/LocaleContext';

/** Minimal sidebar footer — language + case; full a11y lives on Settings page. */
export default function SidebarFooter({ caseLabel, caseId, examiner, onOpenSettings }) {
  const { locale, setLocale, locales, t } = useLocale();

  return (
    <footer className="fx-sidebar-foot">
      <div className="fx-sidebar-lang">
        <label htmlFor="chakshu-sidebar-locale">{t('settings.language', 'Language')}</label>
        <select
          id="chakshu-sidebar-locale"
          value={locale}
          onChange={(e) => setLocale(e.target.value)}
          aria-label={t('settings.language', 'Language')}
        >
          {(locales.length ? locales : [{ code: 'en', name: 'English' }]).map((l) => (
            <option key={l.code} value={l.code}>{l.name}</option>
          ))}
        </select>
      </div>
      <button type="button" className="fx-sidebar-settings-link" onClick={onOpenSettings}>
        {t('nav.settings', 'Settings')} — {t('settings.accessibility', 'Accessibility')}
      </button>
      <div className="fx-sidebar-case">
        <div className="case-id" title={caseId}>{caseLabel}</div>
        <div className="fx-sidebar-examiner">{examiner || 'Examiner'}</div>
      </div>
    </footer>
  );
}
