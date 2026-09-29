

# INCM Project Proposal: How Much Biological Detail Does a Neuron Model Need?

**Course:** Introduction to Neural and Cognitive Modelling (INCM)  
**Team Members:** Student 1: [NAME / ROLL NUMBER] | Student 2: [NAME / ROLL NUMBER]  
**Proposal Deadline:** 30/09/2026  

---

## 1. Research Question and Aim
The core research question of our project is: *How much biological detail is required for computational neuron models to accurately reproduce selected electrophysiological behaviours of a real biological neuron?* 

Our primary aim is not to declare a single "best" model, as model usefulness is inherently purpose-dependent. Rather, we will investigate a progression of computational models—Passive Membrane, Leaky Integrate-and-Fire (LIF), FitzHugh-Nagumo (FHN), and Hodgkin-Huxley (HH)—to systematically characterize the trade-off between biological detail, behavioural fidelity, and computational complexity. By determining what behaviours each model can and cannot reproduce, we aim to isolate the specific biological mechanisms that account for these differences.

## 2. Motivation and Background
Neuron-level modelling requires choosing an appropriate abstraction level. A passive RC model captures basic subthreshold voltage decay but fails to generate action potentials. Phenomenological spiking models, like LIF, introduce a hard threshold for firing, while continuous excitability models, like FHN, capture nonlinear limit cycle dynamics. Detailed biophysical models, such as HH, explicitly model the ion-channel conductances responsible for the action potential shape and adaptation but at a high computational cost. 
This project will bridge the gap between these theoretical models covered in the INCM coursework and empirical data, explicitly testing the boundaries and limitations of each model level.

## 3. Data and Computational Approach
We will utilize the **Allen Cell Types Database** as our source of high-resolution empirical electrophysiology data. To constrain our project scope and ensure rigorous analysis, we will focus on a primary exemplar neuron (Specimen ID: `485909730`, *Mus musculus*, primary visual cortex, Layer 5 spiny pyramidal neuron).

**Preliminary Progress:** We have successfully established programmatic access to the Allen electrophysiology recordings (NWB format). Our preliminary feasibility study successfully extracted subthreshold hyperpolarizing sweeps (-110 pA to -10 pA) and suprathreshold depolarizing sweeps (+50 pA to +110 pA). Furthermore, we validated the baseline Passive Membrane Model on this neuron, extracting physically sensible parameters ($V_{rest} = -76.93$ mV, $R_m = 188.71\text{ M}\Omega$, $\tau_m = 18.92$ ms) that reconstruct the hyperpolarizing trajectory with high fidelity (RMSE $\approx 2.8$ mV). This established a solid foundation for the subsequent active models.

## 4. Experimental Design and Evaluation
Our experimental programme consists of four main evaluation stages:

*   **Experiment 1 — Passive/Subthreshold Response:** Validate the baseline RC membrane properties ($R_m$, $\tau_m$, $C_m$) using hyperpolarizing current steps. 
*   **Experiment 2 — F-I Relationship:** Compare the relationship between injected current amplitude and steady-state firing rate across the LIF, FHN, and HH models against the experimental rheobase (+50 to +70 pA) and graded firing rate response.
*   **Experiment 3 — Voltage & Spike Dynamics:** Quantitatively compare the simulated membrane-voltage trajectories (spike timing and action-potential dynamics) against empirical traces.
*   **Experiment 4 — Adaptation & Limitations:** Investigate spike-frequency adaptation, which was preliminarily observed in the real neuron (e.g., Sweep 34). We will test whether the selected models can reproduce this, and if not, discuss the missing biophysical mechanisms (e.g., slow $K^+$ currents).

**Evaluation Metrics & Validation:** Models will be evaluated using Root Mean Square Error (RMSE) for subthreshold voltage intervals, and by comparing spike counts and firing rates for suprathreshold steps. We will avoid circular fitting by estimating parameters on a calibration subset of sweeps and evaluating performance on held-out test sweeps where data volume permits. Computational complexity will be discussed qualitatively (number of state variables).

## 5. Expected Outcomes and Scope
We expect to precisely characterize the behavioural boundaries of each model. We hypothesize that the Passive model will be sufficient for subthreshold integration; LIF will adequately capture the linear regime of the F-I curve but fail at adaptation; FHN will reproduce nonlinear threshold dynamics; and HH will be required to accurately model the detailed spike trajectory. The scope is strictly limited to neuron-level electrophysiology (excluding morphology, transcriptomics, or network models).

## 6. Team Contributions and Timeline
To ensure a balanced workload, both team members will share research design, interpretation, and report writing duties while maintaining specific technical focuses.
*   **Student 1:** Neuron model implementation, mathematical formulation, simulation experiments, and parameter analysis.
*   **Student 2:** Allen electrophysiology data processing, experimental feature extraction, evaluation metrics, and visualization.

**Project Timeline:**
*   **By 30/09:** Proposal submission and project design.
*   **By 15/10:** Working baseline comparison using real data and initial model.
*   **October:** LIF, FHN, and HH implementation and controlled experiments.
*   **Early November:** Parameter analysis, validation, model comparison, and interpretation.
*   **Mid-November:** Final report, reproducible code/data package, README, and presentation.

---

**AI-Use Disclosure:** Generative AI tools were used to assist with project planning, debugging, documentation, and limited coding support. All modelling decisions, data validation, code verification, experimental interpretation, and final conclusions are reviewed and checked by the student authors.

**References**
1. Allen Institute for Brain Science (2015). Allen Cell Types Database. Available from: celltypes.brain-map.org.
2. Hodgkin, A. L., & Huxley, A. F. (1952). A quantitative description of membrane current and its application to conduction and excitation in nerve. *The Journal of physiology*, 117(4), 500-544.
3. FitzHugh, R. (1961). Impulses and physiological states in theoretical models of nerve membrane. *Biophysical journal*, 1(6), 445-466.
4. Lapicque, L. (1907). Recherches quantitatives sur l'excitation électrique des nerfs traitée comme une polarisation. *J. Physiol. Pathol. Gen.*, 9, 620-635. (Leaky Integrate-and-Fire formulation).
