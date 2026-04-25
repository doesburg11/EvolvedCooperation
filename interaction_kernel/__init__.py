"""General interaction-kernel module.

Import symbols from module entrypoints directly when needed to avoid side
effects during module execution with `python -m`.
"""

__all__ = [
    "InteractionKernelModel",
    "run_simulation",
]

from .interaction_kernel_model import InteractionKernelModel, run_simulation
