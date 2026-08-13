"""ffmpeg video processor (see :doc:`/lazy-build`):
poster frame + copied clip, no transcode.

Shells out to ffmpeg/ffprobe (must be on PATH).
The clip is stream-copied, and its metadata (GPS included) is dropped by default.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from baffin.application.errors import DerivativeFailed
from baffin.domain import Derivative, DerivativeSpec, SourceRef


class FfmpegVideo:
    def poster(self, src: SourceRef, spec: DerivativeSpec, dst: Path) -> Derivative:
        dst.parent.mkdir(parents=True, exist_ok=True)
        midpoint = self._duration(src.path) / 2
        self._run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{midpoint:.3f}",
                "-i",
                str(src.path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(dst),
            ],
            src.path,
        )
        with Image.open(dst) as poster:
            width, height = poster.size
        return Derivative(
            asset_hash=dst.stem,
            spec_name=spec.name,
            rel_path=dst,
            width=width,
            height=height,
        )

    def publish_clip(self, src: SourceRef, dst: Path, *, strip_gps: bool) -> Path:
        dst.parent.mkdir(parents=True, exist_ok=True)
        metadata = "-1" if strip_gps else "0"
        self._run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(src.path),
                "-map_metadata",
                metadata,
                "-c",
                "copy",
                str(dst),
            ],
            src.path,
        )
        return dst

    @staticmethod
    def _run(cmd: list[str], source: Path) -> None:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise DerivativeFailed(str(source)) from exc

    @staticmethod
    def _duration(path: Path) -> float:
        try:
            out = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "csv=p=0",
                    str(path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return float(out.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return 0.0


if TYPE_CHECKING:
    from baffin.application.ports import VideoProcessor

    _conforms: VideoProcessor = FfmpegVideo()
