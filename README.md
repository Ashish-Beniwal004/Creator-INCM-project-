# INCM Course Project: How Much Biological Detail Does a Neuron Model Need?

## Project Overview
This repository contains the coursework project for **INCM (Introduction to Neural and Cognitive Modelling)**.
Our project investigates which electrophysiological behaviours of biological neurons can be captured by simplified computational neuron models, and which features necessitate higher biological realism.

### Intended Model Progression (Course Context)
- **Passive Membrane Model** (Subthreshold linear RC dynamics)
- **Leaky Integrate-and-Fire (LIF)** (Threshold-reset spiking mechanism)
- **FitzHugh-Nagumo (FHN)** (2D continuous excitability & limit cycles)
- **Hodgkin-Huxley (HH)** (Biophysical conductance-based ion channel dynamics)

*(Note: Model implementations and comparisons will be built in subsequent project steps).*

---

## Step 1 — Allen Cell Types Data Pipeline

- **Purpose**: Establish reproducible, programmatic access to real neuronal electrophysiology recordings from the Allen Cell Types Database and validate data integrity in Python.
- **Current Status**: **SUCCESS**
- **Selected Neuron**:
  - **Specimen ID**: `485909730`
  - **Specimen Name**: `Cux2-CreERT2;Ai14-205530.03.02.01`
  - **Species**: *Mus musculus* (Mouse)
  - **Brain Region**: Primary Visual Cortex (`VISp`), Layer 5 pyramidal neuron (spiny dendrites)
- **Selected Sweep**:
  - **Sweep Number**: `34`
  - **Stimulus Type**: `Long Square` (1.0 s depolarizing current pulse at $+90.0\text{ pA}$)
  - **Action Potentials**: `12 spikes`
  - **Sampling Rate**: `200,000.0 Hz` ($5\ \mu\text{s}$ sampling resolution)
- **How to Run**:
  ```bash
  # Activate your Python virtual environment
  python src/allen_data/load_recording.py
  ```
  Or run the interactive Jupyter notebook:
  ```bash
  jupyter notebook notebooks/01_allen_data_exploration.ipynb
  ```
- **Output**:
  - Validated recording traces and summary metrics printed to the console.
  - Figure 1: `results/step1/allen_current_trace.png` (Injected Current vs Time in pA)
  - Figure 2: `results/step1/allen_voltage_trace.png` (Membrane Voltage vs Time in mV)
  - Detailed feasibility report: `docs/step1_data_feasibility.md`

---

## Repository Structure
```
Creator-INCM-project-/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                 # Downloaded raw NWB files (excluded from git)
│   └── processed/           # Cached processed features
├── notebooks/
│   └── 01_allen_data_exploration.ipynb   # Step 1 interactive exploration
├── src/
│   └── allen_data/
│       ├── __init__.py
│       └── load_recording.py             # Data loading and validation pipeline
├── results/
│   └── step1/
│       ├── allen_current_trace.png      # Figure 1: Current vs Time
│       └── allen_voltage_trace.png      # Figure 2: Voltage vs Time
└── docs/
    └── step1_data_feasibility.md        # Step 1 documentation & provenance
```

---

## Data Provenance
Data cited and retrieved from the **Allen Cell Types Database (2015)**.
Available from: [celltypes.brain-map.org](https://celltypes.brain-map.org/).
© 2015 Allen Institute for Brain Science.
