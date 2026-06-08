import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';

const STORAGE_LOCALE = 'chakshu.locale';
const STORAGE_A11Y = 'chakshu.a11y';

const DEFAULT_A11Y = {
  highContrast: false,
  colorBlind: 'none',
  fontScale: 100,
  reduceMotion: false,
  focusVisible: true,
};

const LocaleContext = createContext(null);

function loadA11y() {
  try {
    const raw = localStorage.getItem(STORAGE_A11Y);
    if (!raw) return { ...DEFAULT_A11Y };
    return { ...DEFAULT_A11Y, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_A11Y };
  }
}

function applyA11yDom(a11y, theme) {
  const root = document.documentElement;
  root.dataset.highContrast = a11y.highContrast ? '1' : '0';
  root.dataset.colorBlind = a11y.colorBlind || 'none';
  root.dataset.reduceMotion = a11y.reduceMotion ? '1' : '0';
  root.dataset.focusVisible = a11y.focusVisible ? '1' : '0';
  root.style.setProperty('--fx-font-scale', String((a11y.fontScale || 100) / 100));
  if (theme) {
    root.style.setProperty('--fx-bg', theme.background);
    root.style.setProperty('--fx-text', theme.foreground);
    root.style.setProperty('--fx-accent', theme.accent);
    root.style.setProperty('--fx-panel', theme.panel);
    root.style.setProperty('--fx-border', theme.border);
    if (theme.warning) root.style.setProperty('--fx-warn', theme.warning);
    if (theme.success) root.style.setProperty('--fx-accent-2', theme.success);
  }
}

export function LocaleProvider({ children }) {
  const [locale, setLocaleState] = useState(() => {
    const saved = localStorage.getItem(STORAGE_LOCALE) || 'en';
    return ['en', 'hi', 'mr', 'gu'].includes(saved) ? saved : 'en';
  });
  const [strings, setStrings] = useState({});
  const [locales, setLocales] = useState([]);
  const [a11y, setA11yState] = useState(loadA11y);
  const [ready, setReady] = useState(false);

  const setLocale = useCallback((code) => {
    setLocaleState(code);
    localStorage.setItem(STORAGE_LOCALE, code);
  }, []);

  const setA11y = useCallback((patch) => {
    setA11yState((prev) => {
      const next = { ...prev, ...patch };
      localStorage.setItem(STORAGE_A11Y, JSON.stringify(next));
      return next;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [cat, bundle] = await Promise.all([
          api.i18nLocales(),
          api.i18nStrings(locale),
        ]);
        if (cancelled) return;
        setLocales(cat.locales || []);
        setStrings(bundle.strings || {});
        setReady(true);
      } catch {
        if (!cancelled) setReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, [locale]);

  useEffect(() => {
    document.documentElement.lang = locale === 'gu' ? 'gu' : locale === 'mr' ? 'mr' : locale === 'hi' ? 'hi' : locale;
    document.documentElement.dataset.locale = locale;
  }, [locale]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const theme = await api.a11yTheme(a11y.highContrast, a11y.colorBlind);
        if (!cancelled) applyA11yDom(a11y, theme);
      } catch {
        if (!cancelled) applyA11yDom(a11y, null);
      }
    })();
    return () => { cancelled = true; };
  }, [a11y]);

  const t = useCallback(
    (key, fallback) => strings[key] ?? fallback ?? key,
    [strings],
  );

  const value = useMemo(
    () => ({
      locale,
      setLocale,
      locales,
      strings,
      t,
      a11y,
      setA11y,
      ready,
    }),
    [locale, setLocale, locales, strings, t, a11y, setA11y, ready],
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error('useLocale must be used within LocaleProvider');
  return ctx;
}
