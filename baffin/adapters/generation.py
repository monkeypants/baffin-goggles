"""Generation of misses, serial or over a process pool (see :doc:`/lazy-build`).

The pool fans out the coarse per-asset ``AssetProcessor`` unit,
pinning libvips to one thread per worker to avoid CPU oversubscription.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

from baffin.adapters.processor import AssetJob, AssetProcessor, AssetResult


def _init_worker() -> None:
    os.environ["VIPS_CONCURRENCY"] = "1"


def generate(
    processor: AssetProcessor, jobs: list[AssetJob], *, workers: int
) -> list[AssetResult]:
    if workers <= 1 or len(jobs) <= 1:
        return [processor.process(job) for job in jobs]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
        return list(pool.map(processor.process, jobs))
