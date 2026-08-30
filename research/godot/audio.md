# Godot — Audio Architecture

## Why audio is systemic
Shooter feel depends on timing, layering, spatial cues and material response as much as raw sample quality.

## Proposed layers
- Master
- Music
- Weapons
- Impacts
- Foley/footsteps
- Enemies/voices
- R-3/dialogue
- Environment/ambience
- UI

## Topics
- Audio buses/effects and dynamic routing.
- AudioStreamPlayer3D attenuation and spatialization.
- Weapon layers: mechanical transient, muzzle blast, body, distant tail, environment tail.
- Material-specific impacts.
- Footstep surface system.
- Occlusion/reverb research.
- Polyphony/voice stealing and priority.
- Distance LOD for sound complexity.
- Adaptive music/event-driven scoring.
- Loudness/headroom and mobile speaker/headphone testing.
- Accessibility: subtitles/captions and independent mix controls.

## References
- Godot audio buses: https://docs.godotengine.org/en/stable/tutorials/audio/audio_buses.html
- AudioStreamPlayer3D: https://docs.godotengine.org/en/stable/classes/class_audiostreamplayer3d.html
- MarekZdun godot-audio-manager: https://github.com/MarekZdun/godot-audio-manager
- artom-studios G4-audio-manager: https://github.com/artom-studios/G4-audio-manager
- claudehohl SpatialAudio3D: https://github.com/claudehohl/SpatialAudio3D

## License rule
Audit each external repository before reuse; architecture may be studied even when direct reuse is inappropriate.

## Status
Architecture research: OPEN. Production audio is a major vertical-slice gap.
