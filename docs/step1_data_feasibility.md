# Step 1: Allen Cell Types Data Feasibility & First Neuron Recording

## 1. Executive Summary & Result
- **Pipeline Status**: **SUCCESS** — The Allen electrophysiology data pipeline was successfully established.
- **Core Objective**: Verify that we can reliably access real whole-cell current-clamp electrophysiology recordings from the Allen Cell Types Database, load the standardized NWB (Neurodata Without Borders) format in Python, validate the recording integrity, and reproduce stimulus and membrane voltage responses.
- **Suitability for Later Modelling Phases**: **Confirmed**. The selected neuron displays a clean baseline resting potential (~ -77.6 mV), robust input resistance, and a graded current-to-firing-rate response across current steps (from subthreshold hyperpolarization up to 17+ action potentials), making it ideal for testing our model progression (Passive Membrane -> LIF -> FitzHugh-Nagumo -> Hodgkin-Huxley).

---

## 2. Selected Neuron Profile & Metadata

The selected specimen is an excitatory pyramidal neuron from the mouse primary visual cortex, recorded under the standardized whole-cell patch-clamp protocol of the Allen Institute for Brain Science:

| Metadata Field | Value | Notes |
| :--- | :--- | :--- |
| **Specimen ID** | `485909730` | Unique Allen Institute specimen identifier |
| **Specimen Name / Cell ID** | `Cux2-CreERT2;Ai14-205530.03.02.01` | Transgenic line targeting cortical layers 2/3 & 4/5 |
| **Species** | *Mus musculus* (Mouse) | Laboratory mouse |
| **Brain Region** | Primary Visual Cortex (`VISp`) | Structure Area ID: `385` |
| **Cortical Layer** | Layer 5 | Infragranular pyramidal layer |
| **Dendrite Type** | Spiny | Characteristic of excitatory pyramidal neurons |
| **Apical State** | Intact | Morphologically complete apical trunk |
| **Reconstruction Type** | Dendrite-only | Full 3D dendritic tracing available |
| **Donor ID** | `485250100` | Mouse donor identifier |
| **Transgenic Line** | `Cux2-CreERT2` | Cre driver |
| **Electrophysiology Availability** | Yes (`35` recorded sweeps) | Whole-cell current clamp |

---

## 3. Recording & Selected Sweep Characteristics

To test current-clamp dynamics and future F-I (current-frequency) curve construction, we inspected all 12 "Long Square" current-step sweeps and selected **Sweep 34** as our primary exemplar:

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Selected Sweep** | `34` | Depolarizing suprathreshold current step |
| **Stimulus Name** | `Long Square` | Constant current pulse |
| **Stimulus Description** | `C1LSCOARSE150216[10]` | Standardized Allen step protocol |
| **Stimulus Duration** | `1.000 s` (1000 ms) | Active from $t = 1.020\text{ s}$ to $t = 2.020\text{ s}$ |
| **Stimulus Amplitude** | `+90.0 pA` ($9.0 \times 10^{-11}\text{ A}$) | Depolarizing pulse above rheobase |
| **Total Recording Duration** | `8.020 s` | Baseline, step, and post-pulse recovery |
| **Sampling Rate** | `200,000.0 Hz` (200 kHz) | Time step $\Delta t = 5\ \mu\text{s}$ ($0.000005\text{ s}$) |
| **Total Number of Samples** | `1,604,001` samples | High-resolution recording array |
| **Resting Membrane Potential** | `~ -77.6 mV` ($-0.0776\text{ V}$) | Stable pre-stimulus baseline |
| **Peak Action Potential** | `+16.81 mV` ($+0.0168\text{ V}$) | Full-overshoot action potentials |
| **Official Allen Spike Count** | `12 spikes` | Annotated in Allen metadata |
| **Verified Spikes (> -20 mV)** | `12 spikes` | Independently verified via threshold crossing |

### Context Across Other Long Square Sweeps for F-I Mapping
The cell exhibits a clean, graded firing progression across sweeps:
- **Sweep 24 to 29**: Hyperpolarizing steps ($-110\text{ pA}$ to $-10\text{ pA}$, 0 spikes) — perfect for extracting passive membrane resistance $R_m$ and membrane time constant $\tau_m$.
- **Sweep 30 to 32**: Subthreshold depolarizations ($+10\text{ pA}$ to $+50\text{ pA}$, 0 spikes).
- **Sweep 33**: $+70\text{ pA} \to 7\text{ spikes}$ (rheobase around 60–70 pA).
- **Sweep 34**: $+90\text{ pA} \to 12\text{ spikes}$ (**selected primary sweep**).
- **Sweep 35**: $+110\text{ pA} \to 17\text{ spikes}$.

---

## 4. Data Format & Architecture (NWB)
- The raw intracellular electrophysiological recordings are stored in **NWB (Neurodata Without Borders)** format, an open standard for neurophysiology data based on HDF5 (`.nwb` file extension).
- In NWB files:
  - Injected current traces are stored in SI units of **Amperes (A)**.
  - Membrane voltage traces are stored in SI units of **Volts (V)**.
- Data access is mediated through `allensdk.core.cell_types_cache.CellTypesCache` and `allensdk.core.nwb_data_set.NwbDataSet`.
- To maintain repository efficiency, raw binary `.nwb` files (~17.3 MB per cell) are downloaded on-demand into `data/raw/` and excluded from version control via `.gitignore`.

---

## 5. Figures & Visualizations

The generated figures are stored in `results/step1/`:

1. **Injected Current vs Time** (`results/step1/allen_current_trace.png`):
   - Displays the 1.0 s step current pulse at $+90\text{ pA}$ starting at $t = 1.02\text{ s}$ and ending at $t = 2.02\text{ s}$ (preceded by the brief Allen test pulse at $t = 0\text{ s}$).
2. **Membrane Voltage vs Time** (`results/step1/allen_voltage_trace.png`):
   - Displays resting potential at $-77.6\text{ mV}$, followed by a regular train of 12 full-amplitude action potentials peaking at $+16.8\text{ mV}$, accompanied by spike-frequency adaptation and post-stimulus recovery.

---

## 6. Problems Encountered & Solutions

| Issue Encountered | Diagnosis | Solution Implemented |
| :--- | :--- | :--- |
| **NumPy 2.x Incompatibility** | Python 3.12 installs NumPy 2.x by default, which deprecates `np.VisibleDeprecationWarning` and changes C APIs required by AllenSDK 2.16.2. | Pinned `numpy==1.26.4` (the final NumPy 1.x release supporting Python 3.12) and `scipy==1.13.1`. |
| **Missing Optional AllenSDK Subdependencies** | Importing `CellTypesCache` triggers secondary imports in AllenSDK that require `SimpleITK`, `argschema`, `xarray`, `statsmodels`, etc. | Installed and pinned all required subdependencies cleanly in `.venv` and documented them in `requirements.txt`. |
| **Windows Console Codec (`cp1252`)** | Outputting Unicode symbols ($\mu\text{s}$, bullets) caused a `charmap` encode error on Windows cmd/powershell terminals. | Replaced non-ASCII characters in console logging with standard ASCII (`us`, hyphens) while preserving high-precision formatting in plots and docs. |

---

## 7. Data Provenance & Academic Attribution
- **Dataset**: Allen Cell Types Database
- **Provider**: Allen Institute for Brain Science
- **Resource URL**: [https://celltypes.brain-map.org/](https://celltypes.brain-map.org/)
- **API Endpoint**: `http://api.brain-map.org/api/v2/well_known_file_download/491316386` (NWB Download ID: `491316386`)
- **Access Method**: Automated programmatic download via `allensdk.core.cell_types_cache.CellTypesCache`
- **Date Accessed**: September 2026
- **Attribution Statement**:
  > *Data cited and retrieved from the Allen Cell Types Database (2015). Available from: celltypes.brain-map.org. © 2015 Allen Institute for Brain Science.*

---

## 8. Reproduction Instructions

To reproduce Step 1 from a freshly cloned repository:

```bash
# 1. Clone repository
git clone https://github.com/Ashish-Beniwal004/Creator-INCM-project-.git
cd Creator-INCM-project-
git checkout step1/allen-data-feasibility

# 2. Create and activate virtual environment (Python 3.12 recommended)
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# 3. Install validated dependencies
pip install -r requirements.txt

# 4. Run data loading, validation, and figure generation pipeline
python src/allen_data/load_recording.py

# 5. (Optional) Run the exploration Jupyter notebook
jupyter execute notebooks/01_allen_data_exploration.ipynb
```
