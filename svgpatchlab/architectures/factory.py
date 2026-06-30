from __future__ import annotations

from .base import Architecture
from .diagnostic import OraclePatchArchitecture, OracleTargetArchitecture, TwoStagePatchArchitecture
from .patching import (
    FullContextPatchArchitecture,
    SkeletonPatchArchitecture,
    VisualSkeletonPatchArchitecture,
)
from .rewrite import FullRewriteArchitecture
from .rules import RuleBasedPatchArchitecture


ARCHITECTURES: dict[str, type[Architecture]] = {
    "oracle_patch": OraclePatchArchitecture,
    "rule_based_patch": RuleBasedPatchArchitecture,
    "full_rewrite": FullRewriteArchitecture,
    "full_context_patch": FullContextPatchArchitecture,
    "skeleton_patch": SkeletonPatchArchitecture,
    "visual_skeleton_patch": VisualSkeletonPatchArchitecture,
    "oracle_target_patch": OracleTargetArchitecture,
    "two_stage_patch": TwoStagePatchArchitecture,
}


def create_architecture(name: str) -> Architecture:
    try:
        return ARCHITECTURES[name]()
    except KeyError as exc:
        raise ValueError(f"unknown architecture: {name}") from exc
