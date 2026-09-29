"""
Passive Membrane Model Analysis
Fits linear RC subthreshold response (Rm, tau_m, Cm) using hyperpolarizing sweeps.
Simulates passive membrane and compares to experimental data.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress
from allensdk.core.cell_types_cache import CellTypesCache

def estimate_resting_potential(time, voltage, stim_start_s, pre_stim_window=0.5):
    """Calculate mean and std of V_rest in the pre-stimulus baseline."""
    mask = (time >= stim_start_s - pre_stim_window) & (time < stim_start_s)
    v_baseline = voltage[mask]
    return np.mean(v_baseline), np.std(v_baseline)

def estimate_steady_state(time, voltage, stim_start_s, stim_end_s, tail_window=0.2):
    """Estimate steady state voltage near the end of the stimulus."""
    mask = (time > stim_end_s - tail_window) & (time <= stim_end_s)
    v_ss = voltage[mask]
    return np.mean(v_ss)

def exp_decay(t, v_inf, v_0, tau):
    """Exponential decay function for fitting."""
    return v_inf + (v_0 - v_inf) * np.exp(-t / tau)

def fit_membrane_time_constant(time, voltage, stim_start_s, stim_end_s, v_0, v_ss):
    """Fit exponential curve to the initial transient of the hyperpolarizing step."""
    # Use first 100ms of the pulse for fitting the transient
    mask = (time > stim_start_s) & (time < stim_start_s + 0.1)
    t_fit = time[mask] - stim_start_s # relative time
    v_fit = voltage[mask]
    
    # bounds for tau: 1ms to 200ms
    bounds = ([-np.inf, -np.inf, 0.001], [np.inf, np.inf, 0.2])
    p0 = [v_ss, v_0, 0.015] # initial guesses: v_inf=v_ss, v_0=v_0, tau=15ms
    
    try:
        popt, pcov = curve_fit(exp_decay, t_fit, v_fit, p0=p0, bounds=bounds)
        v_inf_fit, v_0_fit, tau_fit = popt
        # calculate R^2
        residuals = v_fit - exp_decay(t_fit, *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((v_fit - np.mean(v_fit))**2)
        r_squared = 1 - (ss_res / ss_tot)
        return tau_fit, r_squared
    except Exception as e:
        print(f"Curve fit failed: {e}")
        return np.nan, np.nan

def simulate_passive_membrane(time, stimulus, v_rest, r_m, tau_m):
    """
    Simulate passive membrane using explicit Euler method.
    tau_m dV/dt = -(V - V_rest) + R_m I(t)
    V(t+dt) = V(t) + dt * (-(V(t) - V_rest) + R_m * I(t)) / tau_m
    """
    dt = time[1] - time[0]
    v_sim = np.zeros_like(time)
    v_sim[0] = v_rest
    
    for i in range(1, len(time)):
        dv = (-(v_sim[i-1] - v_rest) + r_m * stimulus[i-1]) / tau_m
        v_sim[i] = v_sim[i-1] + dt * dv
        
    return v_sim

def calculate_rmse(v_exp, v_sim, time, start_s, end_s):
    """Calculate RMSE during a specific time interval."""
    mask = (time >= start_s) & (time <= end_s)
    rmse = np.sqrt(np.mean((v_exp[mask] - v_sim[mask])**2))
    return rmse

def main():
    specimen_id = 485909730
    cache_dir = "data/raw"
    results_dir = "results/step2"
    os.makedirs(results_dir, exist_ok=True)
    
    ctc = CellTypesCache(manifest_file=os.path.join(cache_dir, "manifest.json"))
    data_set = ctc.get_ephys_data(specimen_id)
    all_sweeps = ctc.get_ephys_sweeps(specimen_id)
    
    # Sweeps 24-29 are hyperpolarizing
    target_sweeps = [24, 25, 26, 27, 28, 29]
    
    results = []
    currents_A = []
    delta_vs_V = []
    
    for sw_num in target_sweeps:
        meta = next((s for s in all_sweeps if s['sweep_number'] == sw_num), None)
        sweep_data = data_set.get_sweep(sw_num)
        
        stimulus = sweep_data['stimulus'] # Amperes
        response = sweep_data['response'] # Volts
        sr = float(sweep_data['sampling_rate'])
        time = np.arange(len(response)) / sr
        
        stim_start_s = meta.get('stimulus_start_time', 0.0)
        duration_active_s = meta.get('stimulus_duration', 1.0)
        stim_end_s = stim_start_s + duration_active_s
        amp_pA = meta.get('stimulus_absolute_amplitude', 0.0)
        amp_A = amp_pA * 1e-12
        
        # 1. Resting potential
        v_rest, v_rest_std = estimate_resting_potential(time, response, stim_start_s)
        
        # 2. Steady state and delta V
        v_ss = estimate_steady_state(time, response, stim_start_s, stim_end_s)
        delta_v = v_ss - v_rest
        
        # 3. Input resistance (R_m = delta_V / I)
        r_m_ohms = delta_v / amp_A if amp_A != 0 else np.nan
        r_m_mohms = r_m_ohms * 1e-6
        
        # 4. Time constant
        tau_s, tau_r2 = fit_membrane_time_constant(time, response, stim_start_s, stim_end_s, v_rest, v_ss)
        
        currents_A.append(amp_A)
        delta_vs_V.append(delta_v)
        
        results.append({
            'sweep_number': sw_num,
            'stimulus_pA': amp_pA,
            'v_rest_mV': v_rest * 1000,
            'v_rest_std_mV': v_rest_std * 1000,
            'steady_state_voltage_mV': v_ss * 1000,
            'delta_v_mV': delta_v * 1000,
            'input_resistance_MOhm': r_m_mohms,
            'tau_ms': tau_s * 1000,
            'tau_fit_quality': tau_r2
        })
    
    df = pd.DataFrame(results)
    
    # Combined estimates
    # For robust estimate, we will use the linear regression slope of IV curve for R_m
    # For tau_m, we will use the median of high-quality fits to reject outliers
    # For V_rest, average across all sweeps
    
    # IV Curve Analysis
    currents_pA = np.array(currents_A) * 1e12
    delta_vs_mV = np.array(delta_vs_V) * 1000
    
    res = linregress(currents_pA, delta_vs_mV) # x in pA, y in mV -> slope is mV/pA = GOhms
    slope_gohms = res.slope
    r_m_robust_mohms = slope_gohms * 1000 # GOhms to MOhms
    r_m_robust_ohms = r_m_robust_mohms * 1e6
    r2_iv = res.rvalue**2
    
    tau_robust_ms = df[df['tau_fit_quality'] > 0.95]['tau_ms'].median()
    tau_robust_s = tau_robust_ms / 1000
    
    c_m_robust_f = tau_robust_s / r_m_robust_ohms
    c_m_robust_pf = c_m_robust_f * 1e12
    
    v_rest_robust_v = df['v_rest_mV'].mean() / 1000
    
    summary = {
        'R_m_MOhm': r_m_robust_mohms,
        'tau_m_ms': tau_robust_ms,
        'C_m_pF': c_m_robust_pf,
        'V_rest_mV': v_rest_robust_v * 1000,
        'IV_R2': r2_iv
    }
    
    # Save parameters
    df.to_csv(os.path.join(results_dir, "passive_parameters_individual.csv"), index=False)
    pd.DataFrame([summary]).to_csv(os.path.join(results_dir, "passive_parameters_summary.csv"), index=False)
    
    # Plot IV Curve
    fig_iv, ax_iv = plt.subplots(figsize=(6, 5), dpi=300)
    ax_iv.scatter(currents_pA, delta_vs_mV, color='black', label='Data')
    x_fit = np.array([min(currents_pA), max(currents_pA)])
    y_fit = res.intercept + res.slope * x_fit
    ax_iv.plot(x_fit, y_fit, color='red', linestyle='--', label=f'Fit (R²={r2_iv:.4f})')
    ax_iv.set_xlabel('Injected Current (pA)', fontweight='bold')
    ax_iv.set_ylabel('Steady-State Voltage Deflection (mV)', fontweight='bold')
    ax_iv.set_title('Passive Membrane I-V Relationship', fontweight='bold')
    ax_iv.grid(True, linestyle='--', alpha=0.5)
    ax_iv.legend()
    fig_iv.tight_layout()
    fig_iv.savefig(os.path.join(results_dir, "passive_iv_curve.png"))
    plt.close(fig_iv)
    
    # Passive Model vs Experiment (Sweep 24: -110 pA)
    sw_test = 24
    meta_test = next((s for s in all_sweeps if s['sweep_number'] == sw_test), None)
    sweep_test_data = data_set.get_sweep(sw_test)
    stim_test = sweep_test_data['stimulus']
    resp_test = sweep_test_data['response']
    sr = float(sweep_test_data['sampling_rate'])
    time_test = np.arange(len(resp_test)) / sr
    stim_start_s = meta_test.get('stimulus_start_time', 0.0)
    duration_active_s = meta_test.get('stimulus_duration', 1.0)
    
    v_sim = simulate_passive_membrane(time_test, stim_test, v_rest_robust_v, r_m_robust_ohms, tau_robust_s)
    rmse_test = calculate_rmse(resp_test, v_sim, time_test, stim_start_s, stim_start_s + duration_active_s)
    
    fig_sim, ax_sim = plt.subplots(figsize=(8, 5), dpi=300)
    ax_sim.plot(time_test, resp_test * 1000, color='black', label='Experiment')
    ax_sim.plot(time_test, v_sim * 1000, color='red', linestyle='--', label='Passive Model')
    ax_sim.set_xlim(0.8, 2.5)
    ax_sim.set_xlabel('Time (s)', fontweight='bold')
    ax_sim.set_ylabel('Membrane Potential (mV)', fontweight='bold')
    ax_sim.set_title(f'Passive Model vs Experiment (Sweep {sw_test}: {meta_test.get("stimulus_absolute_amplitude")} pA)', fontweight='bold')
    ax_sim.grid(True, linestyle='--', alpha=0.5)
    ax_sim.legend()
    fig_sim.tight_layout()
    fig_sim.savefig(os.path.join(results_dir, "passive_model_vs_experiment.png"))
    plt.close(fig_sim)
    
    # Sensitivity Analysis
    fig_sens, ax_sens = plt.subplots(figsize=(8, 5), dpi=300)
    ax_sens.plot(time_test, resp_test * 1000, color='black', label='Experiment', alpha=0.5)
    
    tau_variations = [0.5, 1.0, 2.0] # 50%, 100%, 200% of tau
    colors = ['blue', 'red', 'green']
    
    for factor, color in zip(tau_variations, colors):
        v_sim_sens = simulate_passive_membrane(time_test, stim_test, v_rest_robust_v, r_m_robust_ohms, tau_robust_s * factor)
        ax_sens.plot(time_test, v_sim_sens * 1000, color=color, linestyle='--', label=f'Model (tau = {factor*100:.0f}%)')
        
    ax_sens.set_xlim(0.9, 1.3) # Zoom in on the start of the pulse
    ax_sens.set_xlabel('Time (s)', fontweight='bold')
    ax_sens.set_ylabel('Membrane Potential (mV)', fontweight='bold')
    ax_sens.set_title(f'Sensitivity Analysis: Varying $\\tau_m$ (Sweep {sw_test})', fontweight='bold')
    ax_sens.grid(True, linestyle='--', alpha=0.5)
    ax_sens.legend()
    fig_sens.tight_layout()
    fig_sens.savefig(os.path.join(results_dir, "passive_parameter_sensitivity.png"))
    plt.close(fig_sens)
    
    print("=== PASSIVE PARAMETER SUMMARY ===")
    print(f"V_rest: {v_rest_robust_v*1000:.2f} mV")
    print(f"R_m: {r_m_robust_mohms:.2f} MOhm")
    print(f"tau_m: {tau_robust_ms:.2f} ms")
    print(f"C_m: {c_m_robust_pf:.2f} pF")
    print(f"I-V curve R^2: {r2_iv:.4f}")
    print(f"RMSE (Sweep {sw_test} active interval): {rmse_test*1000:.3f} mV")

if __name__ == "__main__":
    main()
