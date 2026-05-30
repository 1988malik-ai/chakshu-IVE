"""Multilingual UI strings and report generation."""

from __future__ import annotations

from pathlib import Path

LOCALES = ("en", "es", "fr", "de", "ja", "ko", "zh")

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "app.title": "Chakshu — Digital Media Examination",
        "menu.file": "File",
        "menu.edit": "Edit",
        "menu.view": "View",
        "menu.tools": "Tools",
        "menu.help": "Help",
        "action.open": "Open",
        "action.export": "Export",
        "action.batch": "Batch Convert",
        "action.undo": "Undo",
        "action.redo": "Redo",
        "action.bookmark": "Add Bookmark",
        "filter.browser": "Filter Browser",
        "license.activate": "Activate License",
        "license.machine_id": "Machine ID",
        "report.export_complete": "Export completed successfully",
        "report.batch_summary": "Batch conversion summary",
        "a11y.high_contrast": "High contrast mode",
        "a11y.color_blind": "Color blind mode",
    },
    "es": {
        "app.title": "AI-IVE — Mejora de Imagen y Video",
        "menu.file": "Archivo",
        "menu.edit": "Editar",
        "menu.view": "Ver",
        "menu.tools": "Herramientas",
        "menu.help": "Ayuda",
        "action.open": "Abrir",
        "action.export": "Exportar",
        "action.batch": "Conversión por lotes",
        "action.undo": "Deshacer",
        "action.redo": "Rehacer",
        "action.bookmark": "Añadir marcador",
        "filter.browser": "Navegador de filtros",
        "license.activate": "Activar licencia",
        "license.machine_id": "ID de máquina",
        "report.export_complete": "Exportación completada",
        "report.batch_summary": "Resumen de conversión por lotes",
        "a11y.high_contrast": "Modo alto contraste",
        "a11y.color_blind": "Modo daltónico",
    },
    "fr": {
        "app.title": "AI-IVE — Amélioration Image et Vidéo",
        "menu.file": "Fichier",
        "menu.edit": "Édition",
        "menu.view": "Affichage",
        "menu.tools": "Outils",
        "menu.help": "Aide",
        "action.open": "Ouvrir",
        "action.export": "Exporter",
        "action.batch": "Conversion par lot",
        "action.undo": "Annuler",
        "action.redo": "Rétablir",
        "action.bookmark": "Ajouter un signet",
        "filter.browser": "Navigateur de filtres",
        "license.activate": "Activer la licence",
        "license.machine_id": "ID machine",
        "report.export_complete": "Exportation terminée",
        "report.batch_summary": "Résumé de conversion par lot",
        "a11y.high_contrast": "Mode contraste élevé",
        "a11y.color_blind": "Mode daltonien",
    },
    "de": {
        "app.title": "AI-IVE — Bild- und Videoverbesserung",
        "menu.file": "Datei",
        "menu.edit": "Bearbeiten",
        "menu.view": "Ansicht",
        "menu.tools": "Werkzeuge",
        "menu.help": "Hilfe",
        "action.open": "Öffnen",
        "action.export": "Exportieren",
        "action.batch": "Stapelkonvertierung",
        "action.undo": "Rückgängig",
        "action.redo": "Wiederholen",
        "action.bookmark": "Lesezeichen hinzufügen",
        "filter.browser": "Filterbrowser",
        "license.activate": "Lizenz aktivieren",
        "license.machine_id": "Maschinen-ID",
        "report.export_complete": "Export abgeschlossen",
        "report.batch_summary": "Stapelkonvertierung Zusammenfassung",
        "a11y.high_contrast": "Hoher Kontrast",
        "a11y.color_blind": "Farbenblind-Modus",
    },
    "ja": {
        "app.title": "AI-IVE — 画像・動画エンハンス",
        "menu.file": "ファイル",
        "menu.edit": "編集",
        "menu.view": "表示",
        "menu.tools": "ツール",
        "menu.help": "ヘルプ",
        "action.open": "開く",
        "action.export": "エクスポート",
        "action.batch": "バッチ変換",
        "action.undo": "元に戻す",
        "action.redo": "やり直す",
        "action.bookmark": "ブックマーク追加",
        "filter.browser": "フィルタブラウザ",
        "license.activate": "ライセンス認証",
        "license.machine_id": "マシンID",
        "report.export_complete": "エクスポート完了",
        "report.batch_summary": "バッチ変換サマリー",
        "a11y.high_contrast": "ハイコントラスト",
        "a11y.color_blind": "色覚サポート",
    },
    "ko": {
        "app.title": "AI-IVE — 이미지 및 비디오 향상",
        "menu.file": "파일",
        "menu.edit": "편집",
        "menu.view": "보기",
        "menu.tools": "도구",
        "menu.help": "도움말",
        "action.open": "열기",
        "action.export": "보내기",
        "action.batch": "일괄 변환",
        "action.undo": "실행 취소",
        "action.redo": "다시 실행",
        "action.bookmark": "북마크 추가",
        "filter.browser": "필터 브라우저",
        "license.activate": "라이선스 활성화",
        "license.machine_id": "머신 ID",
        "report.export_complete": "보내기 완료",
        "report.batch_summary": "일괄 변환 요약",
        "a11y.high_contrast": "고대비 모드",
        "a11y.color_blind": "색맹 모드",
    },
    "zh": {
        "app.title": "AI-IVE — 图像与视频增强",
        "menu.file": "文件",
        "menu.edit": "编辑",
        "menu.view": "视图",
        "menu.tools": "工具",
        "menu.help": "帮助",
        "action.open": "打开",
        "action.export": "导出",
        "action.batch": "批量转换",
        "action.undo": "撤销",
        "action.redo": "重做",
        "action.bookmark": "添加书签",
        "filter.browser": "滤镜浏览器",
        "license.activate": "激活许可证",
        "license.machine_id": "机器 ID",
        "report.export_complete": "导出完成",
        "report.batch_summary": "批量转换摘要",
        "a11y.high_contrast": "高对比度",
        "a11y.color_blind": "色盲模式",
    },
}


class Translator:
    def __init__(self, locale: str = "en") -> None:
        self.locale = locale if locale in _STRINGS else "en"

    def tr(self, key: str, **kwargs: str) -> str:
        text = _STRINGS.get(self.locale, _STRINGS["en"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def set_locale(self, locale: str) -> None:
        if locale in _STRINGS:
            self.locale = locale

    def generate_report(self, title_key: str, lines: list[str], output: Path) -> None:
        title = self.tr(title_key)
        body = "\n".join([title, "=" * len(title), ""] + lines)
        output.write_text(body, encoding="utf-8")
