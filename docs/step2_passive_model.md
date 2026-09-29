# Step 2: Passive Membrane Model

## Aim
The objective of this step is to estimate the passive properties (Resting Potential $V_{\text{rest}}$, Input Resistance $R_m$, Membrane Time Constant $\tau_m$, and Membrane Capacitance $C_m$) of the selected neuron using only the hyperpolarizing current sweeps (Sweeps 24-29). We aim to test whether a simple passive RC membrane model can reproduce the measured subthreshold voltage response and explicitly establish baseline parameters before moving to more complex active models (like Leaky Integrate-and-Fire).

## Equation
The standard passive membrane equation models the cell as a linear RC circuit:
$$C_m \frac{dV}{dt} = -\frac{V - V_{\text{rest}}}{R_m} + I(t)$$

Equivalently, written with the time constant $\tau_m = R_m C_m$:
$$\tau_m \frac{dV}{dt} = -(V - V_{\text{rest}}) + R_m I(t)$$

## Parameter Estimation

We systematically estimated the parameters across multiple subthreshold sweeps (-110 pA to -10 pA):

1. **Resting Potential ($V_{\text{rest}}$)**: Estimated by calculating the mean voltage over the 0.5-second pre-stimulus baseline window for each sweep.
2. **Input Resistance ($R_m$)**: For each sweep, we calculated the steady-state voltage deflection ($\Delta V = V_{\text{ss}} - V_{\text{rest}}$) near the end of the stimulus pulse. We then fit a linear regression across all hyperpolarizing sweeps to plot the **I-V Relationship**. The slope of this relationship directly provides the robust input resistance $R_m$.
3. **Membrane Time Constant ($\tau_m$)**: For each sweep, we fit an exponential decay function $V(t) = V_{\text{inf}} + (V_0 - V_{\text{inf}}) \exp(-t/\tau_m)$ to the first 100 ms of the voltage transient immediately after stimulus onset. We used the median of the high-quality fits (where $R^2 > 0.95$) to determine a robust $\tau_m$.
4. **Membrane Capacitance ($C_m$)**: Derived directly from the robust estimates using the physical relationship $C_m = \frac{\tau_m}{R_m}$.

## Results
The combined robust estimates for the neuron are:

- **Resting potential ($V_{\text{rest}}$)**: $-76.93\text{ mV}$
- **Input resistance ($R_m$)**: $188.71\text{ M}\Omega$
- **Membrane time constant ($\tau_m$)**: $18.92\text{ ms}$
- **Membrane capacitance ($C_m$)**: $100.28\text{ pF}$
- **I-V Relationship Linearity ($R^2$)**: $0.9679$

The individual sweep estimates and their variance are fully documented in `results/step2/passive_parameters_individual.csv`.

## Model Validation

We implemented the passive model using an explicit Euler numerical integration scheme with a timestep of $5\ \mu\text{s}$ (matching the $200,000\text{ Hz}$ recording frequency). 

We simulated the response to a $-110\text{ pA}$ current step (Sweep 24) and compared it directly to the experimental data.
The passive model accurately captures the charging trajectory and the steady-state deflection of the real neuron. 
- **Quantitative Error**: The Root Mean Square Error (RMSE) over the 1.0-second active stimulus interval was calculated as **$2.845\text{ mV}$**.

A sensitivity analysis was also performed (varying $\tau_m$ by 50%, 100%, and 200%), demonstrating how the initial transient shape heavily depends on an accurate time constant, while the final steady-state deflection remains dictated by $R_m$.

## Limitations

The passive RC model is fundamentally a linear system. Explicitly, it **cannot represent**:
- Action potential generation (spiking).
- Spike-frequency adaptation or threshold dynamics.
- Non-linear subthreshold dynamics (like Ih sag or active dendritic conductances), which are often visible as small deviations in real biological recordings even at hyperpolarized potentials. 

Because of this, the passive model alone is insufficient to explain the complex electrophysiological behaviours requested by the INCM project, requiring us to move forward to active spiking models.

## Reproducibility

To reproduce this analysis and generate the figures and CSVs:
```bash
python src/allen_data/passive_model.py
```
Or use the interactive notebook:
```bash
jupyter notebook notebooks/02_passive_membrane_analysis.ipynb
```
