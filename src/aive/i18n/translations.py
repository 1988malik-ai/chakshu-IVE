"""Multilingual UI strings and report generation."""

from __future__ import annotations

from pathlib import Path

from aive.i18n.forensic_strings import LOCALE_NAMES, strings_for_locale

LOCALES = tuple(LOCALE_NAMES.keys())


class Translator:
    def __init__(self, locale: str = "en") -> None:
        self.locale = locale if locale in LOCALES else "en"
        self._strings = strings_for_locale(self.locale)

    def tr(self, key: str, **kwargs: str) -> str:
        text = self._strings.get(key) or strings_for_locale("en").get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text

    def set_locale(self, locale: str) -> None:
        if locale in LOCALES:
            self.locale = locale
            self._strings = strings_for_locale(locale)

    def all_strings(self) -> dict[str, str]:
        return dict(self._strings)

    def generate_report(self, title_key: str, lines: list[str], output: Path) -> None:
        title = self.tr(title_key)
        body = "\n".join([title, "=" * len(title), ""] + lines)
        output.write_text(body, encoding="utf-8")


def get_locale_catalog() -> list[dict[str, str]]:
    return [{"code": code, "name": name} for code, name in LOCALE_NAMES.items()]
