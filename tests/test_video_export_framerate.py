from pathlib import Path

from aive.export.exporter import ExportOptions, FrameRateMode, VideoExporter
from aive.export.media_bundle import MediaExportBundle, _export_options


def test_cfr_export_command_forces_constant_frame_rate(tmp_path: Path):
    out = tmp_path / "cfr.mp4"
    opts = ExportOptions(
        output_path=out,
        video_codec="libx264",
        audio_codec="aac",
        use_stream_copy=False,
        frame_rate_mode=FrameRateMode.CFR,
        fps=25.0,
    )

    cmd = VideoExporter(ffmpeg="ffmpeg").build_command(tmp_path / "in.mp4", opts)

    assert "-fps_mode" in cmd
    assert cmd[cmd.index("-fps_mode") + 1] == "cfr"
    assert "-r" in cmd
    assert cmd[cmd.index("-r") + 1] == "25.0"


def test_vfr_export_command_preserves_variable_frame_timing(tmp_path: Path):
    out = tmp_path / "vfr.mp4"
    opts = ExportOptions(
        output_path=out,
        video_codec="libx264",
        audio_codec="aac",
        use_stream_copy=False,
        frame_rate_mode=FrameRateMode.VFR,
        fps=25.0,
    )

    cmd = VideoExporter(ffmpeg="ffmpeg").build_command(tmp_path / "in.mp4", opts)

    assert "-fps_mode" in cmd
    assert cmd[cmd.index("-fps_mode") + 1] == "vfr"
    assert "-r" not in cmd


def test_media_bundle_maps_framerate_mode_to_export_options(tmp_path: Path):
    bundle = MediaExportBundle(
        input_path=tmp_path / "in.mp4",
        output_dir=tmp_path,
        frame_rate_mode="vfr",
        fps=29.97,
        use_stream_copy=False,
        prefer_gpu=False,
    )

    opts = _export_options(bundle, tmp_path / "out.mp4")

    assert opts.frame_rate_mode == FrameRateMode.VFR
    assert opts.fps == 29.97
