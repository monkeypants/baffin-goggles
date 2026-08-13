Architecture
============

baffin is a clean-architecture application: a delivery-agnostic core with thin
adapters at the edge. Three views follow.

The dependency rule
-------------------

Dependencies point inward only: ``interface → adapters → application → domain``.
The domain imports nothing outward.
`import-linter <https://import-linter.readthedocs.io/>`_ enforces this on every
``make check``, so the diagram below is the contract itself.

.. uml::
   :caption: Layers: each depends only on those below.

   @startuml
   skinparam componentStyle rectangle
   skinparam shadowing false

   [interface\n(Typer CLI · reserved web)] as I
   [adapters\n(the imperative shell)] as A
   [application\n(functional core · ports · use cases)] as App
   [domain\n(frozen dataclasses · cache key)] as D

   I --> A
   A --> App
   App --> D

   note right of D
     Imports nothing outward.
   end note
   @enduml

Ports and their implementations
-------------------------------

The seams between core and shell are ``typing.Protocol`` ports in
:py:mod:`baffin.application.ports`. Each has a real adapter and an in-memory
fake; the core depends only on the Protocol, so the use cases test with no I/O.
The diagram traces the :py:class:`~baffin.application.ports.Thumbnailer` seam
through its :py:class:`~baffin.adapters.thumbnails.VipsThumbnailer` and
:py:class:`~baffin.adapters.thumbnails.PillowThumbnailer` adapters.

.. uml::
   :caption: The Thumbnailer port and its implementations.

   @startuml
   skinparam shadowing false

   interface Thumbnailer <<port>> {
     render(src, spec, dst, *, strip_gps, embed)
   }

   class VipsThumbnailer <<adapter>>
   class PillowThumbnailer <<adapter>>
   class FakeThumbnailer <<test double>>

   VipsThumbnailer ..|> Thumbnailer
   PillowThumbnailer ..|> Thumbnailer
   FakeThumbnailer ..|> Thumbnailer
   @enduml

The lazy build
--------------

The core plans; the shell generates. Hashing is memoised on ``stat`` (the
:py:class:`~baffin.application.ports.Hasher`), only cache misses run in a process
pool of :py:class:`~baffin.adapters.processor.AssetProcessor` units, results are
recorded through the :py:class:`~baffin.application.ports.DerivativeStore`, and
the HTML re-renders every build. Editing a template rewrites zero image bytes
(:doc:`lazy-build`).

.. uml::
   :caption: build: plan in the core, generate misses in the shell.

   @startuml
   skinparam shadowing false
   autonumber

   participant "build" as CLI
   participant Repository
   participant "Hasher\n(stat memo)" as Hasher
   participant "MetadataReader" as Reader
   participant "functional core\n(group/plan/diff)" as Core
   participant "process pool\n(AssetProcessor)" as Pool
   participant DerivativeStore as Store
   participant Renderer

   CLI -> Repository: discover()
   CLI -> Hasher: hash_file()  (memo hit if unchanged)
   CLI -> Reader: read() EXIF
   CLI -> Core: group_timeline / plan_derivatives / diff_plan
   Core --> CLI: BuildPlan (hits, misses)
   CLI -> Pool: generate misses only
   Pool -> Store: record(key, derivative)
   CLI -> Renderer: render()   (always; HTML is cheap)
   @enduml
