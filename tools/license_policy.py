#!/usr/bin/env python3
"""ARCONT Asset Vault license policy.

This module classifies source licenses without pretending that every open
license is equally frictionless for commercial cross-platform distribution.
The automatic vault default is GREEN-only. Conditional and restricted licenses
may be represented by adapters, but require explicit opt-in before ingestion.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class LicensePolicy:
    canonical_name: str
    tier: str
    commercial_use: bool | None
    modification: bool | None
    attribution_required: bool | None
    redistribution_allowed: bool | None
    share_alike: bool | None
    drm_risk: bool | None
    portable_commercial_default: bool
    notes: str

    def to_record_fields(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("canonical_name")
        return data


POLICIES: dict[str, LicensePolicy] = {
    "CC0-1.0": LicensePolicy(
        "CC0-1.0", "green", True, True, False, True, False, False, True,
        "Public-domain dedication. Preferred for automatic cross-platform game-asset ingestion.",
    ),
    "PUBLIC-DOMAIN": LicensePolicy(
        "Public-Domain", "green", True, True, False, True, False, False, True,
        "Public-domain work. Verify the source explicitly marks public-domain status before ingestion.",
    ),
    "CC-BY-3.0": LicensePolicy(
        "CC-BY-3.0", "conditional", True, True, True, True, False, True, False,
        "Attribution is required. OpenGameArt warns that anti-DRM terms may conflict with some distribution platforms.",
    ),
    "CC-BY-4.0": LicensePolicy(
        "CC-BY-4.0", "conditional", True, True, True, True, False, True, False,
        "Attribution is required. Distribution terms must be reviewed for the target platform and packaging.",
    ),
    "CC-BY-SA-3.0": LicensePolicy(
        "CC-BY-SA-3.0", "restricted", True, True, True, True, True, True, False,
        "Share-alike plus attribution obligations. Not automatically portable across closed commercial distribution targets.",
    ),
    "CC-BY-SA-4.0": LicensePolicy(
        "CC-BY-SA-4.0", "restricted", True, True, True, True, True, True, False,
        "Share-alike plus attribution obligations. Requires project-specific legal/distribution review.",
    ),
    "OGA-BY-3.0": LicensePolicy(
        "OGA-BY-3.0", "conditional", True, True, True, True, False, None, False,
        "OpenGameArt attribution license. Requires explicit attribution handling and source-term review.",
    ),
    "GPL-2.0": LicensePolicy(
        "GPL-2.0", "restricted", True, True, True, True, True, None, False,
        "Copyleft software license; unsuitable for automatic general-purpose game-art ingestion without project-specific review.",
    ),
    "GPL-3.0": LicensePolicy(
        "GPL-3.0", "restricted", True, True, True, True, True, True, False,
        "Copyleft and anti-Tivoization/DRM considerations require project-specific review.",
    ),
}

ALIASES = {
    "cc0": "CC0-1.0",
    "cc0 1.0": "CC0-1.0",
    "creative commons cc0": "CC0-1.0",
    "public domain": "PUBLIC-DOMAIN",
    "cc-by 3.0": "CC-BY-3.0",
    "cc by 3.0": "CC-BY-3.0",
    "cc-by 4.0": "CC-BY-4.0",
    "cc by 4.0": "CC-BY-4.0",
    "cc-by-sa 3.0": "CC-BY-SA-3.0",
    "cc by-sa 3.0": "CC-BY-SA-3.0",
    "cc-by-sa 4.0": "CC-BY-SA-4.0",
    "cc by-sa 4.0": "CC-BY-SA-4.0",
    "oga-by 3.0": "OGA-BY-3.0",
    "oga-by": "OGA-BY-3.0",
    "gpl 2": "GPL-2.0",
    "gpl 2.0": "GPL-2.0",
    "gpl 3": "GPL-3.0",
    "gpl 3.0": "GPL-3.0",
}


def normalize_license_name(raw: str) -> str | None:
    text = " ".join(raw.lower().replace("_", " ").split())
    if text in ALIASES:
        return ALIASES[text]
    for alias, canonical in sorted(ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if alias in text:
            return canonical
    return None


def classify(raw: str) -> LicensePolicy | None:
    key = normalize_license_name(raw)
    return POLICIES.get(key) if key else None


def is_auto_ingestible(raw: str) -> bool:
    policy = classify(raw)
    return bool(policy and policy.tier == "green" and policy.portable_commercial_default)
