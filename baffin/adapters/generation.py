"""Generation of misses, serial or over a process pool (see :doc:`/lazy-build`).

The pool fans out the coarse per-asset ``AssetProcessor`` unit,
pinning libvips to one thread per worker to avoid CPU oversubscription.
Each asset runs under the skip-and-report guard,
so one failed derivative is recorded and skipped and the run continues
(unless ``--strict``, which makes any failure fatal).
"""

from __future__ import annotations

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from baffin.adapters.processor import AssetJob, AssetProcessor, AssetResult
from baffin.application.reporting import BuildReport, per_asset

# Workers are started by spawn, never fork, on every platform.
#
# libvips initialises a thread pool on import, and forking a process that holds
# one deadlocks the child on locks whose owning threads did not survive the
# fork. The platform default differs: macOS spawns (since 3.8), Linux forks
# (through 3.13), so a pooled build works on one and hangs on the other.
# Spawn is also what makes _init_worker effective: under fork, libvips is
# already initialised in the parent, so setting VIPS_CONCURRENCY in the child
# is too late to pin it to one thread.
_SPAWN = multiprocessing.get_context("spawn")


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
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_init_worker, mp_context=_SPAWN
    ) as pool:
        futures = {pool.submit(processor.process, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            with per_asset(report, str(job.ref.path), strict=strict):
                # A worker's exception re-raises here, inside the guard, so the
                # pool path skips and reports exactly like the serial one.
                results.append(future.result())
    return results
