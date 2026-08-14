"""Generation of misses, serial or over a process pool (see :doc:`/lazy-build`).

The pool fans out the coarse per-asset ``AssetProcessor`` unit,
pinning libvips to one thread per worker to avoid CPU oversubscription.
Each asset runs under the skip-and-report guard,
so one failed derivative is recorded and skipped rather than sinking the whole run
(unless ``--strict``, which makes any failure fatal).
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from baffin.adapters.processor import AssetJob, AssetProcessor, AssetResult
from baffin.application.reporting import BuildReport, per_asset


def _init_worker() -> None:
    os.environ["VIPS_CONCURRENCY"] = "1"


def generate(
    processor: AssetProcessor,
    jobs: list[AssetJob],
    *,
    workers: int,
    report: BuildReport,
    strict: bool,
) -> list[AssetResult]:
    results: list[AssetResult] = []
    if workers <= 1 or len(jobs) <= 1:
        for job in jobs:
            with per_asset(report, str(job.ref.path), strict=strict):
                results.append(processor.process(job))
        return results
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
        futures = {pool.submit(processor.process, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            with per_asset(report, str(job.ref.path), strict=strict):
                # A worker's exception re-raises here, inside the guard, so the
                # pool path skips and reports exactly like the serial one.
                results.append(future.result())
    return results
