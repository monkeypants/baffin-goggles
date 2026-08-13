# The functional core

The core is pure functions over the domain: grouping, planning, cache diffing,
and URL building. No I/O, no mocks — plain dataclasses in, plain dataclasses out.
This is where most of the logic and most of the tests live.

## Chronological grouping

{py:func}`~baffin.application.grouping.group_timeline` buckets assets by
`captured_at`. The adaptive policy groups a short trip by day (with trip-day
labels) and a long archive by year then month; the 30-day span is the boundary.

```{literalinclude} ../tests/application/test_group_timeline.py
:pyobject: test_adaptive_boundary_30_days_is_still_by_day
```

```{literalinclude} ../tests/application/test_group_timeline.py
:pyobject: test_adaptive_long_archive_groups_by_year_month
```

## Planning and diffing

{py:func}`~baffin.application.planning.plan_derivatives` expands assets × specs
into content-addressed tiers; {py:func}`~baffin.application.planning.diff_plan`
splits that plan into HITs to skip and MISSes to generate, purely against an
immutable snapshot. Because the key is the content hash, a moved file is a hit:

```{literalinclude} ../tests/application/test_diff_plan.py
:pyobject: test_moved_source_with_same_bytes_is_a_hit
```

## Portable URLs

{py:func}`~baffin.application.urls.url_for` yields links relative to the current
page, so the same HTML works served at a domain root, under `/baffin/`, or from
`file://` — one string, every mount point:

```{literalinclude} ../tests/application/test_urls.py
:pyobject: test_relative_link_is_portable_across_mount_points
```
