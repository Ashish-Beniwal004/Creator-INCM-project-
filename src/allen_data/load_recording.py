"""Allen Cell Types Database electrophysiology data loading and validation module.

This module provides clean, reproducible functions to:
1. Locate and download electrophysiology NWB recordings from the Allen Cell Types Database.
2. Extract metadata and list available sweeps.
3. Load a specific sweep (returning time, stimulus, response, and sampling rate).
4. Validate recording data integrity (finite values, matching dimensions, positive sampling rate).
5. Generate publication-quality trace plots saved to results/step1/.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
from allensdk.core.cell_types_cache import CellTypesCache


def get_cache(cache_dir: str = "data/raw") -> CellTypesCache:
    """Initialize and return an Allen SDK CellTypesCache object pointing to cache_dir."""
    manifest_file = os.path.join(cache_dir, "manifest.json")
    os.makedirs(cache_dir, exist_ok=True)
    return CellTypesCache(manifest_file=manifest_file)


def download_cell_data(specimen_id: int, cache_dir: str = "data/raw"):
    """Download (if not already cached) and load the NWB electrophysiology dataset for a cell.

    Parameters
    ----------
    specimen_id : int
        The Allen specimen ID (e.g., 485909730).
    cache_dir : str
        Directory to store the manifest and NWB file.

    Returns
    -------
    NwbDataSet
        The Allen SDK NwbDataSet wrapper object.
    """
    ctc = get_cache(cache_dir)
    return ctc.get_ephys_data(specimen_id)


def get_cell_metadata(specimen_id: int, cache_dir: str = "data/raw") -> Dict[str, Any]:
    """Retrieve full metadata for a given specimen ID from the Allen Cell Types Database.

    Parameters
    ----------
    specimen_id : int
        The Allen specimen ID.
    cache_dir : str
        Directory where cell manifest is stored.

    Returns
    -------
    dict
        Cell metadata dictionary containing anatomy, species, layer, transgenic line, etc.
    """
    ctc = get_cache(cache_dir)
    cells = ctc.get_cells()
    for cell in cells:
        if cell["id"] == specimen_id:
            return cell
    raise ValueError(f"Specimen ID {specimen_id} not found in Allen Cell Types Database.")


def list_available_sweeps(specimen_id: int, cache_dir: str = "data/raw") -> List[Dict[str, Any]]:
    """List all available electrophysiology sweeps for a specimen.

    Parameters
    ----------
    specimen_id : int
        The Allen specimen ID.
    cache_dir : str
        Cache directory.

    Returns
    -------
    list of dict
        Metadata for each sweep, including sweep_number, stimulus_name, stimulus_amplitude, num_spikes.
    """
    ctc = get_cache(cache_dir)
    return ctc.get_ephys_sweeps(specimen_id)


def load_sweep(
    data_set, sweep_number: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Load a specific sweep from an NwbDataSet.

    Parameters
    ----------
    data_set : NwbDataSet
        The dataset returned by download_cell_data.
    sweep_number : int
        The sweep number to extract.

    Returns
    -------
    time : np.ndarray
        Time vector in seconds.
    stimulus : np.ndarray
        Injected stimulus current in Amperes (A).
    response : np.ndarray
        Membrane voltage response in Volts (V).
    sampling_rate : float
        Sampling frequency in Hertz (Hz).
    """
    sweep_data = data_set.get_sweep(sweep_number)
    stimulus = sweep_data["stimulus"]
    response = sweep_data["response"]
    sampling_rate = float(sweep_data["sampling_rate"])

    # Construct the time vector from sample count and sampling rate
    time = np.arange(len(response), dtype=np.float64) / sampling_rate

    # Run data validation
    validate_recording(time, stimulus, response, sampling_rate)

    return time, stimulus, response, sampling_rate


def validate_recording(
    time: np.ndarray,
    stimulus: np.ndarray,
    response: np.ndarray,
    sampling_rate: float,
) -> Dict[str, Any]:
    """Validate data integrity of the electrophysiology sweep.

    Checks:
    - stimulus and response are non-empty
    - sampling_rate is positive
    - time vector length matches response and stimulus length
    - all values are finite (no NaNs or Infs)
    - stimulus has non-zero injection

    Returns
    -------
    dict
        Summary of validation metrics.
    """
    if stimulus is None or len(stimulus) == 0:
        raise ValueError("Validation failed: Stimulus array is empty or None.")
    if response is None or len(response) == 0:
        raise ValueError("Validation failed: Response array is empty or None.")
    if sampling_rate <= 0:
        raise ValueError(f"Validation failed: Invalid sampling rate {sampling_rate} Hz.")
    if len(stimulus) != len(response):
        raise ValueError(
            f"Validation failed: Stimulus length ({len(stimulus)}) does not match response length ({len(response)})."
        )
    if len(time) != len(response):
        raise ValueError(
            f"Validation failed: Time length ({len(time)}) does not match response length ({len(response)})."
        )
    if not np.all(np.isfinite(stimulus)):
        raise ValueError("Validation failed: Non-finite values detected in stimulus.")
    if not np.all(np.isfinite(response)):
        raise ValueError("Validation failed: Non-finite values detected in response.")

    stim_max_abs = np.max(np.abs(stimulus))
    if stim_max_abs < 1e-15:
        raise ValueError("Validation warning/failed: Selected sweep has virtually zero stimulus.")

    return {
        "valid": True,
        "num_samples": len(response),
        "duration_seconds": len(response) / sampling_rate,
        "sampling_rate_hz": sampling_rate,
        "stimulus_range_A": (float(stimulus.min()), float(stimulus.max())),
        "response_range_V": (float(response.min()), float(response.max())),
    }


def detect_spikes_basic(
    response: np.ndarray,
    sampling_rate: float,
    threshold_v: float = -0.020,
    refractory_ms: float = 2.0,
) -> Tuple[int, np.ndarray]:
    """Basic upward threshold-crossing spike detector for preliminary data verification.

    Parameters
    ----------
    response : np.ndarray
        Membrane voltage in Volts.
    sampling_rate : float
        Sampling frequency in Hz.
    threshold_v : float
        Threshold voltage in Volts (default: -0.020 V = -20 mV).
    refractory_ms : float
        Minimum lockout window between detected spikes in milliseconds.

    Returns
    -------
    spike_count : int
        Number of detected action potentials.
    spike_times : np.ndarray
        Array of spike onset/peak times in seconds.
    """
    refractory_samples = int((refractory_ms / 1000.0) * sampling_rate)
    above_thresh = response > threshold_v

    spike_indices = []
    i = 1
    while i < len(response):
        if above_thresh[i] and not above_thresh[i - 1]:
            # Found upward crossing, find peak within the next 2 ms
            end_search = min(i + refractory_samples, len(response))
            peak_idx = i + int(np.argmax(response[i:end_search]))
            spike_indices.append(peak_idx)
            i = peak_idx + refractory_samples
        else:
            i += 1

    spike_indices_arr = np.array(spike_indices, dtype=int)
    spike_times = spike_indices_arr / sampling_rate
    return len(spike_indices), spike_times


def plot_and_save_traces(
    time: np.ndarray,
    stimulus: np.ndarray,
    response: np.ndarray,
    specimen_id: int,
    sweep_number: int,
    output_dir: str = "results/step1",
    stimulus_unit_display: str = "pA",
    response_unit_display: str = "mV",
) -> Tuple[str, str]:
    """Generate and save the two required Step-1 figures:

    1. Injected Current vs Time (results/step1/allen_current_trace.png)
    2. Membrane Voltage vs Time (results/step1/allen_voltage_trace.png)

    Parameters
    ----------
    time : np.ndarray
        Time in seconds.
    stimulus : np.ndarray
        Injected current in Amperes.
    response : np.ndarray
        Membrane potential in Volts.
    specimen_id : int
        Allen specimen identifier.
    sweep_number : int
        Sweep number plotted.
    output_dir : str
        Directory to save figures.
    stimulus_unit_display : str
        Display unit for current ('pA' or 'nA' or 'A').
    response_unit_display : str
        Display unit for voltage ('mV' or 'V').

    Returns
    -------
    current_fig_path : str
        File path to saved injected current figure.
    voltage_fig_path : str
        File path to saved membrane voltage figure.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Scaling
    if stimulus_unit_display == "pA":
        stim_plot = stimulus * 1e12
        stim_unit_label = "Current (pA)"
    elif stimulus_unit_display == "nA":
        stim_plot = stimulus * 1e9
        stim_unit_label = "Current (nA)"
    else:
        stim_plot = stimulus
        stim_unit_label = "Current (A)"

    if response_unit_display == "mV":
        resp_plot = response * 1e3
        resp_unit_label = "Membrane Potential (mV)"
    else:
        resp_plot = response
        resp_unit_label = "Membrane Potential (V)"

    # Plot styling
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.titlesize": 14,
    })

    # -------------------------------------------------------------
    # Figure 1: Injected Current vs Time
    # -------------------------------------------------------------
    fig1, ax1 = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax1.plot(time, stim_plot, color="#1f77b4", linewidth=1.2, label=f"Sweep {sweep_number} Stimulus")
    ax1.set_xlabel("Time (s)", fontweight="semibold")
    ax1.set_ylabel(stim_unit_label, fontweight="semibold")
    ax1.set_title(
        f"Injected Current vs Time — Specimen {specimen_id} (Sweep {sweep_number})",
        fontweight="bold",
        pad=10,
    )
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.set_xlim(0, time[-1])
    ax1.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()

    current_fig_path = os.path.join(output_dir, "allen_current_trace.png")
    fig1.savefig(current_fig_path, dpi=300)
    plt.close(fig1)

    # -------------------------------------------------------------
    # Figure 2: Membrane Voltage vs Time
    # -------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax2.plot(time, resp_plot, color="#d62728", linewidth=0.9, label=f"Sweep {sweep_number} Voltage Response")
    ax2.set_xlabel("Time (s)", fontweight="semibold")
    ax2.set_ylabel(resp_unit_label, fontweight="semibold")
    ax2.set_title(
        f"Membrane Voltage vs Time — Specimen {specimen_id} (Sweep {sweep_number})",
        fontweight="bold",
        pad=10,
    )
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.set_xlim(0, time[-1])
    ax2.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()

    voltage_fig_path = os.path.join(output_dir, "allen_voltage_trace.png")
    fig2.savefig(voltage_fig_path, dpi=300)
    plt.close(fig2)

    return current_fig_path, voltage_fig_path


def main():
    """Main execution script for Step 1 data feasibility demo."""
    specimen_id = 485909730
    sweep_number = 34
    cache_dir = "data/raw"
    output_dir = "results/step1"

    print("=" * 70)
    print("INCM Step 1: Allen Cell Types Data Feasibility & First Neuron")
    print("=" * 70)

    # 1. Fetch metadata
    print(f"\n[1/5] Fetching cell metadata for specimen ID {specimen_id}...")
    cell_meta = get_cell_metadata(specimen_id, cache_dir=cache_dir)
    print(f"  - Specimen ID       : {cell_meta.get('id')}")
    print(f"  - Cell Name         : {cell_meta.get('name')}")
    print(f"  - Species           : {cell_meta.get('species')}")
    print(f"  - Brain Region      : {cell_meta.get('structure_area_abbrev')} (Area ID: {cell_meta.get('structure_area_id')})")
    print(f"  - Cortical Layer    : Layer {cell_meta.get('structure_layer_name')}")
    print(f"  - Dendrite Type     : {cell_meta.get('dendrite_type')}")
    print(f"  - Transgenic Line   : {cell_meta.get('transgenic_line')}")

    # 2. List sweeps
    print(f"\n[2/5] Inspecting available electrophysiology sweeps...")
    sweeps = list_available_sweeps(specimen_id, cache_dir=cache_dir)
    long_square_sweeps = [s for s in sweeps if "Long Square" in s.get("stimulus_name", "")]
    print(f"  - Total sweeps recorded: {len(sweeps)}")
    print(f"  - Long Square (step) sweeps: {len(long_square_sweeps)}")
    for s in long_square_sweeps:
        sw_num = s["sweep_number"]
        amp = s.get("stimulus_absolute_amplitude")
        spk = s.get("num_spikes")
        marker = " <--- SELECTED" if sw_num == sweep_number else ""
        print(f"    - Sweep {sw_num:2d}: stimulus_amp = {amp:7.1f} pA, spikes = {str(spk):4s}{marker}")

    # 3. Download / Load NWB data
    print(f"\n[3/5] Loading NWB recording dataset for specimen {specimen_id}...")
    data_set = download_cell_data(specimen_id, cache_dir=cache_dir)

    print(f"\n[4/5] Loading and validating Sweep {sweep_number}...")
    time, stimulus, response, sampling_rate = load_sweep(data_set, sweep_number)
    val_report = validate_recording(time, stimulus, response, sampling_rate)

    duration = val_report["duration_seconds"]
    n_samples = val_report["num_samples"]
    stim_min_pa = val_report["stimulus_range_A"][0] * 1e12
    stim_max_pa = val_report["stimulus_range_A"][1] * 1e12
    resp_min_mv = val_report["response_range_V"][0] * 1e3
    resp_max_mv = val_report["response_range_V"][1] * 1e3

    print(f"  - Sampling Rate     : {sampling_rate:.1f} Hz (5 us time step)")
    print(f"  - Sample Count      : {n_samples:,} points")
    print(f"  - Duration          : {duration:.3f} s")
    print(f"  - Stimulus Range    : [{stim_min_pa:.2f}, {stim_max_pa:.2f}] pA")
    print(f"  - Voltage Range     : [{resp_min_mv:.2f}, {resp_max_mv:.2f}] mV")

    # 4. Basic spike count check
    spk_count_algo, spk_times = detect_spikes_basic(response, sampling_rate, threshold_v=-0.020)
    allen_spk_count = next(
        (s.get("num_spikes") for s in sweeps if s["sweep_number"] == sweep_number), None
    )
    print(f"  - Allen Official Spikes : {allen_spk_count}")
    print(f"  - Verified Spikes (> -20mV): {spk_count_algo}")

    # 5. Generate and save figures
    print(f"\n[5/5] Generating publication-quality figures in '{output_dir}'...")
    curr_path, volt_path = plot_and_save_traces(
        time, stimulus, response, specimen_id, sweep_number, output_dir=output_dir
    )
    print(f"  - Saved: {curr_path}")
    print(f"  - Saved: {volt_path}")

    print("\n" + "=" * 70)
    print("STEP 1 PIPELINE VERIFICATION: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    main()
