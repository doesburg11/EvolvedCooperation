"""Mechanism implementations that plug into the shared Moran interaction core."""

from __future__ import annotations

from typing import Any, Protocol

import numpy as np

from .kernels import build_kin_weighted_kernel, build_uniform_kernel, normalize_rows

ExtraState = dict[str, np.ndarray]


class MoranMechanism(Protocol):
    """Protocol for mechanism logic consumed by the shared engine."""

    name: str

    def initialize_extra_state(
        self,
        cfg: dict[str, Any],
        n_sites: int,
        rng: np.random.Generator,
    ) -> ExtraState:
        ...

    def build_positive_kernel(
        self,
        neighbor_mask: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        ...

    def build_negative_kernel(
        self,
        neighbor_mask: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        ...

    def compute_positive_output(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        ...

    def compute_negative_output(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        ...

    def compute_private_cost(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        ...

    def inherit_extra_state(
        self,
        extra_state: ExtraState,
        parent_indices: np.ndarray,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> ExtraState:
        ...

    def post_reproduction_update(
        self,
        trait: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> tuple[np.ndarray, np.ndarray, ExtraState]:
        ...


class BaseKernelMechanism:
    """Default mechanism behavior for kernel-routed Moran models."""

    name = "kernel_mechanism"

    def initialize_extra_state(
        self,
        cfg: dict[str, Any],
        n_sites: int,
        rng: np.random.Generator,
    ) -> ExtraState:
        del cfg, n_sites, rng
        return {}

    def compute_positive_output(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        del extra_state
        return float(cfg["B_plus_scale"]) * trait

    def compute_negative_output(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        del extra_state
        return float(cfg["B_minus_scale"]) * trait

    def compute_private_cost(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        del extra_state
        return float(cfg["C_scale"]) * trait

    def inherit_extra_state(
        self,
        extra_state: ExtraState,
        parent_indices: np.ndarray,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> ExtraState:
        del step_context, rng, cfg
        return {key: values[parent_indices].copy() for key, values in extra_state.items()}

    def post_reproduction_update(
        self,
        trait: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> tuple[np.ndarray, np.ndarray, ExtraState]:
        del step_context, rng, cfg
        return trait, lineage, extra_state


class ConfigDrivenKernelMechanism(BaseKernelMechanism):
    """Use the active config dict to choose positive and negative kernels."""

    name = "interaction_kernel"

    def build_positive_kernel(
        self,
        neighbor_mask: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        del extra_state
        mode = str(cfg["positive_kernel_mode"])
        if mode == "uniform":
            return build_uniform_kernel(neighbor_mask)
        if mode == "kin_weighted":
            return build_kin_weighted_kernel(
                neighbor_mask,
                lineage,
                float(cfg["kin_weight_same_lineage"]),
                float(cfg["kin_weight_other_lineage"]),
            )
        raise ValueError(f"Unsupported positive_kernel_mode: {mode}")

    def build_negative_kernel(
        self,
        neighbor_mask: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        del lineage, extra_state
        mode = str(cfg["negative_kernel_mode"])
        if mode == "none":
            return np.zeros(neighbor_mask.shape, dtype=float)
        if mode == "uniform":
            return build_uniform_kernel(neighbor_mask)
        raise ValueError(f"Unsupported negative_kernel_mode: {mode}")


class KinSelectionMechanism(ConfigDrivenKernelMechanism):
    """Named mechanism wrapper for kin-weighted positive routing."""

    name = "kin_selection"


class NetworkReciprocityMechanism(ConfigDrivenKernelMechanism):
    """Named mechanism wrapper for sparse/local interaction structure."""

    name = "network_reciprocity"


class DirectReciprocityMechanism(ConfigDrivenKernelMechanism):
    """Direct reciprocity via persistent local partner memory.

    The evolving trait `h` determines how much cooperation an agent can express.
    In the default mode, `partner_memory[i, j]` tracks how much site `i`
    remembers being helped by site `j`, so future help from `i` is biased back
    toward `j`.
    """

    name = "direct_reciprocity"

    def _mode(self, cfg: dict[str, Any]) -> str:
        return str(cfg.get("direct_reciprocity_mode", "partner_memory"))

    def _memory_expression(
        self,
        memory: np.ndarray,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        baseline = float(cfg.get("memory_baseline_expression", 0.35))
        gain = float(cfg.get("memory_expression_gain", 0.85))
        return np.clip(baseline + gain * memory, 0.0, 1.0)

    def initialize_extra_state(
        self,
        cfg: dict[str, Any],
        n_sites: int,
        rng: np.random.Generator,
    ) -> ExtraState:
        del rng
        initial_memory = float(cfg.get("memory_initial", 0.0))
        mode = self._mode(cfg)
        if mode == "received_help_memory":
            return {
                "reciprocity_memory": np.full(n_sites, initial_memory, dtype=float),
            }
        if mode == "partner_memory":
            return {
                "partner_memory": np.full((n_sites, n_sites), initial_memory, dtype=float),
            }
        raise ValueError(f"Unsupported direct_reciprocity_mode: {mode}")

    def build_positive_kernel(
        self,
        neighbor_mask: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        mode = self._mode(cfg)
        if mode == "received_help_memory":
            return super().build_positive_kernel(neighbor_mask, lineage, extra_state, cfg)
        if mode != "partner_memory":
            raise ValueError(f"Unsupported direct_reciprocity_mode: {mode}")

        interaction_mask = neighbor_mask.astype(bool).copy()
        if not bool(cfg.get("direct_reciprocity_include_self_interaction", False)):
            np.fill_diagonal(interaction_mask, False)

        partner_memory = np.clip(extra_state["partner_memory"], 0.0, 1.0)
        expression = self._memory_expression(partner_memory, cfg)
        neighbor_weights = interaction_mask.astype(float)
        neighbor_count = neighbor_weights.sum(axis=1)
        safe_count = np.where(neighbor_count > 0.0, neighbor_count, 1.0)
        kernel = neighbor_weights * expression / safe_count[:, None]
        extra_state["reciprocity_expression"] = kernel.sum(axis=1)
        extra_state["reciprocity_neighbor_count"] = safe_count
        return kernel

    def compute_positive_output(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        if self._mode(cfg) == "partner_memory":
            del extra_state
            return float(cfg["B_plus_scale"]) * trait

        memory = extra_state["reciprocity_memory"]
        expressed_fraction = self._memory_expression(memory, cfg)
        return float(cfg["B_plus_scale"]) * trait * expressed_fraction

    def compute_private_cost(
        self,
        trait: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        if self._mode(cfg) != "partner_memory":
            return super().compute_private_cost(trait, extra_state, cfg)

        cost_mode = str(cfg.get("direct_reciprocity_cost_mode", "expressed"))
        if cost_mode == "capacity":
            return float(cfg["C_scale"]) * trait
        if cost_mode != "expressed":
            raise ValueError(f"Unsupported direct_reciprocity_cost_mode: {cost_mode}")

        expression = extra_state.get("reciprocity_expression")
        if expression is None:
            expression = np.ones_like(trait)
        return float(cfg["C_scale"]) * trait * np.clip(expression, 0.0, 1.0)

    def inherit_extra_state(
        self,
        extra_state: ExtraState,
        parent_indices: np.ndarray,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> ExtraState:
        del extra_state
        mode = self._mode(cfg)
        if mode == "partner_memory":
            previous_memory = step_context["partner_memory"]
            positive_kernel = step_context["K_plus"]
            positive_output = step_context["B_plus"]
            neighbor_count = step_context["reciprocity_neighbor_count"]
            base_scale = max(float(cfg["B_plus_scale"]), 1e-9)
            max_edge_help = base_scale / np.maximum(neighbor_count, 1.0)
            help_sent = positive_kernel * positive_output[:, None]
            normalized_help_sent = np.clip(help_sent / max_edge_help[:, None], 0.0, 1.0)
            received_from_partner = normalized_help_sent.T

            decay = float(cfg.get("memory_decay", 0.35))
            updated_memory = decay * previous_memory + (1.0 - decay) * received_from_partner
            next_memory = updated_memory[parent_indices, :].copy()

            if bool(cfg.get("reset_memory_on_mutation", False)):
                mutation_rate = float(cfg.get("mutation_rate", 0.0))
                reset_value = float(cfg.get("memory_initial", 0.0))
                reset_mask = rng.random(len(parent_indices)) < mutation_rate
                next_memory[reset_mask, :] = reset_value

            return {
                "partner_memory": np.clip(next_memory, 0.0, 1.0),
            }

        if mode != "received_help_memory":
            raise ValueError(f"Unsupported direct_reciprocity_mode: {mode}")

        previous_memory = step_context["reciprocity_memory"]
        positive_return = step_context["R_plus"]
        base_scale = max(float(cfg["B_plus_scale"]), 1e-9)
        normalized_return = np.clip(positive_return / base_scale, 0.0, 1.0)
        decay = float(cfg.get("memory_decay", 0.35))
        updated_memory = decay * previous_memory + (1.0 - decay) * normalized_return
        next_memory = updated_memory[parent_indices].copy()

        if bool(cfg.get("reset_memory_on_mutation", False)):
            mutation_rate = float(cfg.get("mutation_rate", 0.0))
            reset_value = float(cfg.get("memory_initial", 0.0))
            reset_mask = rng.random(len(parent_indices)) < mutation_rate
            next_memory[reset_mask] = reset_value

        return {
            "reciprocity_memory": np.clip(next_memory, 0.0, 1.0),
        }


class IndirectReciprocityMechanism(ConfigDrivenKernelMechanism):
    """Indirect reciprocity through a public reputation channel.

    Reputation is tracked per site, inherited through local reproduction, and
    used to bias positive routing toward better-reputed recipients.
    """

    name = "indirect_reciprocity"

    def initialize_extra_state(
        self,
        cfg: dict[str, Any],
        n_sites: int,
        rng: np.random.Generator,
    ) -> ExtraState:
        del rng
        default_rep = float(cfg.get("reputation_default", 0.5))
        return {
            "reputation": np.full(n_sites, default_rep, dtype=float),
        }

    def build_positive_kernel(
        self,
        neighbor_mask: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        cfg: dict[str, Any],
    ) -> np.ndarray:
        del lineage
        reputation = np.clip(extra_state["reputation"], 0.0, 1.0)
        bias = float(cfg.get("reputation_kernel_bias", 0.10))
        exponent = float(cfg.get("reputation_kernel_exponent", 1.0))
        recipient_weight = bias + np.power(reputation, exponent)
        weights = neighbor_mask.astype(float) * recipient_weight[None, :]
        return normalize_rows(weights)

    def inherit_extra_state(
        self,
        extra_state: ExtraState,
        parent_indices: np.ndarray,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> ExtraState:
        del extra_state, rng
        previous_reputation = step_context["reputation"]
        base_scale = max(float(cfg["B_plus_scale"]), 1e-9)
        observed_helping = np.clip(step_context["B_plus"] / base_scale, 0.0, 1.0)
        observation_weight = float(cfg.get("reputation_observation_weight", 0.35))
        updated_reputation = (
            (1.0 - observation_weight) * previous_reputation
            + observation_weight * observed_helping
        )
        next_reputation = updated_reputation[parent_indices].copy()
        return {
            "reputation": np.clip(next_reputation, 0.0, 1.0),
        }


class GroupSelectionMechanism(ConfigDrivenKernelMechanism):
    """Group selection with fixed group membership and periodic group copying."""

    name = "group_selection"

    def initialize_extra_state(
        self,
        cfg: dict[str, Any],
        n_sites: int,
        rng: np.random.Generator,
    ) -> ExtraState:
        del rng
        group_count = max(1, int(cfg.get("group_count", 8)))
        group_id = (np.arange(n_sites, dtype=np.int32) * group_count) // n_sites
        return {
            "group_id": group_id,
        }

    def inherit_extra_state(
        self,
        extra_state: ExtraState,
        parent_indices: np.ndarray,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> ExtraState:
        del parent_indices, step_context, rng, cfg
        # Group membership is a fixed site property in this mechanism.
        return {
            "group_id": extra_state["group_id"].copy(),
        }

    def post_reproduction_update(
        self,
        trait: np.ndarray,
        lineage: np.ndarray,
        extra_state: ExtraState,
        step_context: dict[str, np.ndarray],
        rng: np.random.Generator,
        cfg: dict[str, Any],
    ) -> tuple[np.ndarray, np.ndarray, ExtraState]:
        interval = max(1, int(cfg.get("group_selection_interval", 25)))
        step_index = int(step_context["step_index"][0])
        if (step_index + 1) % interval != 0:
            return trait, lineage, extra_state

        group_id = extra_state["group_id"]
        fitness = step_context["fitness"]
        unique_groups = np.unique(group_id)
        if unique_groups.size < 2:
            return trait, lineage, extra_state

        group_means = np.array(
            [float(np.mean(fitness[group_id == g])) for g in unique_groups],
            dtype=float,
        )
        source_group = int(unique_groups[int(np.argmax(group_means))])
        sink_group = int(unique_groups[int(np.argmin(group_means))])
        if source_group == sink_group:
            return trait, lineage, extra_state

        source_idx = np.where(group_id == source_group)[0]
        sink_idx = np.where(group_id == sink_group)[0]
        if source_idx.size == 0 or sink_idx.size == 0:
            return trait, lineage, extra_state

        copied_from_source = rng.choice(source_idx, size=sink_idx.size, replace=True)

        next_trait = trait.copy()
        next_lineage = lineage.copy()
        next_trait[sink_idx] = trait[copied_from_source]
        next_lineage[sink_idx] = lineage[copied_from_source]

        next_extra_state: ExtraState = {}
        for key, values in extra_state.items():
            copied = values.copy()
            if key != "group_id":
                copied[sink_idx] = values[copied_from_source]
            next_extra_state[key] = copied

        return next_trait, next_lineage, next_extra_state
