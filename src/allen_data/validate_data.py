"""Validation script for INCM Step 1.
Extracts sweep metadata, creates sweep_summary.csv, 
generates experimental F-I curve, ISI plot, and passive sweeps overview.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from allensdk.core.cell_types_cache import CellTypesCache
import json

def detect_spikes(time, response, threshold_v=-0.020, min_peak_distance=0.002):
    """Simple peak detection for spikes."""
    spikes = []
    spike_times = []
    dt = time[1] - time[0]
    min_dist_idx = int(min_peak_distance / dt)
    
    above = response > threshold_v
    i = 1
    while i < len(response):
        if above[i] and not above[i-1]:
            # find peak in local window
            window_end = min(i + min_dist_idx, len(response))
            peak_idx = i + np.argmax(response[i:window_end])
            spikes.append(peak_idx)
            spike_times.append(time[peak_idx])
            i = peak_idx + min_dist_idx
        else:
            i += 1
    return np.array(spike_times)

def main():
    specimen_id = 485909730
    cache_dir = "data/raw"
    results_dir = "results/step1"
    os.makedirs(results_dir, exist_ok=True)
    
    ctc = CellTypesCache(manifest_file=os.path.join(cache_dir, "manifest.json"))
    data_set = ctc.get_ephys_data(specimen_id)
    all_sweeps = ctc.get_ephys_sweeps(specimen_id)
    
    target_sweeps = [24, 25, 26, 27, 28, 29, 32, 33, 34, 35]
    
    summary_data = []
    quality_issues = []
    
    # Setup for passive sweeps plot
    fig_passive, ax_passive = plt.subplots(figsize=(10, 5), dpi=300)
    
    # Store F-I data
    currents_pA = []
    firing_rates_Hz = []
    
    for sw_num in target_sweeps:
        # Get metadata
        meta = next((s for s in all_sweeps if s['sweep_number'] == sw_num), None)
        if not meta:
            continue
            
        # Get raw data
        sweep_data = data_set.get_sweep(sw_num)
        stimulus = sweep_data['stimulus']
        response = sweep_data['response']
        sr = float(sweep_data['sampling_rate'])
        time = np.arange(len(response)) / sr
        
        # Validation checks
        if not np.all(np.isfinite(stimulus)):
            quality_issues.append(f"Sweep {sw_num}: Non-finite values in stimulus")
        if not np.all(np.isfinite(response)):
            quality_issues.append(f"Sweep {sw_num}: Non-finite values in response")
        if len(stimulus) != len(response):
            quality_issues.append(f"Sweep {sw_num}: Length mismatch (stim={len(stimulus)}, resp={len(response)})")
            
        amp_pA = meta.get('stimulus_absolute_amplitude', 0.0)
        stim_start_s = meta.get('stimulus_start_time', 0.0)
        duration_active_s = meta.get('stimulus_duration', 1.0)
        stim_end_s = stim_start_s + duration_active_s
            
        duration_s = len(response) / sr
        
        # Verify spikes
        spike_times = detect_spikes(time, response, threshold_v=-0.020)
        spike_count = len(spike_times)
        
        # Baseline check (first 0.5s)
        baseline = response[:int(0.5 * sr)]
        baseline_std = np.std(baseline) * 1e3 # in mV
        if baseline_std > 1.0: # arbitrary threshold for stable baseline
            quality_issues.append(f"Sweep {sw_num}: Unstable baseline (std={baseline_std:.2f}mV)")
            
        summary_data.append({
            'sweep_number': sw_num,
            'stimulus_pA': round(amp_pA, 2),
            'stimulus_start_s': round(stim_start_s, 4),
            'stimulus_end_s': round(stim_end_s, 4),
            'duration_s': round(duration_s, 4),
            'spike_count': spike_count,
            'official_spike_count': meta.get('num_spikes')
        })
        
        # F-I data (only for sweeps that were intended as depolarization >= 0)
        if amp_pA >= 0:
            currents_pA.append(amp_pA)
            if duration_active_s > 0:
                firing_rates_Hz.append(spike_count / duration_active_s)
            else:
                firing_rates_Hz.append(0.0)
                
        # Passive sweeps plot
        if 24 <= sw_num <= 29:
            ax_passive.plot(time, response * 1e3, label=f"Sweep {sw_num} ({amp_pA:.0f} pA)")
            
        # ISI analysis for sweep 34
        if sw_num == 34:
            if spike_count > 1:
                isis = np.diff(spike_times) * 1000 # in ms
                spike_numbers = np.arange(1, len(isis) + 1)
                
                fig_isi, ax_isi = plt.subplots(figsize=(8, 4), dpi=300)
                ax_isi.plot(spike_numbers, isis, marker='o', linestyle='-', color='indigo')
                ax_isi.set_xlabel('Interval Number (i-th to (i+1)-th spike)', fontweight='bold')
                ax_isi.set_ylabel('Inter-Spike Interval (ms)', fontweight='bold')
                ax_isi.set_title(f'Adaptation: Inter-Spike Intervals for Sweep 34 (+90 pA)', fontweight='bold')
                ax_isi.grid(True, linestyle='--', alpha=0.5)
                ax_isi.set_xticks(spike_numbers)
                plt.tight_layout()
                fig_isi.savefig(os.path.join(results_dir, "sweep34_isi.png"))
                plt.close(fig_isi)
                
                # Check adaptation statistically (positive slope in ISI)
                if len(isis) > 2:
                    slope, _ = np.polyfit(spike_numbers, isis, 1)
                    if slope > 0:
                        print(f"Sweep 34: Spike frequency adaptation OBSERVED (ISI increases by ~{slope:.2f} ms per spike)")
                    else:
                        print("Sweep 34: No clear adaptation observed.")
            else:
                print("Sweep 34: Not enough spikes for ISI analysis.")

    # Save summary CSV
    df = pd.DataFrame(summary_data)
    df.to_csv(os.path.join(results_dir, "sweep_summary.csv"), index=False)
    
    # Save Passive Plot
    ax_passive.set_xlabel("Time (s)", fontweight='bold')
    ax_passive.set_ylabel("Membrane Potential (mV)", fontweight='bold')
    ax_passive.set_title("Hyperpolarizing Sweeps (24-29)", fontweight='bold')
    ax_passive.set_xlim(0.8, 2.5) # Zoom in on stimulus window + recovery
    ax_passive.grid(True, linestyle='--', alpha=0.5)
    ax_passive.legend(loc='lower right', framealpha=0.9)
    fig_passive.tight_layout()
    fig_passive.savefig(os.path.join(results_dir, "passive_sweeps_overview.png"))
    plt.close(fig_passive)
    
    # Save F-I Plot
    fig_fi, ax_fi = plt.subplots(figsize=(8, 5), dpi=300)
    currents_pA = np.array(currents_pA)
    firing_rates_Hz = np.array(firing_rates_Hz)
    
    sub_mask = firing_rates_Hz == 0
    supra_mask = firing_rates_Hz > 0
    
    ax_fi.plot(currents_pA, firing_rates_Hz, color='gray', linestyle='--', zorder=1)
    ax_fi.scatter(currents_pA[sub_mask], firing_rates_Hz[sub_mask], color='black', label='Subthreshold', zorder=2)
    ax_fi.scatter(currents_pA[supra_mask], firing_rates_Hz[supra_mask], color='red', label='Suprathreshold', zorder=2)
    
    ax_fi.set_xlabel("Injected Current (pA)", fontweight='bold')
    ax_fi.set_ylabel("Firing Rate (Hz)", fontweight='bold')
    ax_fi.set_title("Initial Experimental F-I Curve", fontweight='bold')
    ax_fi.grid(True, linestyle='--', alpha=0.5)
    ax_fi.legend()
    fig_fi.tight_layout()
    fig_fi.savefig(os.path.join(results_dir, "initial_fi_curve.png"))
    plt.close(fig_fi)
    
    # Print reports
    print("=== SWEEP SUMMARY ===")
    print(df.to_string())
    
    print("\n=== QUALITY ISSUES ===")
    if quality_issues:
        for q in quality_issues:
            print("-", q)
    else:
        print("No quality issues detected. Data is clean.")

if __name__ == "__main__":
    main()
