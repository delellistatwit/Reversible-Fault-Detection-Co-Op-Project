# Automated Fault Detection for Reversible Logic Circuits

Fall 2026 co-op project with Prof. Susrutha Babu Sukhavasi, Wentworth Institute of Technology.

The goal is to simulate small reversible logic circuits, inject predefined faults, generate test vectors, select a reduced test set, measure fault coverage, and validate selected results through a VHDL simulation.

## Team

- Jeramiah Simon: hardware design and VHDL validation
- Tyler deLellis: simulator and fault injection
- Matthew Santorsa: testing, optimization, and analytics

## Folder Structure

- `src/` is the Python package root and now keeps the implementation organized by concern.
  - `src/core/` holds the circuit model, reversible gate definitions, and gate metadata.
  - `src/faults_lib/` holds the fault generator, catalog, and mutant-audit tooling.
  - `src/analysis/` holds detection matrices, metrics, plotting, and experiment-analysis utilities.
  - `src/experiments/` holds the end-to-end simulation and optimization entry points.
  - `src/benchmarking/` holds reusable benchmark circuit builders.
  - The legacy flat module paths remain as compatibility shims so existing imports keep working.
- `hardware/` holds VHDL files, testbenches, and Quartus/ModelSim project files.
- `tests/` holds automated unit tests for the Python code.
- `benchmarks/` holds circuit definitions shared by the hardware and software sides, such as the reversible XOR and half adder.
- `results/` holds experiment outputs, such as truth tables, detection matrices, and coverage data.
- `docs/` holds design documents, diagrams, the interface agreement, and progress summaries.

## How to Run

python -m unittest discover tests        # run all unit tests
python -m src.experiments.experiments.integrated_run             # full pipeline: simulate, inject faults, detection matrix, greedy selection
python -m src.faults_lib.fault_catalog              # one CSV row per fault, with the inputs that detect it
python -m src.faults_lib.mutant_audit               # checks that the generated faults are correct and complete
```
Add circuit names to run only those, for example `python -m src.experiments.experiments.integrated_run HALF_ADDER FULL_ADDER`.
