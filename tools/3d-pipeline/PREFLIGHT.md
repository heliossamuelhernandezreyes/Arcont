# Arcont 3D backend preflight

Run: GitHub Actions `3D Backend Preflight` on Ubuntu 24.04 hosted runners.

Hosted runner observed:
- 4 CPU cores
- ~15 GiB RAM
- ~87 GiB free disk
- no NVIDIA GPU (`nvidia-smi` unavailable)

## SiTH

Status: **not runnable on standard GitHub-hosted CPU runner**.

Evidence from the actual dependency probe:
- requirements pin PyTorch CUDA 12.1 and NVIDIA Kaolin CUDA builds;
- `nvdiffrast` fails during dependency preparation because a CUDA/PyTorch build environment is required;
- SiTH's own documentation tests inference on RTX 3090;
- SMPL-X body model assets are not bundled and must be obtained separately under their own license.

Use case: excellent human-specific reconstruction backend for a GPU worker after SMPL-X assets are supplied.

## ECON

Status: **not runnable as-is on standard GitHub-hosted CPU runner**.

Evidence from the actual dependency probe:
- official Ubuntu instructions require CUDA 11.6 and >12 GB GPU memory;
- requires CuPy, PyTorch3D and SMPL-X/PIXIE assets;
- the current dependency set also hits an old `chumpy` packaging failure with modern pip before inference is reached.

Use case: human reconstruction/SMPL-X animation research backend, but requires a dedicated compatibility environment and GPU.

## Hunyuan3D-2mini / Hunyuan3D-2mv

Status: **best candidate, but inference still needs a GPU worker**.

Evidence from the actual dependency probe:
- repository clones cleanly;
- full `requirements.txt` dependency resolution succeeds (`pip --dry-run` return code 0);
- official docs state ~6 GB VRAM for shape generation and ~16 GB for shape + texture;
- multiview shape models are available, including the 1.1B Hunyuan3D-2mv family;
- the hosted GitHub runner has no NVIDIA GPU.

Recommended Arcont path:
1. Generate a consistent turnaround (front/back/left/right or front/back/side).
2. Run Hunyuan3D multiview on a CUDA worker with >=8 GB VRAM for shape-only prototyping; more VRAM for texturing.
3. Export GLB.
4. Run Blender headless cleanup/decimation/scale validation.
5. Produce a gameplay LOD around the chosen low-poly target.
6. Perform deliberate joint topology and modular gore segmentation rather than trusting automatic retopology at deformation boundaries.
7. Rig/skin and export Godot-ready GLB.

## Licensing note

The Hunyuan3D-2 repository uses the Tencent Hunyuan 3D 2.0 Community License. The current license states Tencent claims no rights in generated Outputs, but it includes territory, distribution, acceptable-use and >1M-MAU commercial terms. Review the license before shipping a product built with the model. Do not copy the model itself into the game distribution unless the license obligations are intentionally satisfied.

## Decision

Keep TripoSR only as a lightweight fallback/blockout generator. Prefer Hunyuan3D multiview for the next serious reconstruction experiment. Keep SiTH as a future human-specific refinement option on a stronger GPU worker if its SMPL-X workflow produces a meaningful quality gain.
