"""Compatibility re-export for the canonical core kernel helpers."""

from .core.kernels import build_kin_weighted_kernel, build_uniform_kernel, normalize_rows

__all__ = ["normalize_rows", "build_uniform_kernel", "build_kin_weighted_kernel"]
