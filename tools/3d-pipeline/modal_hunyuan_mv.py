from pathlib import Path
import modal

app = modal.App("arcont-hunyuan3d-mv")

repo = (
    modal.Image.from_registry("nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04", add_python="3.10")
    .apt_install("git", "build-essential", "ninja-build", "libgl1", "libglib2.0-0")
    .run_commands(
        "git clone --depth 1 https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git /opt/Hunyuan3D-2",
        "cd /opt/Hunyuan3D-2 && pip install --upgrade pip setuptools wheel",
        "cd /opt/Hunyuan3D-2 && pip install torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cu121",
        "cd /opt/Hunyuan3D-2 && pip install -r requirements.txt",
        "cd /opt/Hunyuan3D-2 && pip install -e .",
    )
)

weights = modal.Volume.from_name("arcont-hunyuan-weights", create_if_missing=True)

@app.function(
    image=repo,
    gpu="L4",
    timeout=1800,
    volumes={"/root/.cache/huggingface": weights},
)
def generate(front: bytes, left: bytes, back: bytes, right: bytes | None = None) -> bytes:
    import os
    import sys
    import tempfile
    import torch
    from PIL import Image

    sys.path.insert(0, "/opt/Hunyuan3D-2")
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    with tempfile.TemporaryDirectory() as td:
        paths = {}
        for name, payload in {"front": front, "left": left, "back": back, "right": right}.items():
            if payload is None:
                continue
            p = Path(td) / f"{name}.png"
            p.write_bytes(payload)
            paths[name] = p

        images = {name: Image.open(path).convert("RGBA") for name, path in paths.items()}

        pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            "tencent/Hunyuan3D-2mv",
            subfolder="hunyuan3d-dit-v2-mv-turbo",
            variant="fp16",
        )
        if hasattr(pipe, "enable_flashvdm"):
            pipe.enable_flashvdm()

        mesh = pipe(
            image=images,
            num_inference_steps=5,
            octree_resolution=380,
            num_chunks=20000,
            generator=torch.manual_seed(12345),
            output_type="trimesh",
        )[0]

        out = Path(td) / "arcont_survivor_hunyuan_mv.glb"
        mesh.export(out)
        weights.commit()
        return out.read_bytes()

@app.local_entrypoint()
def main(
    front: str = "tools/3d-pipeline/input/front.png",
    left: str = "tools/3d-pipeline/input/left.png",
    back: str = "tools/3d-pipeline/input/back.png",
    right: str = "",
    output: str = "tools/3d-pipeline/output/arcont_survivor_hunyuan_mv.glb",
):
    required = [Path(front), Path(left), Path(back)]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit(f"Missing multiview inputs: {', '.join(missing)}")

    result = generate.remote(
        Path(front).read_bytes(),
        Path(left).read_bytes(),
        Path(back).read_bytes(),
        Path(right).read_bytes() if right and Path(right).exists() else None,
    )
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(result)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
