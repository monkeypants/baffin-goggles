"""FfmpegVideo: poster extraction, clip copy, metadata strip, source safety."""

import hashlib
import subprocess
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from baffin.adapters.video import FfmpegVideo
from baffin.domain import DerivativeSpec, SourceRef

VideoFactory = Callable[..., Path]
POSTER = DerivativeSpec("poster", None, 90)


def _ref(path: Path) -> SourceRef:
    stat = path.stat()
    return SourceRef(path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def _format_tags(path: Path) -> str:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format_tags",
            "-of",
            "default",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout


def test_poster_is_a_real_jpeg(make_video: VideoFactory, tmp_path: Path) -> None:
    src = make_video()
    dst = tmp_path / "poster" / "hash.jpg"
    deriv = FfmpegVideo().poster(_ref(src), POSTER, dst)
    assert dst.exists()
    assert Image.open(dst).size == (deriv.width, deriv.height)
    assert (deriv.width, deriv.height) == (320, 240)


def test_clip_is_copied_and_original_untouched(
    make_video: VideoFactory, tmp_path: Path
) -> None:
    src = make_video()
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    dst = tmp_path / "video" / "hash.mp4"
    result = FfmpegVideo().publish_clip(_ref(src), dst, strip_gps=True)
    assert result == dst
    assert dst.exists() and dst.stat().st_size > 0
    assert hashlib.sha256(src.read_bytes()).hexdigest() == before


def test_strip_drops_container_metadata(
    make_video: VideoFactory, tmp_path: Path
) -> None:
    src = make_video(metadata={"comment": "secret location note"})
    assert "secret location note" in _format_tags(src)

    dst = tmp_path / "video" / "hash.mp4"
    FfmpegVideo().publish_clip(_ref(src), dst, strip_gps=True)
    assert "secret location note" not in _format_tags(dst)
