# FISURA v0.8 — camera composition gate from a real in-engine regression

**Classification:** reusable Godot 4.7.2 observation, not production gameplay.  
**Source game:** [FISURA](https://github.com/heliossamuelhernandezreyes/Godot-juegos-3d.-/pull/14) (work-in-progress; Android performance not validated).

## Failure that the old QA missed

After reducing FISURA's camera distance and compressing its HUD, a real Godot 1280×720 insertion screenshot showed the player **cut off at the bottom**. Basic tests of camera distance, FOV, renderer, shadow budgets and valid PNG content could all pass while the actor's feet were outside the frame.

A simple camera-distance gate also produced a false alarm at the initial spawn: the camera correctly shortened its follow distance next to the arena's perimeter wall. A meaningful test must probe an unobstructed authored shot and *separately* retain wall safety tests.

A second test failed to count four repeated industrial PBR containers and two carts by name: Godot silently assigned automatic node names to duplicate instance labels. Unique, stable asset instance IDs are necessary for observability (model license alone is not sufficient).

## Engine-neutral contract to use in other games

1. Author at least one **insertion**, one **mission interaction**, and one **combat/boss** deterministic shot with a named viewport and actor.
2. Capture real in-engine frames and log camera transform, FOV, pose, viewport size, mission phase and branch commit.
3. Project two or more actor anchor points (foot/head, or mesh AABB corners) to screen coordinates with the engine's equivalent of Godot `Camera3D.unproject_position()`.
4. Require a deliberately chosen in-frame safe region for the projected points in representative gameplay; include **negative fixture tests** with feet cut off and overly wide FOV. Do not interpret camera-wall clamping as an art regression by itself.
5. Audit real vendor model instance count with stable IDs, distinct from count of asset families, and test that render-only dressing doesn't create physical collisions.
6. Keep `viewport_evidence_gate.py` for screenshot integrity/uniqueness but never confuse passing its PNG checks with successful framing or AAA fidelity.

### Example conceptual Godot probe

```gdscript
# For a SceneTree test, root is the Window/Viewport; get_viewport()
# belongs to Node, not SceneTree.
var view_h: float = root.get_visible_rect().size.y
var foot: Vector2 = camera.unproject_position(actor.global_position + Vector3(0, -0.87, 0))
var head: Vector2 = camera.unproject_position(actor.global_position + Vector3(0, 0.93, 0))
var bottom_cropped: bool = foot.y > view_h * 0.95
```

Anchors above are **model-specific** and must be calibrated per skeleton or derived from skinned bounds. This is a static shot gate; it does not measure camera jitter, temporal visibility, animation clipping, frame pacing, draw calls or Android thermal performance.

## QA principle

**A physically valid third-person camera may still be visually invalid.** Use three complementary checks: (1) engine camera/actor projection, (2) real scene screenshot + human composition review, and (3) phone playtest. All three matter before making production-quality claims. ARCONT records this method; FISURA owns the actual camera/HUD scripts, art and screenshots.
