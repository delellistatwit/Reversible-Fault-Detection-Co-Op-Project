# Automated Fault Detection for Reversible Logic Circuits

Fall 2026 co-op project with Prof. Susrutha Babu Sukhavasi, Wentworth Institute of Technology.

The goal is to simulate small reversible logic circuits, inject predefined faults, generate test vectors, select a reduced test set, measure fault coverage, and validate selected results through a VHDL simulation.

## Team

- Jeramiah Simon: hardware design and VHDL validation
- Tyler deLlellis: simulator and fault injection
- Matthew Santorsa: testing, optimization, and analytics

## Folder Structure

- `src/` holds the Python source code (gates, circuits, faults, test generation, and analysis).
- `hardware/` holds VHDL files, testbenches, and Quartus/ModelSim project files.
- `tests/` holds automated unit tests for the Python code.
- `benchmarks/` holds circuit definitions shared by the hardware and software sides, such as the reversible XOR and half adder.
- `results/` holds experiment outputs, such as truth tables, detection matrices, and coverage data.
- `docs/` holds design documents, diagrams, the interface agreement, and progress summaries.

## How to Run

Instructions will be added as each part of the project is completed.
