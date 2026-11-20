"""EducAI Unified Orchestrator backed by OpenMontage ToolRegistry."""

from core.orchestrator._openmontage_env import ensure_openmontage_env, get_registry


def __getattr__(name: str):
    if name == "EducAIPipeline":
        from core.orchestrator.pipeline import EducAIPipeline
        return EducAIPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ensure_openmontage_env", "get_registry", "EducAIPipeline"]
