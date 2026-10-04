"""Inspect bounded, hash-verified PCM snapshots; acoustic approval stays project-owned."""
import hashlib
import math
import re
import struct
import tempfile
import wave
from contextlib import ExitStack
from pathlib import Path

try:
    from tools.production_assets import local
except ModuleNotFoundError:
    from production_assets import local

MAX_BYTES = 64 * 1024 * 1024
CHUNK_BYTES = 64 * 1024


def validate(project, record, directory):
    root = Path(project).resolve()
    base = local(root, directory)
    if record.get("version") != 1 or not isinstance(record.get("banks"), dict) or not record["banks"]:
        raise ValueError("explicit audio bank version 1 required")
    references = []
    for category, files in record["banks"].items():
        if (not isinstance(category, str) or not category or not isinstance(files, list)
                or not files or len(files) > 16 or any(not isinstance(f, str) for f in files)
                or len(set(files)) != len(files)):
            raise ValueError("unique bounded audio variants required")
        references.extend(files)
    outputs = record.get("output_hashes")
    if not isinstance(outputs, dict) or set(references) != set(outputs):
        raise ValueError("audio bank and delivered output closure differ")
    with ExitStack() as stack:
        snapshots = {}
        for field, parent in [("source_hashes", root), ("output_hashes", base)]:
            hashes = record.get(field)
            if not isinstance(hashes, dict) or not hashes:
                raise ValueError("source and output hashes required")
            total = 0
            for name, sha in hashes.items():
                if not isinstance(sha, str) or not re.fullmatch("[0-9a-f]{64}", sha):
                    raise ValueError("invalid audio hash")
                path = local(parent, name)
                snapshot = stack.enter_context(tempfile.SpooledTemporaryFile(max_size=1024 * 1024)) if field == "output_hashes" else None
                h = hashlib.sha256()
                count = 0
                with path.open("rb") as source:
                    while chunk := source.read(CHUNK_BYTES):
                        count += len(chunk)
                        total += len(chunk)
                        if total > MAX_BYTES:
                            raise ValueError("audio inspection exceeds 64 MiB")
                        h.update(chunk)
                        if snapshot is not None:
                            snapshot.write(chunk)
                if not count or h.hexdigest() != sha:
                    raise ValueError("empty stream or audio hash mismatch: " + name)
                if snapshot is not None:
                    snapshot.seek(0)
                    snapshots[name] = snapshot
        clips = []
        for name in sorted(snapshots):
            if Path(name).suffix != ".wav":
                raise ValueError("native inspection expects PCM WAV")
            try:
                with wave.open(snapshots[name], "rb") as pcm:
                    if pcm.getsampwidth() != 2 or pcm.getnchannels() not in (1, 2) or pcm.getframerate() not in (22050, 44100, 48000):
                        raise ValueError("supported 16-bit PCM format required")
                    expected = pcm.getnframes() * pcm.getnchannels() * 2
                    read = samples = 0
                    peak = squares = 0.0
                    while data := pcm.readframes(8192):
                        read += len(data)
                        for (sample,) in struct.iter_unpack("<h", data):
                            value = sample / 32768
                            peak = max(peak, abs(value))
                            squares += value * value
                            samples += 1
                    if not samples or read != expected:
                        raise ValueError("empty or truncated PCM payload: " + name)
                    rms = math.sqrt(squares / samples)
                    if peak >= .999 or rms < .0001:
                        raise ValueError("clipped or effectively silent PCM clip: " + name)
                    clips.append({"file": name, "seconds": pcm.getnframes() / pcm.getframerate(),
                                  "peak_dbfs": 20 * math.log10(peak), "rms_dbfs": 20 * math.log10(rms)})
            except (EOFError, wave.Error, struct.error) as error:
                raise ValueError("malformed PCM WAV: " + name) from error
    return {"ok": True, "banks": len(record["banks"]), "clips": clips,
            "limits": ["Diagnostics describe the same bounded byte snapshots as the recorded hashes.",
                       "PCM/hash validation does not approve sound design, spatial mix or device latency.",
                       "Native playback/event routing and human review are required."]}
