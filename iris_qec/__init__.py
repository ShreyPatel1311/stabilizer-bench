"""IRIS-QEC: an agent pipeline for StabilizerBench (B1 state preparation, B2 optimization, B3 fault tolerance).

The pipeline separates *interventional* actions (which change the retained candidate circuit) from
*epistemic* actions (which only gather evidence), keeps revisable claim records, targets rewrites at
the circuit segment with the most impact, and selects among verified candidates.

All grading uses the benchmark's own oracles from the pinned submodule (see `benchmark.py`).
"""

__version__ = "0.1.0"
