# Copyright 2024-2026 HUMMBL, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Model Registry -- Registry of all frontier AI labs and their models.

Provides metadata for 28 frontier AI labs tracked by Frontier Benchmarks AI,
including HQ, founding year, valuation, flagship model, weight posture,
safety framework, FMF membership, Frontier Index score, and API availability.

Usage:
    from hummbl_governance.evaluations.model_registry import (
        ModelRegistry, LabInfo, list_labs, get_lab,
    )

    registry = ModelRegistry()
    anthropic = registry.get("anthropic")
    print(anthropic.name, anthropic.flagship_model, anthropic.weights)

    all_labs = registry.list_all()
    open_weight_labs = registry.filter_by(weights="open")

Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class LabInfo:
    """Metadata for a frontier AI lab.

    Attributes:
        slug: URL-safe identifier (e.g., "anthropic", "deepseek").
        name: Full lab name.
        hq: Headquarters city, country.
        founded: Founding year.
        valuation: Valuation string (e.g., "$965B") or "subsidiary".
        flagship_model: Name of flagship model (Aug 2026).
        weights: Weight posture — "open", "closed", or "mixed".
        safety_framework: Name of published safety framework or "None published".
        fmf_member: Whether the lab is a Frontier Model Forum member.
        frontier_index: Frontier Benchmarks AI score (0.0 if not ranked).
        api_available: Whether the lab has a public API.
        api_provider: Provider string for API calls (e.g., "anthropic", "openai").
        tier: Account tier from HUMMBL scoring ("A", "B", "C", "D").
        hummbl_score: HUMMBL account-potential score (0-30 unweighted, 0-100 weighted).
    """

    slug: str
    name: str
    hq: str
    founded: int
    valuation: str
    flagship_model: str
    weights: str  # "open", "closed", "mixed"
    safety_framework: str
    fmf_member: bool
    frontier_index: float
    api_available: bool
    api_provider: str
    tier: str = "C"
    hummbl_score: int = 0


# ---------------------------------------------------------------------------
# Lab registry — 28 frontier AI labs (Aug 2026)
# Data sourced from frontier-ai-labs-full28-2026-08-31.md and
# frontier-labs-deep-profiles-2026-08-31.md research artifacts.
# ---------------------------------------------------------------------------

_LABS: tuple[LabInfo, ...] = (
    # Tier 1 — Undisputed Frontier (US)
    LabInfo("openai", "OpenAI", "San Francisco, US", 2015, "$852B",
            "GPT-5.6 Sol/Terra/Luna", "closed",
            "Preparedness Framework v2 + Frontier Governance Framework",
            True, 89.2, True, "openai", "A", 71),
    LabInfo("google-deepmind", "Google DeepMind", "London/Mountain View", 2010,
            "subsidiary (Alphabet $4.4T)", "Gemini 3.7 Flash; Gemini 4 (training)",
            "mixed", "Frontier Safety Framework v3.1", True, 87.5, True,
            "google", "A", 68),
    LabInfo("anthropic", "Anthropic", "San Francisco, US", 2021, "$965B",
            "Claude Fable 5, Opus 5, Sonnet 5", "closed",
            "RSP v3.4 (Jul 2026)", True, 88.1, True, "anthropic", "A", 76),
    LabInfo("meta-msl", "Meta Superintelligence Labs", "Menlo Park, US", 2025,
            "Meta market cap ~$1.4T+", "Muse Spark 1.2; Llama 4 (open)",
            "mixed", "Responsible Use Guide + system cards", True, 82.3,
            True, "meta", "A", 71),
    LabInfo("xai", "xAI", "Austin/Memphis, US", 2023, "$250B (SpaceX merger)",
            "Grok 4.5", "closed", "Model card + risk framework (draft)",
            False, 81.7, True, "xai", "A", 63),
    LabInfo("microsoft-ai", "Microsoft AI", "Redmond, US", 2024,
            "Microsoft market cap ~$4T+", "MAI-Thinking-1, MAI-Code-1-Flash",
            "mixed", "Responsible AI Standard", True, 80.5, True,
            "azure-openai", "A", 68),

    # Tier 2 — Chinese Open-Weight Frontier
    LabInfo("alibaba-qwen", "Alibaba Qwen", "Hangzhou, China", 2023,
            "Alibaba market cap ~$300B+", "Qwen3.8-Max (2.4T, 95B active)",
            "mixed", "None published", False, 83.9, True, "dashscope", "A", 71),
    LabInfo("zai-zhipu", "Z.ai / Zhipu", "Beijing, China", 2019,
            "~$62-128B (HKEX: 2513)", "GLM-5.3-Flash (320B); GLM-5.2 (744B)",
            "open", "None published", False, 80.2, True, "zhipu", "A", 61),
    LabInfo("deepseek", "DeepSeek", "Hangzhou, China", 2023,
            "~$52-74B (Jul 2026)", "DeepSeek V4-Pro (1.6T, 49B active)",
            "open", "None published", False, 82.8, True, "deepseek", "A", 61),
    LabInfo("minimax", "MiniMax", "Shanghai, China", 2021,
            "~$8-12B (Jul 2026)", "MiniMax-M2 (230B); M2.5 (preview)",
            "open", "None published", False, 76.5, True, "minimax", "B", 58),
    LabInfo("moonshot", "Moonshot AI / Kimi", "Beijing, China", 2023,
            "~$20-35B (Jul 2026)", "Kimi K3 (2.8T, 104B active)",
            "open", "None published", False, 81.3, True, "moonshot", "A", 61),
    LabInfo("bytedance", "ByteDance Seed", "Beijing, China", 2023,
            "ByteDance valuation ~$300B+", "Seed2.0 (agentic); Seed1.5",
            "mixed", "None published", False, 79.8, True, "volcengine", "A", 64),
    LabInfo("tencent", "Tencent Hunyuan", "Shenzhen, China", 2022,
            "Tencent market cap ~$500B+", "Hunyuan Hy3 (agentic)",
            "mixed", "None published", False, 78.4, True, "tencent", "A", 62),

    # Tier 3 — Western Mid-Tier + Chinese Vertical
    LabInfo("mistral", "Mistral AI", "Paris, France", 2023, "~$12-15B",
            "Mistral Large 3; Codestral 2", "mixed", "None published",
            False, 74.2, True, "mistral", "A", 63),
    LabInfo("cohere", "Cohere", "Toronto, Canada", 2019, "~$5-8B",
            "Command A+ (111B)", "open", "Cohere Safety Framework",
            False, 70.8, True, "cohere", "A", 62),
    LabInfo("ssi", "SSI (Safe Superintelligence)", "Palo Alto/Tel Aviv", 2024,
            "~$32B", "No products released", "closed",
            "None published (mission-only)", False, 0.0, False, "none", "B", 48),
    LabInfo("baidu", "Baidu ERNIE", "Beijing, China", 2023,
            "Baidu market cap ~$80B+", "ERNIE 4.5 Turbo (agentic)",
            "closed", "None published", False, 75.6, True, "baidu", "B", 52),
    LabInfo("huawei", "Huawei Pangu", "Shenzhen, China", 2023,
            "Huawei (non-public)", "Pangu Ultra (dense, 720B)",
            "closed", "None published", False, 73.1, False, "none", "B", 49),
    LabInfo("amazon-aws", "Amazon AWS AI", "Seattle, US", 2024,
            "Amazon market cap ~$2.4T+", "Nova Pro 2 (frontier effort)",
            "mixed", "AWS Responsible AI Policy", True, 72.5, True,
            "aws-bedrock", "A", 66),
    LabInfo("tml", "Thinking Machines Lab", "San Francisco, US", 2024,
            "~$15-20B", "Inkling 975B (Apache 2.0); Tinker API",
            "open", "None published", False, 71.0, True, "tinker", "A", 61),

    # Tier 4 — Hyperscaler / Device-Integrated
    LabInfo("nvidia", "Nvidia", "Santa Clara, US", 1993,
            "Nvidia market cap ~$3.8T+", "Nemotron 3 Ultra (340B)",
            "open", "Nvidia AI Safety Framework", False, 68.2, True,
            "nvidia", "A", 64),
    LabInfo("lg-ai", "LG AI Research", "Seoul, South Korea", 2020,
            "LG (non-public)", "EXAONE 4.0 (372B)", "closed",
            "None published", False, 65.0, True, "lg", "B", 43),
    LabInfo("apple", "Apple", "Cupertino, US", 2024,
            "Apple market cap ~$3.5T+", "AFM3 (on-device + Cloud Pro)",
            "closed", "Apple Intelligence Privacy Framework", False, 67.5,
            False, "apple", "B", 55),
    LabInfo("samsung", "Samsung", "Suwon, South Korea", 2024,
            "Samsung (non-public)", "Gauss 3 + Gemini + Perplexity",
            "closed", "Samsung AI Ethics Framework", False, 62.0, False,
            "none", "B", 49),
    LabInfo("xiaomi", "Xiaomi", "Beijing, China", 2024,
            "Xiaomi market cap ~$100B+", "MiMo (7B, open)", "open",
            "None published", False, 58.5, True, "xiaomi", "B", 58),

    # Tier 5 — Niche / Research / Vertical
    LabInfo("ant-group", "Ant Group", "Hangzhou, China", 2024,
            "Ant (non-public)", "Ling/Ring (open-weight)", "open",
            "None published", False, 55.0, True, "ant", "B", 47),
    LabInfo("reka", "Reka AI", "San Francisco, US", 2022, "~$170M raised",
            "Reka Core 2 (physical AI)", "mixed", "None published",
            False, 50.0, True, "reka", "B", 45),
    LabInfo("sakana", "Sakana AI", "Tokyo, Japan", 2023, "~$200M raised",
            "Fugu (multi-agent orchestrator)", "mixed",
            "None published", False, 52.0, True, "sakana", "A", 59),
)


class ModelRegistry:
    """Registry of frontier AI labs with metadata lookup.

    Thread-safe, immutable after construction. Data sourced from
    frontier-ai-labs-full28-2026-08-31.md research artifact.
    """

    def __init__(self, labs: tuple[LabInfo, ...] | None = None) -> None:
        self._labs: dict[str, LabInfo] = {}
        for lab in (labs or _LABS):
            self._labs[lab.slug] = lab

    def get(self, slug: str) -> LabInfo | None:
        """Get lab info by slug. Returns None if not found."""
        return self._labs.get(slug)

    def list_all(self) -> list[LabInfo]:
        """List all registered labs, sorted by Frontier Index score."""
        return sorted(self._labs.values(), key=lambda lab: lab.frontier_index, reverse=True)

    def filter_by(
        self,
        *,
        weights: str | None = None,
        fmf_member: bool | None = None,
        api_available: bool | None = None,
        tier: str | None = None,
    ) -> list[LabInfo]:
        """Filter labs by attributes. None means no filter on that attribute."""
        result = list(self._labs.values())
        if weights is not None:
            result = [lab for lab in result if lab.weights == weights]
        if fmf_member is not None:
            result = [lab for lab in result if lab.fmf_member == fmf_member]
        if api_available is not None:
            result = [lab for lab in result if lab.api_available == api_available]
        if tier is not None:
            result = [lab for lab in result if lab.tier == tier]
        return sorted(result, key=lambda lab: lab.frontier_index, reverse=True)

    def count(self) -> int:
        """Number of registered labs."""
        return len(self._labs)

    def __len__(self) -> int:
        return len(self._labs)

    def __iter__(self) -> Iterator[LabInfo]:
        return iter(self.list_all())

    def __contains__(self, slug: str) -> bool:
        return slug in self._labs


def list_labs() -> list[LabInfo]:
    """Convenience function: list all registered labs."""
    return ModelRegistry().list_all()


def get_lab(slug: str) -> LabInfo | None:
    """Convenience function: get lab by slug."""
    return ModelRegistry().get(slug)
