"""hummbl-axis — the ladder that selects which Atlas contradiction to act on.

Closes the lattice-ladder-loop:
    Atlas (lattice: observe) → Axis (ladder: select) → Human (act) → Atlas (loop: re-observe)

Axis is not a platform. It is a script that:
  1. Reads Atlas evidence cuts (markdown ledger + JSON inventory)
  2. Diffs claimed state against observed state
  3. Emits prioritized contradiction rows
  4. Routes to human (bus post or stdout)
  5. Runs on cadence
  6. Exits when stuck (3 unchanged cycles)
"""

__version__ = "0.1.0"
