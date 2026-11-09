import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import socket

# Hard network timeout to keep processing fast
socket.setdefaulttimeout(12)

# 1. Load unstudied candidates catalog
df = pd.read_csv("unstudied_candidates.csv")
os.makedirs("candidate_plots", exist_ok=True)

# Filter out known bad/empty IDs
bad_ids = ['194258999', '380157588']
df = df[~df['tic_id'].astype(str).str.contains('|'.join(bad_ids))]

# 2. Select next batch of 50 unstudied targets to scan
targets_to_scan = df.iloc[10:60]

print(f"Starting batch scan for {len(targets_to_scan)} unstudied targets...\n")

for idx, row in targets_to_scan.iterrows():
    raw_id = str(row['tic_id']).replace('TIC', '').strip()
    tic_id = f"TIC {int(float(raw_id))}"
    
    print(f"[{idx+1}/{len(targets_to_scan)}] Processing {tic_id}...")
    
    try:
        # Query MAST for TESS Light Curves
        search_results = lk.search_lightcurve(tic_id, mission="TESS")
        
        if len(search_results) == 0:
            print(f"   --> No TESS light curves found for {tic_id}. Skipping.\n")
            continue
            
        print(f"   --> Found {len(search_results)} data sets. Downloading first sector...")
        
        # Download first dataset safely
        lc = search_results[0].download(quality_bitmask="default")
        
        if lc is None:
            print(f"   --> Empty light curve data for {tic_id}. Skipping.\n")
            continue
            
        # Clean and flatten baseline
        clean_lc = lc.remove_outliers(sigma=5)
        flat_lc = clean_lc.flatten(window_length=101)
        
        # Fast BLS search grid (1500 evaluation steps)
        period_grid = np.linspace(0.5, 12, 1500)
        bls = flat_lc.to_periodogram(method="bls", period=period_grid)
        
        planet_p = bls.period_at_max_power
        planet_t0 = bls.transit_time_at_max_power
        max_power = bls.max_power.value
        
        # Power threshold filter: Ignore random scatter noise (Power < 12)
        if max_power < 12.0:
            print(f"   --> NOISE: Period = {planet_p.value:.4f} d | Max Power = {max_power:.2f} (Below signal threshold)\n")
            continue

        print(f"   --> !!! SIGNAL DETECTED !!! Period = {planet_p.value:.4f} d | Max Power = {max_power:.2f}")
        
        # Phase-fold and generate plot ONLY for high-power signals
        folded_lc = flat_lc.fold(period=planet_p, epoch_time=planet_t0)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        flat_lc.scatter(ax=ax1, s=1)
        ax1.set_title(f"Cleaned Light Curve: {tic_id} (R_star = {row['st_rad']} R_sun)")
        
        folded_lc.scatter(ax=ax2, s=2, color='black', alpha=0.5)
        folded_lc.bin(time_bin_size=0.01).plot(ax=ax2, color='red', lw=2, label='Binned Profile')
        ax2.set_xlim(-0.3, 0.3)
        ax2.set_title(f"Phase-Folded Signal (Period = {planet_p.value:.4f} d | Power = {max_power:.2f})")
        
        filename = f"candidate_plots/{tic_id.replace(' ', '_')}_scan.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close(fig)
        print(f"   --> Candidate plot saved to {filename}\n")
        
    except Exception as e:
        print(f"   --> Skipped {tic_id}: {e}\n")

print("Batch scan complete! Any candidate plots with Power > 12 are in 'candidate_plots'.")
