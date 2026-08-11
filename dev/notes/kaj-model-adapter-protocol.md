# Kaj Model Adapter Protocol

**Status:** Architecture proposal  
**Language:** Kaj  
**Provisional proposal:** KIP-0018 — Kaj Model Adapter Protocol  
**Version:** 0.1  
**Date:** August 2026

---

## 1. Summary

Kaj should be adoptable by existing generative-model developers **without requiring full foundation-model retraining**.

The Kaj Model Adapter Protocol defines how a model provider can progressively support:

```text
Kaj annotation → format
```

and, when the underlying architecture permits:

```text
format + Kaj annotation → format
```

and ultimately:

```text
format
+
Kaj patch
+
selection
+
preservation constraints
→
edited format
```

The protocol deliberately separates:

1. **understanding Kaj semantics**, from
2. **accepting a reference artifact**, from
3. **performing localized artifact editing**.

Kaj alone cannot give a text-to-format model a reference-input path that its architecture does not have.

However, Kaj support should usually be addable through **prompt translators, small conditioning adapters, projection modules, LoRA-style adaptation, reference encoders, or other lightweight integration layers**, rather than by training a new foundation model from zero.

---

## 2. Goals

The adapter protocol should make Kaj:

- easy to adopt,
- incremental,
- model-architecture-neutral,
- modality-neutral,
- testable,
- versioned,
- open,
- efficient,
- compatible with frozen foundation models,
- and useful even for text-only generative models.

A provider should be able to add partial Kaj support first and improve over time.

---

## 3. Non-Goals

The protocol does not require:

- full foundation-model retraining,
- one universal neural architecture,
- one tokenizer,
- one latent space,
- one diffusion/flow/autoregressive design,
- one vendor runtime,
- full format-to-format support,
- localized editing for every model,
- or native understanding of arbitrary general-purpose Kaj AST.

---

## 4. Core Separation

There are three distinct problems.

### Problem A — Structured Semantic Conditioning

```text
Kaj
→
generated artifact
```

A text-to-format model may already know the underlying concepts semantically. The integration problem is how to map structured Kaj meaning into the conditioning space it already uses.

### Problem B — Reference Conditioning

```text
reference artifact
+
Kaj
→
new artifact
```

This requires some architectural path through which the generator can receive information about the reference artifact.

### Problem C — Localized Editing

```text
reference artifact
+
Kaj patch
+
selection
+
preservation
→
edited artifact
```

This additionally requires the model or surrounding pipeline to understand edit locality and preservation.

Kaj support should not pretend these three capabilities are equivalent.

---

## 5. Architecture

```text
                     Kaj AST
                        |
                        v
                   Kaj Compiler
                        |
                        v
                 Kaj Neural IR
                        |
             +----------+----------+
             |                     |
             v                     v
        Kaj Adapter          Provider Translator
             |                     |
             |                native prompt/API
             |                     |
             +----------+----------+
                        |
                        v
                   Base Model
                        |
                        v
                      Asset
```

Optional reference support:

```text
Reference Asset
      |
      v
Reference Encoder
      |
      v
Reference Adapter -----------+
                             |
Kaj Neural IR                |
      |                      |
      v                      |
Kaj Adapter -----------------+----> Base Model
                             |
Selection Adapter -----------+
```

---

## 6. Kaj Neural IR

Existing models should not be required to parse arbitrary Kaj.

They should consume a compact, normalized, versioned representation produced by the Kaj compiler.

Example:

```json
{
  "profile": "kaj.audio.neural.v1",
  "operation": "local_edit",
  "selection": {
    "type": "time_range",
    "start_seconds": 1.25,
    "end_seconds": 2.10
  },
  "semantic_delta": {
    "event": "impact_1",
    "weight": 0.90,
    "brightness": 0.28
  },
  "preservation": {
    "outside_selection": 1.0
  }
}
```

The IR should contain only concepts relevant to the modality/profile.

An audio model should not need to understand:

```text
web.open
robot.move_to
ask
handoff
filesystem.read
```

---

## 7. Compatibility Levels

Kaj should define a progressive compatibility ladder.

---

## 7.1 Level 0 — Kaj-Translated

**No neural changes required.**

```text
Kaj
 |
 v
Kaj compiler
 |
 v
provider translator
 |
 v
provider-native text prompt / parameters
 |
 v
existing model
```

Example:

Kaj:

```kaj
audio {
    event impact {
        material = steel
        target_material = concrete
        weight = 0.90
        brightness = 0.25
    }
}
```

Translator output:

```text
A very heavy steel impact on concrete with a dark,
low-brightness timbre and strong transient.
```

Advantages:

- immediate compatibility,
- zero weight changes,
- works with closed APIs,
- useful for semantic-state persistence.

Limitations:

- lossy,
- provider-specific,
- weaker precision,
- unsupported concepts may be approximated or rejected,
- true editing is unavailable if provider lacks reference input.

Certification name:

```text
Kaj-Translated
```

---

## 7.2 Level 1 — Kaj-Conditioned

The model receives Kaj semantics through a dedicated conditioning path.

```text
Kaj Neural IR
     |
     v
Kaj Encoder
     |
     v
Kaj Adapter
     |
     +-------------------+
                         |
Text Encoder ------------+----> frozen or mostly frozen generator
```

Typical implementation choices may include:

- learned projection,
- cross-attention adapter,
- prefix/prompt embeddings,
- side network,
- LoRA modules,
- feature modulation,
- control tokens,
- conditioning vectors.

The foundation generator may remain frozen.

Certification name:

```text
Kaj-Conditioned
```

Required behavior:

```text
Kaj annotation
→
artifact
```

Native structured conditioning should outperform or be measurably more faithful than the Level-0 text translation baseline on at least some Kaj conformance tasks.

---

## 7.3 Level 2 — Kaj-Referenced

The model supports a reference artifact.

```text
reference artifact
      |
      v
Reference Encoder
      |
      v
Reference Adapter -----------+
                             |
Kaj Adapter -----------------+----> generator
```

Required behavior:

```text
reference artifact
+
Kaj target state
→
new artifact
```

Examples:

```text
WAV + Kaj.Audio → WAV
PNG + Kaj.Image → PNG
GLB + Kaj.Geometry → GLB
```

This level does not yet require reliable localized edits.

Certification name:

```text
Kaj-Referenced
```

---

## 7.4 Level 3 — Kaj-Editable

The system additionally supports:

```text
reference
+
Kaj patch
+
selection
+
preservation constraints
→
edited result
```

Architecture:

```text
Reference Asset ---> Reference Adapter -----+
                                             |
Kaj Patch ---------> Kaj Adapter -----------+----> Generator
                                             |
Selection ---------> Selection Adapter -----+
                                             |
Preservation ------> constraint path -------+
```

The model must demonstrate edit locality and preservation behavior.

Certification name:

```text
Kaj-Editable
```

---

## 7.5 Optional Level 4 — Kaj-Stateful

A Kaj-Stateful system can consume and produce semantic asset state alongside the artifact.

```text
artifact_t
+
KajState_t
+
KajPatch_t
→
artifact_t+1
+
KajState_t+1
```

This is especially useful for persistent creative systems.

Certification name:

```text
Kaj-Stateful
```

---

## 8. Why the Ladder Matters

A model should not be forced to jump from:

```text
text → WAV
```

to:

```text
WAV + structured patch + mask + preservation → WAV
```

in one integration.

A provider can evolve:

```text
text model
   |
   v
Kaj-Translated
   |
   v
Kaj-Conditioned
   |
   v
Kaj-Referenced
   |
   v
Kaj-Editable
   |
   v
Kaj-Stateful
```

This makes Kaj adoptable by existing APIs as well as research models.

---

## 9. Minimal Provider Interface

A conceptual provider interface:

```python
class KajModelProvider:
    def capabilities(self) -> KajModelCapabilities:
        ...

    def compile_provider_request(
        self,
        ir: KajNeuralIR
    ) -> ProviderRequest:
        ...

    def generate(
        self,
        request: ProviderRequest,
        reference=None,
        selection=None
    ) -> ProviderResult:
        ...
```

Native Kaj-conditioned models may instead expose:

```python
class KajConditionedModel:
    def encode_kaj(
        self,
        ir: KajNeuralIR
    ) -> KajConditioning:
        ...

    def generate(
        self,
        kaj_condition: KajConditioning,
        reference_condition=None,
        selection_condition=None
    ):
        ...
```

Exact APIs are illustrative.

The specification should define behavior and serialization, not mandate Python.

---

## 10. Capability Manifest

Every Kaj-integrated model should expose a machine-readable capability manifest.

Example:

```json
{
  "kaj_model_protocol": "1.0",
  "provider": "example-audio-lab",
  "model": "example-audio-v3",
  "domains": {
    "audio": {
      "profile": "kaj.audio.v1",
      "neural_ir": "kaj.audio.neural.v1",
      "compatibility_level": "kaj_editable",
      "operations": [
        "generate",
        "transform",
        "local_edit",
        "inpaint",
        "extend"
      ],
      "selections": [
        "time_range",
        "event"
      ],
      "preservation": [
        "outside_selection"
      ]
    }
  }
}
```

Kaj runtimes should use this manifest during capability resolution.

---

## 11. Unsupported Semantics

Providers must never silently pretend full support for unsupported Kaj concepts.

A provider may return:

```json
{
  "code": "KAJ_UNSUPPORTED_PROPERTY",
  "path": "events.impact_1.timbre.hollowness",
  "profile": "kaj.audio.v1"
}
```

or:

```json
{
  "code": "KAJ_UNSUPPORTED_OPERATION",
  "operation": "local_edit"
}
```

A Level-0 translator may optionally approximate a property only when the manifest declares approximation behavior.

Example:

```json
{
  "property": "audio.weight",
  "support": "approximate",
  "lowering": "text_prompt"
}
```

---

## 12. Frozen-Model Integration Strategy

The preferred initial strategy for many providers should be:

```text
existing pretrained generator
        |
        | frozen
        v
     unchanged

new trainable components:
    Kaj encoder
    projection
    cross-attention/conditioning adapter
```

This teaches a small module how Kaj semantics map into concepts already represented by the model.

The provider is not relearning how to generate the modality from zero.

---

## 13. Kaj Encoder

### 13.1 Role

The Kaj Encoder converts canonical Neural IR into model-consumable semantic features.

```text
Kaj Neural IR
    |
    v
Kaj Encoder
    |
    v
semantic embeddings
```

The encoder may use:

- structured field embeddings,
- small transformer encoders,
- graph encoders,
- learned domain vocabularies,
- numeric/unit encoders,
- temporal encoders,
- spatial encoders.

### 13.2 Provider-Specific vs Universal

Initial implementations may use provider-specific Kaj encoders.

Long-term, Kaj may define a **universal Kaj semantic encoder**:

```text
Kaj Neural IR
      |
      v
Universal Kaj Encoder
      |
      v
Kaj Embedding
      |
  +---+---+----------------+
  |       |                |
  v       v                v
Proj A  Proj B           Proj C
  |       |                |
Model A Model B          Model C
```

A provider would then train only a projection or adapter into its model's conditioning space.

This should be treated as a later research milestone, not a dependency for initial adoption.

---

## 14. Reference Adapter

A text-to-format model cannot become format-to-format merely because Kaj exists.

For reference editing, a provider needs some representation of the source asset.

General structure:

```text
reference asset
      |
      v
modality encoder
      |
      v
reference features
      |
      v
Reference Adapter
      |
      v
generator conditioning
```

Potential encoders:

```text
audio codec/latent encoder
image VAE/vision encoder
video latent encoder
mesh/point-cloud encoder
scene graph encoder
```

The protocol should define the *semantic contract* of reference conditioning without prescribing the encoder architecture.

---

## 15. Selection Adapter

Localized editing requires a typed representation of edit locality.

### Audio

```text
time range
event selection
channel/source selection
```

### Image

```text
mask
region
object ID
bounding box
```

### Video

```text
time range
mask track
object track
frame range
```

### Geometry

```text
faces
surface
part
volume
semantic component
```

The model may encode selections through:

- masks,
- attention biases,
- spatial control maps,
- temporal masks,
- latent-region masks,
- point/mesh features.

Kaj specifies the selection semantics, not the implementation.

---

## 16. Preservation Adapter / Constraints

Kaj-Editable models should receive explicit preservation information.

Conceptual:

```text
PreservationConstraint {
    scope
    strength
    tolerance
    metric
}
```

Examples:

```text
outside selection: 1.0
timing: 0.95
camera pose: hard
object identity: 0.9
topology outside selected part: hard
```

Providers may implement these through:

- losses,
- mask constraints,
- latent freezing,
- reconstruction objectives,
- attention restrictions,
- reference feature injection,
- deterministic postprocessing.

---

## 17. Dataset Conversion

Most providers already possess datasets such as:

```text
text + output
```

Kaj adoption should not require manual reannotation of the entire corpus.

Recommended conversion pipeline:

```text
existing artifact
+
existing caption/tags
+
signal/vision/geometry analysis
+
annotation model
        |
        v
Kaj annotation
        |
        v
confidence/provenance filtering
        |
        v
Kaj-conditioned training corpus
```

The provider should preserve annotation provenance.

Example:

```json
{
  "path": "timbre.brightness",
  "value": 0.71,
  "provenance": {
    "source": "signal_analysis"
  }
}
```

---

## 18. Level-1 Training

For Kaj-Conditioned support:

```text
artifact
+
Kaj annotation
```

is enough.

Training target:

```text
Kaj semantic representation
→
conditioning compatible with existing generation behavior
```

The base model may remain frozen.

A provider may initially create Kaj annotations from existing captions and artifact analysis.

---

## 19. Level-2 Training

For Kaj-Referenced support:

```text
reference artifact
+
target Kaj annotation
+
target artifact
```

Training should teach:

```text
preserve useful source structure
+
change semantic identity according to Kaj
```

Identity/no-op pairs are important:

```text
reference
+
no-op Kaj
→
same artifact
```

Without these examples, the model may learn that every conditioning input implies unnecessary change.

---

## 20. Level-3 Training

The most valuable dataset for Kaj-Editable models is transition data:

```text
artifact_t
KajState_t
KajPatch_t
selection_t
invariants_t
artifact_t+1
KajState_t+1
preference_t
```

This teaches:

- what changed,
- what did not change,
- where the edit occurred,
- whether preservation succeeded,
- which result users preferred.

Synthetic transition data can bootstrap early training.

Examples:

### Audio

```text
EQ change
reverb change
time stretch
transient change
event insertion/removal
```

### Image

```text
controlled recolor
object removal
mask-local relighting
background replacement
```

### Geometry

```text
scale selected part
extrude region
move component
material reassignment
controlled deformation
```

Each deterministic transformation produces a known Kaj patch.

---

## 21. Loss Design

The protocol should not mandate one loss, but conformance guidance should encourage multiple objectives.

Conceptually:

```text
L =
    generation_quality
  + semantic_adherence
  + reference_adherence
  + preservation
  + edit_locality
  + temporal/spatial adherence
  + boundary_continuity
```

Modality-specific profiles may define evaluation metrics corresponding to these goals.

---

## 22. Kaj Prompt Translation

Level-0 support should be a first-class part of the protocol, not a hack.

A provider translator maps:

```text
Kaj Neural IR
→
provider request
```

The request may contain:

```text
text prompt
negative prompt
duration
seed
guidance
mask
reference image/audio
strength
provider-native controls
```

The translator should be deterministic given:

```text
Kaj IR
provider adapter version
provider capability manifest
```

unless explicitly documented otherwise.

---

## 23. Persistent Semantic State With Non-Editable Models

Kaj remains valuable even when a provider supports only text-to-format.

Example:

```text
Asset v4
KajState v4
```

User requests:

```text
"make the impact heavier"
```

Kaj produces:

```text
KajState v5
```

Then:

```text
KajState v5
→
provider translator
→
new text prompt
→
text-to-audio model
→
Asset v5
```

This is still regeneration, not true editing.

However, the system preserves:

- semantic state,
- version lineage,
- user delta,
- reproducibility,
- migration path to a future editable provider.

Therefore Kaj-Translated models still provide real product value.

---

## 24. Provider SDK

Kaj should eventually ship provider SDKs.

Possible repository:

```text
kaj-model-sdk/
├── schema/
├── neural_ir/
├── manifests/
├── translators/
├── encoders/
├── adapters/
├── conformance/
├── examples/
└── training/
```

Possible Python package:

```text
kaj_model
```

Possible interfaces:

```python
from kaj_model import KajProfile, KajTranslator, KajCapabilities
```

The SDK should support:

- schema parsing,
- manifest validation,
- Neural IR normalization,
- provider translation,
- compatibility reporting,
- conformance tests.

Neural components should remain optional.

---

## 25. Model-Side Integration Example

Illustrative pseudocode:

```python
kaj_ir = kaj_compiler.lower_neural(
    ast,
    profile="kaj.audio.neural.v1"
)

kaj_features = kaj_encoder(kaj_ir)

output = base_model.generate(
    text_features=text_features,
    kaj_features=kaj_features,
)
```

With reference support:

```python
reference_features = reference_encoder(reference_audio)

output = base_model.generate(
    kaj_features=kaj_features,
    reference_features=reference_features,
)
```

With localized editing:

```python
selection_features = selection_encoder(time_mask)

output = base_model.generate(
    kaj_features=kaj_features,
    reference_features=reference_features,
    selection_features=selection_features,
    preservation=preservation_features,
)
```

---

## 26. Closed API Integration Example

A closed provider can still support Level 0.

```python
class ProviderTranslator:
    def lower(self, kaj_ir):
        return {
            "prompt": render_prompt(kaj_ir),
            "duration": map_duration(kaj_ir),
            "seed": kaj_ir.generation.seed
        }
```

If its API already supports reference inputs or masks, the same adapter can expose higher compatibility without retraining the provider's model.

---

## 27. Model Capability Discovery

Applications should query compatibility before planning an edit.

Example:

```text
User:
"make only this chair leg thicker"
```

Runtime checks:

```text
provider:
  geometry profile: yes
  reference support: yes
  part selection: yes
  local edit: no
```

The runtime may then:

1. choose another provider,
2. fall back to regeneration,
3. ask the user,
4. or reject the operation.

Kaj should not hide capability gaps.

---

## 28. Conformance Tests

Kaj should ship profile-specific test suites.

### Kaj-Translated

Test:

```text
Does translation preserve requested semantic meaning?
Are unsupported fields reported?
```

### Kaj-Conditioned

Test:

```text
Does changing one Kaj property measurably affect the intended property?
```

### Kaj-Referenced

Test:

```text
Does reference identity/structure survive when requested?
```

### Kaj-Editable

Test:

```text
Does the requested region change?
Does the unselected region remain substantially unchanged?
```

### Kaj-Stateful

Test:

```text
Does output semantic state accurately represent the resulting artifact?
```

---

## 29. Example Audio Conformance Task

Input:

```text
reference:
5-second impact sequence

selection:
2.1s → 2.6s

Kaj patch:
second impact.weight += 0.3
second impact.timbre.brightness -= 0.2

preserve:
outside selection
event timing
background
```

Success:

```text
second impact becomes heavier
second impact becomes darker
event timing remains stable
first impact remains stable
third impact remains stable
background remains stable
no boundary artifact
```

---

## 30. Example Image Conformance Task

Input:

```text
reference:
room.png

selection:
couch mask

Kaj patch:
couch.color = dark_green

preserve:
geometry
lighting
camera
background
outside mask
```

Success:

```text
couch color changes
couch geometry remains stable
room lighting remains stable
background remains stable
outside-mask difference remains low
```

---

## 31. Example Geometry Conformance Task

Input:

```text
reference:
chair.glb

selection:
semantic parts role=leg

Kaj patch:
thickness *= 1.15

preserve:
seat geometry
overall height
material
unselected topology
```

Success:

```text
legs become thicker
seat remains stable
height remains stable
material remains stable
unselected topology remains stable
```

---

## 32. Adapter Portability

The Kaj protocol should standardize:

```text
Neural IR
capability manifest
error schema
selection semantics
preservation semantics
versioning
conformance behavior
```

It should *not* standardize:

```text
tensor shapes
attention implementation
latent dimensions
training framework
optimizer
GPU stack
model architecture
```

This lets PyTorch, JAX, MLX, Core ML, proprietary runtimes, and future systems all participate.

---

## 33. Universal Kaj Encoder Research Path

A future Kaj research project may train a cross-domain semantic encoder.

Potential interface:

```text
Kaj Neural IR
      |
      v
Kaj Universal Encoder
      |
      v
shared semantic embedding
```

Providers would train:

```text
shared embedding
→
provider projection
→
model conditioning space
```

Potential advantages:

- lower integration burden,
- shared semantics across vendors,
- better transfer,
- smaller provider-specific datasets,
- common embedding-space evaluation.

Risks:

- lowest-common-denominator semantics,
- cross-domain interference,
- coupling Kaj to one learned representation,
- versioning difficulty.

Therefore the universal encoder should remain optional.

The canonical standard is **Kaj semantics and IR**, not one embedding model.

---

## 34. Security and Trust

Kaj model adapters should be treated as potentially untrusted provider code.

The compiler establishes semantic validity.

The provider determines generation.

The host still owns:

- authorization,
- data access,
- model routing,
- privacy policy,
- file access,
- remote calls,
- billing,
- retention,
- content policy,
- provenance.

A model adapter must not gain privileges merely because Kaj source requested an operation.

---

## 35. Versioning

Version independently:

```text
Kaj language
AST schema
Asset model
domain profile
Neural IR
Model Adapter Protocol
provider adapter
model
```

Example:

```text
Kaj 0.2
Asset v1
kaj.audio.v1
kaj.audio.neural.v1
KMAP 1.0
ProviderAdapter 0.4
Model 3.2
```

Generation metadata should persist all relevant versions.

---

## 36. Recommended Adoption Sequence for Model Developers

### Phase 0

Publish capability manifest.

### Phase 1

Implement:

```text
Kaj Neural IR → provider-native prompt/parameters
```

Claim:

```text
Kaj-Translated
```

### Phase 2

Freeze base model.

Train:

```text
KajEncoder
+
small conditioning adapter
```

Claim:

```text
Kaj-Conditioned
```

### Phase 3

Add:

```text
reference encoder
+
reference adapter
+
identity/no-op training
```

Claim:

```text
Kaj-Referenced
```

### Phase 4

Add:

```text
selection conditioning
+
preservation objective
+
transition dataset
```

Claim:

```text
Kaj-Editable
```

### Phase 5

Predict/persist semantic output state.

Claim:

```text
Kaj-Stateful
```

---

## 37. Recommended Kaj Project Deliverables

To make third-party adoption realistic, Kaj should eventually publish:

```text
Kaj Asset specification
domain profile specifications
Neural IR schemas
capability manifest schema
provider adapter SDK
reference translator implementations
training recipes
sample annotation pipeline
conformance datasets
evaluation harness
example PyTorch adapter
example closed-API translator
```

A provider should not have to invent Kaj integration from scratch.

---

## 38. Central Principle

> **Kaj compatibility should be additive, not foundational-model replacement.**

The preferred path is:

```text
existing model
+
Kaj semantic adapter
+
optional reference adapter
+
optional selection/preservation adapter
```

not:

```text
retrain entire model from zero on Kaj
```

The protocol should make the lowest-cost useful integration possible while leaving a clean path toward true reference-based, localized, stateful editing.

---

## 39. Final Architecture

```text
                     User / Agent
                         |
                         v
                        Kaj
                         |
                         v
                     Kaj AST
                         |
                         v
                   Kaj Compiler
                         |
                         v
                   Neural Asset IR
                         |
             +-----------+-----------+
             |                       |
             v                       v
       Provider Translator       Kaj Adapter
       (zero-training path)    (native path)
             |                       |
             +-----------+-----------+
                         |
                +--------+--------+
                |                 |
                v                 v
         Reference Adapter   Selection Adapter
             optional           optional
                \                 /
                 +-------+-------+
                         |
                         v
                    Base Model
                         |
                         v
                      Artifact
```

Kaj therefore becomes a stable semantic interoperability layer between intelligent agents, creative applications, and heterogeneous generative models.
