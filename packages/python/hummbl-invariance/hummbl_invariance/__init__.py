"""hummbl-invariance — measure whether a stance survives transformation.

Seven axes (paraphrase, order, negation, persona, temperature, pushback,
checkpoint-time) applied to one probe. A pass does not mean the answer was
right; it means the answer did not move when nothing gave it a principled
reason to.
"""

from __future__ import annotations

from hummbl_invariance.axes import (
    AXIS_CLASSES,
    Axis,
    CheckpointAxis,
    NegationAxis,
    OrderAxis,
    ParaphraseAxis,
    PersonaAxis,
    PushbackAxis,
    TemperatureAxis,
    build_axis,
)
from hummbl_invariance.battery import BatteryRun, Classifier, InvarianceBattery, Responder
from hummbl_invariance.loader import load_axis_catalog, load_run_schema
from hummbl_invariance.models import (
    AxisResult,
    Baseline,
    Observation,
    Probe,
    Pushback,
    Variant,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "AXIS_CLASSES",
    "Axis",
    "AxisResult",
    "Baseline",
    "BatteryRun",
    "CheckpointAxis",
    "Classifier",
    "InvarianceBattery",
    "NegationAxis",
    "Observation",
    "OrderAxis",
    "ParaphraseAxis",
    "PersonaAxis",
    "Probe",
    "Pushback",
    "PushbackAxis",
    "Responder",
    "TemperatureAxis",
    "Variant",
    "build_axis",
    "load_axis_catalog",
    "load_run_schema",
]
