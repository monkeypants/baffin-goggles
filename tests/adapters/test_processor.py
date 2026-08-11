"""AssetProcessor: serial per-asset output and picklability of args/results."""

import pickle
from pathlib import Path

from PIL import Image

from baffin.adapters.processor import AssetJob, AssetProcessor
from baffin.application.config import GalleryConfig
from baffin.domain import DerivativeSpec, SourceRef

SPECS = (
    DerivativeSpec("thumb", 300, 80),
    DerivativeSpec("low", 800, 82),
    DerivativeSpec("med", 1600, 85),
)


def _job(tmp_path: Path) -> tuple[GalleryConfig, AssetJob]:
    photos = tmp_path / "photos"
    photos.mkdir(parents=True)
    src = photos / "a.jpg"
    Image.new("RGB", (1200, 900), (30, 120, 90)).save(src, "JPEG")
    stat = src.stat()
    ref = SourceRef(path=src, size=stat.st_size, mtime_ns=stat.st_mtime_ns)
    config = GalleryConfig(source=photos, output=tmp_path / "site")
    return config, AssetJob(ref=ref, specs=SPECS)


def test_serial_composite_produces_expected_derivatives(tmp_path: Path) -> None:
    config, job = _job(tmp_path)
    result = AssetProcessor.from_config(config).process(job)

    assert result.content_hash
    assert [g.derivative.spec_name for g in result.generated] == ["thumb", "low", "med"]
    for gen in result.generated:
        assert gen.derivative.rel_path.exists()
        assert gen.cache_key


def test_job_and_result_are_picklable(tmp_path: Path) -> None:
    config, job = _job(tmp_path)
    assert pickle.loads(pickle.dumps(job)) == job

    result = AssetProcessor.from_config(config).process(job)
    restored = pickle.loads(pickle.dumps(result))
    assert restored == result


def test_processor_is_reconstructable_in_a_worker(tmp_path: Path) -> None:
    config, job = _job(tmp_path)
    processor = AssetProcessor.from_config(config)
    revived = pickle.loads(pickle.dumps(processor))  # what the pool does
    assert len(revived.process(job).generated) == 3
