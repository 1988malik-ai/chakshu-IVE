"""Main application window."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from aive.accessibility.theme import ColorBlindMode, get_theme, stylesheet
from aive.ai.models import AIModelRegistry
from aive.analysis.stream import StreamAnalyzer
from aive.batch.queue import BatchQueue
from aive.bookmarks.store import BookmarkStore
from aive.export.exporter import ExportOptions, FrameRateMode, VideoExporter
from aive.filters.catalog import filter_count, list_filters
from aive.filters.engine import apply_filter
from aive.gpu.encode import detect_available_encoders
from aive.i18n.translations import LOCALES, Translator
from aive.license.protection import check_license, machine_fingerprint, activate_license
from aive.logging.operations import OperationLogger
from aive.media.loader import MediaLibrary, MediaType
from aive.subtitles.renderer import SubtitleParser
from aive.tracking.tracker import ObjectTracker
from aive.undo.stack import UndoStack


class PreviewLabel(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(640, 360)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAccessibleName("Video and image preview")
        self.setAccessibleDescription("Shows the current frame or image with applied filters")

    def show_frame(self, frame: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qimg).scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))


class MainWindow(QMainWindow):
    def __init__(
        self,
        locale: str = "en",
        high_contrast: bool = False,
        color_blind: ColorBlindMode = ColorBlindMode.NONE,
        enable_logging: bool = False,
    ) -> None:
        super().__init__()
        self.tr = Translator(locale)
        self.setWindowTitle(self.tr.tr("app.title"))
        self.setMinimumSize(1280, 800)

        theme = get_theme(high_contrast, color_blind)
        self.setStyleSheet(stylesheet(theme))

        self.library = MediaLibrary()
        self.bookmarks = BookmarkStore()
        self.undo_stack: UndoStack[np.ndarray] = UndoStack()
        self.analyzer = StreamAnalyzer()
        self.exporter = VideoExporter()
        self.batch = BatchQueue()
        self.tracker = ObjectTracker()
        self.ai = AIModelRegistry()
        self.logger = OperationLogger(enable_logging)
        self._current_frame: np.ndarray | None = None
        self._current_path: Path | None = None
        self._filter_chain: list[tuple[str, dict]] = []

        self._build_ui()
        self._build_menus()
        self._check_license_on_start()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel(self.tr.tr("menu.file"))
        self.folder_tree.setAccessibleName("Project folder tree")
        left_layout.addWidget(QLabel(self.tr.tr("menu.file")))
        left_layout.addWidget(self.folder_tree)

        self.filter_list = QListWidget()
        self.filter_list.setAccessibleName(self.tr.tr("filter.browser"))
        for f in list_filters():
            self.filter_list.addItem(f"{f.name} [{f.category.value}]")
        self.filter_list.itemDoubleClicked.connect(self._apply_selected_filter)
        left_layout.addWidget(QLabel(f"{self.tr.tr('filter.browser')} ({filter_count()})"))
        left_layout.addWidget(self.filter_list)
        splitter.addWidget(left)

        center = QTabWidget()
        self.preview = PreviewLabel()
        center.addTab(self.preview, "Preview")

        self.analysis_log = QTextEdit()
        self.analysis_log.setReadOnly(True)
        self.analysis_log.setAccessibleName("Stream analysis log")
        center.addTab(self.analysis_log, "Analysis")

        self.bookmark_list = QListWidget()
        self.bookmark_list.setAccessibleName("Bookmarks list")
        center.addTab(self.bookmark_list, "Bookmarks")
        splitter.addWidget(center)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.gpu_label = QLabel()
        encoders = detect_available_encoders()
        self.gpu_label.setText("GPU: " + ", ".join(e.name for e in encoders))
        right_layout.addWidget(self.gpu_label)

        self.frame_type_label = QLabel("I/P/B: —")
        self.frame_type_label.setAccessibleName("Frame type summary")
        right_layout.addWidget(self.frame_type_label)

        self.status_detail = QTextEdit()
        self.status_detail.setReadOnly(True)
        self.status_detail.setMaximumHeight(200)
        right_layout.addWidget(self.status_detail)
        splitter.addWidget(right)

        splitter.setSizes([280, 720, 240])
        layout.addWidget(splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(f"AI-IVE ready — {filter_count()} filters loaded")

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu(self.tr.tr("menu.file"))
        file_menu.addAction(self._action(self.tr.tr("action.open"), self._open_file, "Ctrl+O"))
        file_menu.addAction(self._action("Open Folder…", self._open_folder))
        file_menu.addAction(self._action(self.tr.tr("action.export"), self._export, "Ctrl+E"))
        file_menu.addAction(self._action(self.tr.tr("action.batch"), self._batch_convert))

        edit_menu = menubar.addMenu(self.tr.tr("menu.edit"))
        self._undo_action = self._action(self.tr.tr("action.undo"), self._undo, "Ctrl+Z")
        self._redo_action = self._action(self.tr.tr("action.redo"), self._redo, "Ctrl+Y")
        edit_menu.addAction(self._undo_action)
        edit_menu.addAction(self._redo_action)
        edit_menu.addAction(self._action(self.tr.tr("action.bookmark"), self._add_bookmark))

        tools_menu = menubar.addMenu(self.tr.tr("menu.tools"))
        tools_menu.addAction(self._action("Analyze Stream", self._analyze_stream))
        tools_menu.addAction(self._action("Import AI Model…", self._import_ai_model))
        tools_menu.addAction(self._action("Load Subtitles…", self._load_subtitles))

        view_menu = menubar.addMenu(self.tr.tr("menu.view"))
        for loc in LOCALES:
            view_menu.addAction(self._action(loc.upper(), lambda l=loc: self._set_locale(l)))

        help_menu = menubar.addMenu(self.tr.tr("menu.help"))
        help_menu.addAction(self._action(self.tr.tr("license.machine_id"), self._show_machine_id))
        help_menu.addAction(self._action(self.tr.tr("license.activate"), self._activate_license))

    def _action(self, text: str, slot, shortcut: str | None = None) -> QAction:
        act = QAction(text, self)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        return act

    def _check_license_on_start(self) -> None:
        status = check_license()
        if not status.valid:
            QMessageBox.warning(self, "License", status.message)

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr.tr("action.open"),
            "",
            "Media (*.mp4 *.mov *.avi *.mkv *.jpg *.jpeg *.png *.tiff *.bmp *.cr2 *.nef *.arw);;All (*)",
        )
        if not path:
            return
        self._load_path(Path(path))

    def _open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Open Folder")
        if not folder:
            return
        node = self.library.scan_folder(Path(folder))
        self._populate_tree(node)
        self.logger.log("OPEN_FOLDER", folder)

    def _populate_tree(self, node) -> None:
        item = QTreeWidgetItem([node.path.name])
        item.setData(0, Qt.ItemDataRole.UserRole, str(node.path))
        for f in node.files:
            child = QTreeWidgetItem([f.name])
            child.setData(0, Qt.ItemDataRole.UserRole, str(f))
            item.addChild(child)
        for child in node.children:
            item.addChild(self._populate_tree(child))
        if self.folder_tree.topLevelItemCount() == 0 or node.path.parent == node.path:
            self.folder_tree.addTopLevelItem(item)
        return item

    def _load_path(self, path: Path) -> None:
        item = self.library.add_file(path)
        if item is None:
            QMessageBox.warning(self, "Error", f"Unsupported file: {path}")
            return
        self._current_path = path
        if item.media_type in (MediaType.IMAGE, MediaType.RAW):
            frame = self.library.load_image(path)
            if frame is not None:
                self._set_frame(frame)
        elif item.media_type == MediaType.VIDEO and item.capture:
            ok, frame = item.capture.read()
            if ok:
                self._set_frame(frame)
        self.logger.log("OPEN", str(path))
        self.status.showMessage(f"Loaded: {path.name}")

    def _set_frame(self, frame: np.ndarray) -> None:
        self.undo_stack.push(frame, "edit")
        self._current_frame = frame
        self.preview.show_frame(frame)
        self._update_undo_actions()

    def _apply_selected_filter(self) -> None:
        if self._current_frame is None:
            return
        idx = self.filter_list.currentRow()
        filters = list_filters()
        if idx < 0 or idx >= len(filters):
            return
        spec = filters[idx]
        out = apply_filter(self._current_frame, spec.id)
        self._filter_chain.append((spec.id, {}))
        self._set_frame(out)
        self.logger.log("FILTER", spec.id)

    def _undo(self) -> None:
        state = self.undo_stack.undo()
        if state is not None:
            self._current_frame = state
            self.preview.show_frame(state)
        self._update_undo_actions()

    def _redo(self) -> None:
        state = self.undo_stack.redo()
        if state is not None:
            self._current_frame = state
            self.preview.show_frame(state)
        self._update_undo_actions()

    def _update_undo_actions(self) -> None:
        self._undo_action.setEnabled(self.undo_stack.can_undo)
        self._redo_action.setEnabled(self.undo_stack.can_redo)

    def _add_bookmark(self) -> None:
        if not self._current_path:
            return
        from aive.bookmarks.store import Bookmark

        bm = Bookmark.new_frame(str(self._current_path), 0, 0.0, label="User bookmark")
        self.bookmarks.add(bm)
        self.bookmark_list.addItem(f"{bm.label or bm.id} @ {bm.media_path}")
        self.logger.log("BOOKMARK", bm.id)

    def _analyze_stream(self) -> None:
        if not self._current_path or self.library.classify(self._current_path) != MediaType.VIDEO:
            QMessageBox.information(self, "Analysis", "Open a video file first.")
            return
        summary = self.analyzer.frame_type_summary(self._current_path)
        self.frame_type_label.setText(
            f"I: {summary.get('I', 0)}  P: {summary.get('P', 0)}  B: {summary.get('B', 0)}"
        )
        streams = self.analyzer.probe_streams(self._current_path)
        lines = [str(s) for s in streams]
        self.analysis_log.setPlainText("\n".join(lines))
        self.logger.log("ANALYZE", str(self._current_path))

    def _export(self) -> None:
        if not self._current_path:
            return
        out, _ = QFileDialog.getSaveFileName(self, self.tr.tr("action.export"), "", "MP4 (*.mp4)")
        if not out:
            return
        from aive.gpu.encode import select_encoder

        codec, vendor = select_encoder()
        opts = ExportOptions(
            output_path=Path(out),
            video_codec=codec,
            gpu_encoder=codec if "nvenc" in codec or "qsv" in codec or "amf" in codec else None,
            frame_rate_mode=FrameRateMode.CFR,
            use_stream_copy=True,
        )
        result = self.exporter.export(self._current_path, opts)
        if result.get("success"):
            QMessageBox.information(self, "Export", self.tr.tr("report.export_complete"))
        else:
            QMessageBox.warning(self, "Export", result.get("stderr", "Failed"))
        self.logger.log("EXPORT", out, success=result.get("success"))

    def _batch_convert(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Batch Input Folder")
        if not folder:
            return
        out_dir = QFileDialog.getExistingDirectory(self, "Batch Output Folder")
        if not out_dir:
            return

        def factory(inp: Path) -> ExportOptions:
            return ExportOptions(
                output_path=Path(out_dir) / (inp.stem + "_out.mp4"),
                use_stream_copy=True,
            )

        self.batch.add_folder(Path(folder), Path(out_dir), factory)
        results = self.batch.run_all()
        self.tr.generate_report(
            "report.batch_summary",
            [f"Done: {results['done']}", f"Failed: {results['failed']}"],
            Path(out_dir) / "batch_report.txt",
        )
        QMessageBox.information(
            self, "Batch", f"Done: {results['done']}, Failed: {results['failed']}"
        )

    def _import_ai_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import ONNX Model", "", "ONNX (*.onnx)")
        if path:
            info = self.ai.import_model(Path(path))
            QMessageBox.information(self, "AI", f"Imported model: {info.name}")

    def _load_subtitles(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Subtitles", "", "SRT (*.srt);;SMI (*.smi)")
        if path:
            cues = SubtitleParser.load(Path(path))
            self.status_detail.setPlainText(f"Loaded {len(cues)} subtitle cues from {path}")

    def _set_locale(self, locale: str) -> None:
        self.tr.set_locale(locale)
        self.setWindowTitle(self.tr.tr("app.title"))
        self.status.showMessage(f"Locale: {locale}")

    def _show_machine_id(self) -> None:
        QMessageBox.information(
            self, self.tr.tr("license.machine_id"), machine_fingerprint()
        )

    def _activate_license(self) -> None:
        from PyQt6.QtWidgets import QInputDialog

        key, ok = QInputDialog.getText(self, self.tr.tr("license.activate"), "License key:")
        if ok and key:
            status = activate_license(key.strip())
            QMessageBox.information(self, "License", status.message)

    def closeEvent(self, event) -> None:
        self.library.close_all()
        super().closeEvent(event)


def run_app(locale: str = "en", enable_logging: bool = False) -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AI-IVE")
    win = MainWindow(locale=locale, enable_logging=enable_logging)
    win.show()
    return app.exec()
