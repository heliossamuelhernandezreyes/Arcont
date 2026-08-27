# Arcont 3D GPU pipeline (Modal + Hunyuan3D-2mv)

## Why Modal
Modal provides GPU functions with no idle billing. Its Starter plan currently includes monthly compute credit, making it suitable for low-volume asset generation during prototyping.

## One-time account setup
1. Create/sign in to a Modal account.
2. Install the Modal CLI locally or use Modal's web setup to create a token.
3. In this GitHub repository add two Actions secrets:
   - `MODAL_TOKEN_ID`
   - `MODAL_TOKEN_SECRET`

Do not commit either token.

## Required input files
Place consistent turnaround renders here:

- `tools/3d-pipeline/input/front.png`
- `tools/3d-pipeline/input/left.png`
- `tools/3d-pipeline/input/back.png`
- `tools/3d-pipeline/input/right.png` (optional)

Use the same character, clothing, proportions, camera height, neutral lighting, plain background, and A/T pose in every view.

## Run
Open GitHub Actions → `Generate 3D on Modal GPU` → Run workflow.

The workflow runs Hunyuan3D-2mv Turbo on an NVIDIA L4 and uploads:

`arcont_survivor_hunyuan_mv.glb`

as the `arcont-hunyuan-multiview` artifact.

## Pipeline status
TripoSR remains available as a CPU blockout backend. Hunyuan3D multiview is the preferred geometry backend for production experiments. Post-processing (retopology, rigging, anatomical segmentation and Godot export) comes after geometry quality is accepted.
