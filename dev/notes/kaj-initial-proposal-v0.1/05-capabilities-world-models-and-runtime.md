# 5. Capabilities, World Models, and Runtime

# 5.1 Capabilities make Kaj general

Kaj core should not know how to browse, move a robot, or transform audio.

Instead:

```kaj
use web
use vision
use robot
```

loads typed environmental capability contracts.

## 5.2 `import` vs `use`

Proposed distinction:

```kaj
import math
```

means ordinary code/module dependency.

```kaj
use web
```

means an effectful environmental capability requirement.

## 5.3 Capability contract

A capability should define:

```text
name
version
types
operations
observations
effects
errors
serialization
provider interface
policy metadata
```

## 5.4 Web capability

The first production capability.

Potential types:

```text
Web.Tab
Web.Page
Web.Element
Web.Form
Web.NavigationResult
Web.Download
```

Potential operations:

```text
web.open
web.close
web.switch
web.navigate
web.back
web.forward
web.reload

web.click
web.enter
web.select
web.scroll

web.observe
web.extract
```

The exact API must align with the real Chalok browser workspace/runtime rather than an imagined generic browser.

## 5.5 Vision capability

Future types:

```text
Vision.Scene
Vision.Object
Vision.Mask
Vision.BoundingBox
Vision.DepthMap
Vision.Track
```

Potential operations:

```text
vision.observe
vision.locate
vision.track
vision.segment
vision.measure
```

## 5.6 Robotics capability

Future types:

```text
Robot.Pose
Robot.Grasp
Robot.Trajectory
Robot.JointState
Robot.Force
```

Potential operations:

```text
robot.move_to
robot.grasp
robot.release
robot.rotate
robot.stop
robot.observe_state
```

## 5.7 Navigation capability

Potential types:

```text
Location
Route
Map
Obstacle
Path
```

Potential operations:

```text
navigation.plan
navigation.follow
navigation.stop
navigation.localize
```

## 5.8 Audio capability

Potential types:

```text
Audio.Scene
Audio.Source
Audio.Clip
Audio.Transform
```

Potential operations:

```text
audio.observe
audio.locate
audio.transform
audio.render
audio.verify
```

## 5.9 Providers

The language targets capability contracts; hosts provide implementations.

```text
web
 ├── WKWebView
 ├── Playwright
 └── cloud browser
```

```text
robot
 ├── ROS provider
 ├── simulator provider
 └── proprietary hardware provider
```

## 5.10 Capability versioning

Programs/AST should record requirements:

```text
web@1
vision@1
```

## 5.11 Capability operations and permissions

A low-level action name may not be sufficient for authorization.

Example:

```text
web.click(button)
```

may semantically classify as:

```text
commerce.place_paid_order
```

The host policy engine uses semantic context, not just raw verbs.

## 5.12 Capability SDK

Long-term open-source ecosystem should support third-party providers without compiler modification.

Potential ecosystems:

- ROS,
- Playwright,
- Home Assistant,
- filesystem,
- shell,
- email,
- calendar,
- databases,
- cloud APIs,
- simulation,
- CAD,
- industrial controllers.

# 5.13 Kaj and world models

Kaj is not a world model.

Kaj answers:

> What does the program propose, what must already be true, and what outcome is expected?

A world model answers:

> Given the current state and proposed action, what is likely to happen next?

The runtime answers:

> What actually happened?

## 5.14 Transition model

Conceptually:

```text
(state_t, action_t) → predicted_state_t+1
```

Kaj gives the system a structured action and explicit expected outcomes.

## 5.15 Predict-before-act loop

Long-term:

```text
Kaj action
   ↓
WorldModel.predict
   ↓
predicted next state
   ↓
compare with:
  goal
  invariant
  policy
  safety
  expect clauses
   ↓
execute or replan
```

## 5.16 Post-action loop

```text
actual observation
   ↓
compare with prediction
   ↓
compare with Kaj expectations
   ↓
verification
   ↓
task memory update
   ↓
continue / replan
```

## 5.17 Web example

```kaj
web.click(place_order_button)

expect {
    order.status == confirmed
}
```

A web world model may predict likely navigation/effect semantics. Permission policy still decides whether the action is allowed.

## 5.18 Robotics example

```kaj
robot.grasp(cup)

expect {
    robot.holds(cup)
    cup.position follows robot.gripper
}
```

A world model may predict grasp success/collision risk before execution.

## 5.19 Navigation example

```kaj
navigation.follow(route)

expect {
    distance_to(destination) decreases
    collision == false
}
```

## 5.20 Model-agnostic language

Kaj source should not care whether the host uses:

- deterministic simulation,
- specialist world models,
- multimodal foundation models,
- physics engines,
- learned latent dynamics,
- or no predictor at all.

## 5.21 Training data connection

Kaj execution can generate structured trajectories:

```text
task state
observation
Kaj action
permission decision
prediction
actual result
verification
human feedback
```

This can become high-quality training/evaluation data for future planners and world models.

## 5.22 Predictions are not facts

Preserve:

```text
PREDICT → EXECUTE → OBSERVE → VERIFY
```

Never:

```text
PREDICT → ASSUME SUCCESS
```
