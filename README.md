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


### Step 1 Validation Pass
- **Validated Sweeps**: Programmatically verified hyperpolarizing (24-29) and depolarizing (32-35) sweeps.
- **Initial Experimental F-I Relationship**: 
  - Observed distinct rheobase between $+50$ pA and $+70$ pA. 
  - Sweep 33 (+70 pA): 7 spikes. 
  - Sweep 34 (+90 pA): 12 spikes. 
  - Sweep 35 (+110 pA): 17 spikes.
- **Electrophysiological Features**:
  - The neuron exhibits spike-frequency adaptation (ISI increased by ~5.28 ms/spike in Sweep 34).
  - Hyperpolarizing sweeps show excellent subthreshold stability, suitable for passive property extraction.
  - No data quality issues (missing values or clipping) were observed.

### What Step 2 Will Investigate
- **Passive Membrane Model**: We will fit the linear RC subthreshold response ($, $	au_m$, $) using the verified hyperpolarizing sweeps (24-29). Note: No computational models have been implemented yet.

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


## Step 2 — Passive Membrane Model

- **Purpose**: Estimate the subthreshold passive properties of the selected neuron using linear RC dynamics and validate the fit against experimental data.
- **Current Status**: **SUCCESS**
- **Findings**:
  - $V_{rest}$: -76.93 mV
  - $R_m$: 188.71 MOhm
  - $	au_m$: 18.92 ms
  - $C_m$: 100.28 pF
- **Validation**: The fitted passive model reproduced the measured subthreshold response of Sweep 24 (-110 pA) accurately with an RMSE of 2.845 mV.
- **How to Run**:
  ```bash
  python src/allen_data/passive_model.py
  ```
- **Output**:
  - Passive model parameter CSVs: `results/step2/passive_parameters_summary.csv`
  - I-V Curve and Model Validation Plots in `results/step2/`
  - Detailed model documentation: `docs/step2_passive_model.md`

---
---

## Data Provenance
Data cited and retrieved from the **Allen Cell Types Database (2015)**.
Available from: [celltypes.brain-map.org](https://celltypes.brain-map.org/).
© 2015 Allen Institute for Brain Science.
