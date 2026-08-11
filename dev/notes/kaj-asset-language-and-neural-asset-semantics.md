# Kaj Asset Language and Neural Asset Semantics

**Status:** Architecture proposal  
**Language:** Kaj  
**Provisional proposal:** KIP-0017 — Asset Model and Neural Asset Semantics  
**Version:** 0.1  
**Date:** August 2026

---

## 1. Summary

Kaj should support not only ordinary computation and goal-directed agent work, but also **structured description, generation, transformation, and verification of digital assets**.

The core abstraction is:

```text
artifact format
+
Kaj semantic annotation
+
optional Kaj patch
+
optional selection
+
preservation constraints
→
artifact format
```

Examples:

```text
WAV + Kaj.Audio.Annotation + Kaj.Audio.Patch → WAV
PNG + Kaj.Image.Annotation + Kaj.Image.Patch → PNG
GLB + Kaj.Geometry.Annotation + Kaj.Geometry.Patch → GLB
USD + Kaj.Scene.Annotation + Kaj.Scene.Patch → USD
```

Kaj is the common language. Audio, image, video, geometry, scene, material, and animation semantics are provided by typed Kaj domain profiles rather than by separate standalone languages such as SoundSpec, ImageSpec, MeshSpec, or SceneSpec.

The artifact file itself is not the complete semantic state. A Kaj-aware creative system should preserve:

```text
binary artifact
+
semantic annotation
+
version lineage
+
edit operations
+
selections/masks
+
invariants
+
provenance
+
model/inference metadata
```

This enables controllable generation and, more importantly, reproducible iterative editing.

---

## 2. Motivation

Prompt-to-format generation is useful but weak as an editing system.

Typical systems expose:

```text
natural language
→
WAV / PNG / GLB / other output
```

Once the result is flattened into the output format, there may be no durable machine-readable representation of:

- what semantic entities exist,
- what properties they have,
- which regions correspond to which entities,
- which properties should change,
- which properties must remain unchanged,
- what the user selected,
- how the asset evolved,
- or what previous edits meant.

This creates a regeneration problem.

A user may say:

> Make the second impact heavier.

or:

> Make only the couch green.

or:

> Increase the thickness of the chair legs without changing the seat.

A prompt-only system can attempt these requests, but it has no universal representation of the requested delta and no standard way to express preservation.

Kaj should provide that representation.

---

## 3. Design Goal

Kaj should become a general semantic language for:

1. **describing an asset,**
2. **describing desired asset state,**
3. **selecting part of an asset,**
4. **expressing a transformation,**
5. **expressing what must not change,**
6. **recording provenance and confidence,**
7. **versioning semantic state,**
8. **lowering asset intent into model-specific or runtime-specific IR.**

Kaj should *not* make every modality concept part of Kaj Core.

Instead:

```text
Kaj Core
  |
  +-- common asset semantics
  |
  +-- typed domain profiles
        |
        +-- audio
        +-- image
        +-- video
        +-- geometry
        +-- scene
        +-- material
        +-- animation
        +-- simulation
```

---

## 4. Architectural Position

Kaj should support at least two major compiler targets.

```text
                         Kaj AST
                            |
                    semantic compiler
                            |
              +-------------+-------------+
              |                           |
              v                           v
           Task IR                    Asset IR
              |                           |
       agent/runtime            domain-specific lowering
                                          |
                     +----------+---------+----------+
                     |          |         |          |
                     v          v         v          v
                  Audio IR   Image IR  Geometry IR  Scene IR
                     |          |         |          |
                     v          v         v          v
                   model      model     model      runtime/model
```

Task IR describes executable work.

Asset IR describes typed semantic asset state and transformations.

A single Kaj program may use both.

Example:

```kaj
use web
use image

task create_campaign_asset {
    step research {
        ...
    }

    step produce {
        let reference = image.load("product.png")

        edit reference {
            select object "background"
            set style = "clean studio"
            preserve object "product"
        }
    }
}
```

---

## 5. Core Asset Abstractions

### 5.1 `Asset<T>`

Kaj should define a generic asset abstraction:

```text
Asset<T>
```

where `T` identifies the semantic asset domain.

Examples:

```text
Asset<Audio>
Asset<Image>
Asset<Video>
Asset<Geometry>
Asset<Scene>
Asset<Material>
Asset<Animation>
```

An asset may be backed by a concrete file or by an in-memory/runtime object.

Conceptually:

```text
Asset<T> {
    id
    domain
    format
    content_reference
    semantic_state
    version
    provenance
}
```

The binary bytes should not normally be embedded directly inside Kaj AST JSON. Kaj should reference them through typed asset references.

---

## 6. Format Is Separate From Semantic Domain

File formats are serialization/container formats, not languages.

Examples:

```text
Audio
  WAV
  FLAC
  MP3
  AAC

Image
  PNG
  JPEG
  HEIF
  TIFF

Geometry
  STL
  OBJ
  PLY
  GLB/glTF

Scene
  USD
  USDZ
  scene-native package formats
```

The same Kaj annotation should be usable across compatible formats.

Example:

```text
Kaj.Audio.Annotation
```

should not depend on whether the underlying audio is WAV or FLAC.

Likewise:

```text
Kaj.Image.Annotation
```

should not depend on PNG vs JPEG.

Format-specific features can be represented separately through format capabilities and metadata.

---

## 7. Asset State

A Kaj-aware asset project should distinguish the artifact from its semantic state.

```text
AssetState<T> =
    Artifact<T>
    +
    Annotation<T>
    +
    VersionMetadata
    +
    Provenance
```

Conceptually:

```kaj
let sound: Asset<Audio>
let state: AssetState<Audio>
```

The annotation is not merely UI metadata. It is intended to be usable by:

- neural models,
- deterministic editors,
- simulators,
- validators,
- search/indexing systems,
- version-control systems,
- agents,
- and humans.

---

## 8. Annotation

### 8.1 Definition

`Annotation<T>` is the typed semantic description of an asset.

Conceptually:

```text
Annotation<Audio>
Annotation<Image>
Annotation<Geometry>
Annotation<Scene>
```

Annotations may describe:

- entities,
- parts,
- events,
- materials,
- semantic roles,
- perceptual properties,
- geometry,
- time,
- spatial relationships,
- physical properties,
- hierarchy,
- motion,
- style,
- and other domain concepts.

### 8.2 Annotation Requirements

Annotations should be:

- typed,
- versioned,
- patchable,
- schema-validatable,
- deterministic in structure,
- extensible,
- model-oriented where appropriate,
- provenance-aware,
- and representable as canonical Kaj AST JSON.

---

## 9. Patch

### 9.1 Definition

Most iterative edits should be represented as a patch rather than as an entirely new annotation.

```text
AssetPatch<T>
```

A patch represents the semantic delta requested by the user or agent.

Example:

```kaj
edit impact {
    set weight = 0.90
    set timbre.brightness = 0.28
}
```

Conceptual normalized representation:

```json
{
  "kind": "asset_patch",
  "domain": "audio",
  "changes": [
    {
      "op": "set",
      "path": "events.impact_1.weight",
      "value": 0.90
    },
    {
      "op": "set",
      "path": "events.impact_1.timbre.brightness",
      "value": 0.28
    }
  ]
}
```

### 9.2 Patch Operations

Initial generic patch operations should include:

```text
set
increase
decrease
add
remove
replace
move
transform
insert
delete
preserve
```

Domain profiles may expose richer typed operations.

---

## 10. Selection

### 10.1 Generic Model

Kaj should define:

```text
Selection<T>
```

A selection identifies which portion of an asset a patch primarily targets.

Selections should have stable identity where possible so edits remain reproducible.

### 10.2 Audio Selections

Potential types:

```text
Audio.TimePoint
Audio.TimeRange
Audio.EventSelection
Audio.ChannelSelection
Audio.SourceSelection
```

Example:

```kaj
select time(1.25s..2.10s)
```

### 10.3 Image Selections

Potential types:

```text
Image.Mask
Image.Region
Image.BoundingBox
Image.ObjectSelection
Image.LayerSelection
```

Example:

```kaj
select object "couch"
```

### 10.4 Video Selections

Potential types:

```text
Video.Frame
Video.FrameRange
Video.TimeRange
Video.Track
Video.MaskTrack
Video.ObjectTrack
```

### 10.5 Geometry Selections

Potential types:

```text
Geometry.VertexSelection
Geometry.EdgeSelection
Geometry.FaceSelection
Geometry.SurfaceRegion
Geometry.PartSelection
Geometry.VolumeSelection
```

### 10.6 Scene Selections

Potential types:

```text
Scene.EntitySelection
Scene.HierarchySelection
Scene.Region3D
Scene.LayerSelection
Scene.CollectionSelection
```

---

## 11. Preservation and Invariants

Generative editing should treat **preservation as first-class semantics**.

The user usually wants:

```text
requested change
+
everything else preserved
```

Kaj already has concepts such as `invariant`, `require`, `expect`, and `verify`. Asset editing should reuse those semantics.

Example:

```kaj
edit chair {
    select parts where semantic_role == "leg"

    set thickness *= 1.15

    invariant {
        seat.geometry == previous.seat.geometry
        material == previous.material
        overall_height == previous.overall_height
    }
}
```

For an image:

```kaj
edit room {
    select object "couch"
    set color = rgb(22, 74, 47)

    preserve {
        lighting
        camera
        background
        geometry
        outside selection
    }
}
```

For audio:

```kaj
edit sound {
    select time(1.2s..2.0s)
    set impact.weight = 0.90
    preserve outside selection
}
```

Preservation constraints may be soft or hard.

Potential representation:

```text
PreservationConstraint {
    scope
    strength
    metric
    tolerance
}
```

---

## 12. Provenance and Confidence

Asset annotations often come from multiple sources:

```text
human annotation
existing metadata
signal analysis
computer vision
geometry analysis
model inference
synthetic transformation
imported source metadata
```

Kaj should permit provenance on semantic values.

Example:

```json
{
  "path": "events.impact_1.material",
  "value": "steel",
  "provenance": {
    "source": "human_metadata"
  }
}
```

Model-derived values may include confidence:

```json
{
  "path": "events.impact_1.weight",
  "value": 0.83,
  "provenance": {
    "source": "model_annotation",
    "model": "audio-annotator-v2",
    "confidence": 0.76
  }
}
```

Pseudo-labels should not be treated as unquestioned truth.

---

## 13. Versioning

A complete creative history should preserve:

```text
asset version
annotation version
patch
parent version
selection
invariants
user instruction
model version
adapter version
seed
inference settings
candidate outputs
accepted candidate
provenance
```

Conceptual graph:

```text
Asset v1 + Annotation v1
          |
          | Patch A
          v
Asset v2 + Annotation v2
          |
          | Patch B
          v
Asset v3 + Annotation v3
```

This is an asset state graph, not merely a chat transcript.

---

## 14. State-Transition Formulation

Kaj asset editing can be modeled generally as:

```text
state_t =
    artifact_t
    +
    annotation_t
```

The user action becomes:

```text
action_t =
    Kaj patch
    +
    selection
    +
    invariants
```

A model or deterministic runtime predicts/applies:

```text
state_t+1 =
    artifact_t+1
    +
    annotation_t+1
```

Thus:

```text
(state_t, action_t)
        |
        v
transition runtime/model
        |
        v
state_t+1
```

This generalizes beyond audio to images, video, geometry, scenes, animation, and other creative modalities.

---

## 15. Neural Asset IR

### 15.1 Why an IR Is Required

General Kaj AST should not be fed directly into every neural model.

A neural audio model does not need to understand:

```text
web.open
handoff
filesystem.read
while
task
```

Kaj therefore needs domain-specific lowering.

```text
Kaj AST
   |
   v
semantic validation
   |
   v
Kaj Asset IR
   |
   v
domain lowering
   |
   v
Audio Neural IR / Image Neural IR / Geometry Neural IR
```

### 15.2 Neural IR Properties

A Neural Asset IR should be:

- compact,
- typed,
- canonical,
- stable enough for training datasets,
- free of irrelevant general-purpose Kaj nodes,
- versioned independently,
- easy to encode into tensors/tokens,
- explicit about selection and preservation,
- explicit about operation mode.

Example audio IR:

```json
{
  "profile": "kaj.audio.neural.v1",
  "operation": "local_edit",
  "selection": {
    "type": "time_range",
    "start_seconds": 1.25,
    "end_seconds": 2.10
  },
  "events": [
    {
      "id": "impact_1",
      "properties": {
        "weight": 0.90
      },
      "timbre": {
        "brightness": 0.28
      }
    }
  ],
  "preservation": {
    "outside_selection": 1.0
  }
}
```

---

## 16. Domain Profiles

Kaj should define versioned domain profiles.

Initial candidates:

```text
kaj.audio.v1
kaj.image.v1
kaj.video.v1
kaj.geometry.v1
kaj.scene.v1
kaj.material.v1
kaj.animation.v1
```

A profile defines:

```text
name
version
types
semantic properties
operations
selection types
units
constraints
serialization
normalization
neural lowering rules
validation rules
optional provider operations
```

Domain vocabulary must not become Kaj Core syntax unless it proves broadly universal.

---

## 17. Kaj Audio Profile

SoundSpec should evolve into the ontology and Neural IR design for `kaj.audio`.

Potential types:

```text
Audio.Asset
Audio.Clip
Audio.Event
Audio.Source
Audio.Scene
Audio.TimePoint
Audio.TimeRange
Audio.Timbre
Audio.Dynamics
Audio.SpatialState
Audio.Automation
Audio.ReferencePolicy
```

Potential semantic dimensions include:

```text
event type
source
material
target material
weight
size
intensity
brightness
roughness
warmth
density
noisiness
tonalness
attack
sustain
decay
loudness
distance
position
width
motion
duration
```

Temporal automation should support:

```text
point
step
linear
ease-in
ease-out
envelope
keyframes
spline
```

Example:

```kaj
use audio

edit sound {
    select time(1.25s..2.10s)

    set event("impact_1").weight = 0.90
    set event("impact_1").timbre.brightness = 0.28

    preserve outside selection
}
```

---

## 18. Kaj Image Profile

Potential types:

```text
Image.Asset
Image.Object
Image.Mask
Image.Region
Image.Layer
Image.CameraState
Image.LightingState
Image.Appearance
Image.Style
```

Potential operations:

```text
recolor
replace
remove
insert
relight
restyle
move
resize
inpaint
outpaint
preserve
```

Example:

```kaj
use image

edit room {
    select object "couch"

    set appearance.color = rgb(22, 74, 47)

    preserve {
        object.geometry
        room.lighting
        room.camera
        outside selection
    }
}
```

---

## 19. Kaj Video Profile

Video combines image and temporal semantics.

Potential types:

```text
Video.Asset
Video.Track
Video.ObjectTrack
Video.FrameRange
Video.TimeRange
Video.MaskTrack
Video.Motion
Video.CameraMotion
```

Example:

```kaj
use video

edit clip {
    select track "car_1" during time(2.0s..5.5s)

    set appearance.color = "black"

    invariant {
        track.motion == previous.track.motion
        camera.motion == previous.camera.motion
    }
}
```

---

## 20. Kaj Geometry Profile

Potential types:

```text
Geometry.Mesh
Geometry.Part
Geometry.Vertex
Geometry.Edge
Geometry.Face
Geometry.Surface
Geometry.Volume
Geometry.Transform
Geometry.Topology
Geometry.MaterialBinding
```

Example:

```kaj
use geometry

edit chair {
    select parts where semantic_role == "leg"

    transform {
        scale x = 1.15
        scale z = 1.15
    }

    invariant {
        overall_height == previous.overall_height
        seat.geometry == previous.seat.geometry
    }
}
```

---

## 21. Kaj Scene Profile

A scene is richer than a mesh.

Potential types:

```text
Scene.Asset
Scene.Entity
Scene.Hierarchy
Scene.Transform
Scene.Camera
Scene.Light
Scene.MaterialBinding
Scene.AnimationBinding
Scene.PhysicsState
Scene.SemanticRole
Scene.Region3D
```

USD/USDZ should be treated as interchange/runtime formats rather than automatically becoming the canonical semantic source of truth.

Construct Studio or another host may maintain its own canonical scene document and export USD/GLB/etc.

---

## 22. Kaj Material Profile

Materials may be shared across image, 3D, and scene systems.

Potential types:

```text
Material.PBR
Material.Color
Material.Texture
Material.Normal
Material.Roughness
Material.Metallic
Material.Opacity
Material.Emission
```

Material semantics should be domain-independent where possible.

---

## 23. Kaj Animation Profile

Potential types:

```text
Animation.Track
Animation.Keyframe
Animation.Curve
Animation.Event
Animation.Constraint
Animation.RigBinding
```

Common temporal control abstractions may be shared with audio/video automation.

---

## 24. Asset Loading and References

Kaj should distinguish semantic references from raw file bytes.

Conceptual:

```kaj
let clip: Asset<Audio> = asset.open("impact.wav")
let mesh: Asset<Geometry> = asset.open("chair.glb")
```

The host resolves these references.

AST JSON should contain stable asset references such as:

```json
{
  "kind": "asset_reference",
  "asset_id": "asset_01JXYZ...",
  "domain": "audio",
  "format": "wav"
}
```

The compiler should not load arbitrary bytes during semantic validation.

---

## 25. Generate vs Edit

Generation should be treated as a special case of the same asset semantics.

### Generation

```text
no reference asset
+
target annotation
→
new asset
```

### Transformation

```text
reference asset
+
target annotation
→
new asset
```

### Local edit

```text
reference asset
+
patch
+
selection
+
preservation
→
new asset
```

### Identity

```text
reference asset
+
no-op patch
→
same asset
```

### Inpaint

```text
reference asset
+
missing/masked region
+
target annotation
→
completed asset
```

### Extend

```text
reference asset
+
extension boundary
+
target annotation
→
extended asset
```

---

## 26. Training Dataset Representation

Kaj AST JSON or domain Neural IR should be suitable as training annotations.

Audio example:

```text
sample_000143/
├── before.wav
├── before.kaj.json
├── action.kaj.json
├── after.wav
├── after.kaj.json
└── metadata.json
```

Image example:

```text
sample_192834/
├── before.png
├── before.kaj.json
├── action.kaj.json
├── mask.png
├── after.png
├── after.kaj.json
└── metadata.json
```

3D example:

```text
sample_058431/
├── before.glb
├── before.kaj.json
├── action.kaj.json
├── selection.bin
├── after.glb
├── after.kaj.json
└── metadata.json
```

The most valuable long-term dataset is transition data:

```text
(
  artifact_t,
  annotation_t,
  Kaj_patch,
  selection,
  invariants,
  artifact_t+1,
  annotation_t+1,
  user_preference
)
```

---

## 27. Deterministic and Neural Providers

Kaj asset semantics should not assume every operation requires a neural model.

For example:

```kaj
geometry.translate(mesh, x: 2cm)
```

may be deterministic.

```kaj
image.inpaint(selection, ...)
```

may be neural.

```kaj
audio.render(scene)
```

may be a physical/acoustic simulator.

The same Kaj domain can therefore have multiple providers:

```text
audio
  neural generator
  DSP processor
  acoustic simulator

geometry
  deterministic modeling engine
  neural geometry model

image
  deterministic compositing engine
  neural image model
```

The capability/provider boundary should preserve portability.

---

## 28. Relationship to Kaj Capabilities

Domain profiles may expose both pure semantic types and effectful operations.

Example:

```kaj
use audio
```

can load:

```text
types
annotation schemas
selection schemas
asset operations
render/generate/edit effects
provider contracts
Neural IR lowering
```

Kaj Core does not need to know how audio or geometry generation works.

---

## 29. Relationship to Construct Studio

Construct Studio already benefits from an operation-oriented architecture.

The intended direction should become:

```text
Hands / Gaze / Spatial UI
Mouse / Keyboard
AI commands
Kaj scripts
Robot adapters
        |
        v
Validated Kaj / Construct operations
        |
        v
Canonical Spatial Document
        |
        v
Geometry + Semantics + Navigation + State
        |
        v
RealityKit / simulation / export / neural generation
```

This avoids creating a separate Euclidia scripting language unless future requirements prove that Kaj cannot adequately serve the spatial domain.

---

## 30. Relationship to SoundSpec

SoundSpec should no longer be treated as an independent language.

Its useful work should be preserved as:

```text
Kaj Audio ontology
+
Kaj Audio Neural IR
+
Kaj Audio training/evaluation profile
```

The SoundSpec principles remain valid:

- typed semantics,
- temporal structure,
- patchability,
- preservation,
- reference adherence,
- provenance,
- iterative state transitions.

Kaj provides the common language and compiler architecture around them.

---

## 31. JSON and Human Source

Kaj retains its two canonical forms:

```text
Kaj source      human-facing
Kaj AST JSON    machine/model-facing
```

Asset annotations should therefore be representable both ways.

Human:

```kaj
edit sound {
    select time(1.25s..2.10s)
    set impact.weight = 0.90
    preserve outside selection
}
```

Machine:

```json
{
  "language": "kaj",
  "language_version": "0.x",
  "ast_schema_version": 1,
  "kind": "asset_edit",
  "domain": "audio",
  "selection": {
    "kind": "time_range",
    "start": {"value": 1.25, "unit": "seconds"},
    "end": {"value": 2.10, "unit": "seconds"}
  },
  "changes": [
    {
      "op": "set",
      "path": "impact.weight",
      "value": 0.90
    }
  ],
  "constraints": [
    {
      "kind": "preserve",
      "scope": "outside_selection"
    }
  ]
}
```

Exact AST shape should be standardized through a KIP and versioned schema.

---

## 32. Compiler Validation

Asset compilation should include:

```text
schema validity
domain resolution
type checking
unit checking
asset reference validation
selection validation
property/path validation
patch validation
constraint validation
capability/provider validation
Neural IR lowering
```

Example invalid program:

```kaj
let mesh: Asset<Geometry>

set mesh.timbre.brightness = 0.5
```

Compiler diagnostic:

```text
DOMAIN_PROPERTY_MISMATCH

`timbre.brightness` belongs to the Audio profile
but target asset is Geometry.
```

---

## 33. Compatibility and Versioning

Version separately:

```text
Kaj language
Kaj AST schema
Kaj Asset model
domain profiles
Neural IR profiles
provider contracts
adapter protocol
```

Example:

```text
Kaj language 0.2
AST v2
Asset model v1
kaj.audio.v1
kaj.geometry.v1
Kaj Neural IR v1
```

A model may support only a subset.

Example:

```text
Kaj Core 0.2
Asset Model v1
Audio Profile v1
Audio Neural IR v1
```

It does not need Web, Robot, Geometry, or other domains.

---

## 34. Initial Implementation Sequence

### Phase 1 — Asset Core

Implement:

```text
Asset<T>
AssetState<T>
Annotation<T>
AssetPatch<T>
Selection<T>
PreservationConstraint
Provenance
VersionMetadata
```

### Phase 2 — Audio Profile

Migrate SoundSpec concepts into:

```text
kaj.audio.v1
```

Implement:

```text
audio schema
ontology
temporal selections
events
timbre
dynamics
spatial semantics
automation
reference policy
preservation
Audio Neural IR
```

### Phase 3 — Adapter Protocol

Implement the Kaj model-adapter specification.

### Phase 4 — Image Profile

Build enough image semantics to test:

```text
object selection
mask editing
recolor
replacement
inpainting
preservation
```

### Phase 5 — Geometry Profile

Integrate with Construct Studio's typed operation system.

### Phase 6 — Shared Creative Semantics

Factor out broadly reusable concepts such as:

```text
time
curves
materials
transforms
selections
provenance
constraints
```

only after real domain implementations prove they are truly shared.

---

## 35. Non-Goals

This proposal does not require Kaj to:

- become a media container format,
- replace WAV/PNG/USD/GLB/etc.,
- define every possible audio/image/3D property in Core,
- make all neural models editable,
- mandate one neural architecture,
- mandate one tokenizer or embedding model,
- contain binary assets directly in AST JSON,
- or make neural generation deterministic.

Kaj defines **semantic intent and state**. Providers define execution.

---

## 36. Central Principle

> **Kaj describes structured asset state, requested deltas, selections, invariants, and provenance. Domain profiles define the vocabulary. Compilers lower that meaning into deterministic runtime operations or modality-specific neural conditioning representations.**

The general asset transition becomes:

```text
FORMAT_t
+
KAJ_STATE_t
+
KAJ_PATCH
+
SELECTION
+
INVARIANTS
        |
        v
deterministic or neural provider
        |
        v
FORMAT_t+1
+
KAJ_STATE_t+1
```

This is the generalization of SoundSpec into Kaj.
