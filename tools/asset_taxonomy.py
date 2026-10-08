"""Provider values normalized once for indexing and live discovery."""
POLYHAVEN_TYPES = {0: "hdri", 1: "texture", 2: "model"}


def polyhaven_type(value):
    if type(value) is int:
        return POLYHAVEN_TYPES.get(value, "unknown")
    if isinstance(value, str):
        return {"0": "hdri", "1": "texture", "2": "model", "hdri": "hdri",
                "hdris": "hdri", "texture": "texture", "textures": "texture",
                "model": "model", "models": "model"}.get(value.lower(), "unknown")
    return "unknown"
