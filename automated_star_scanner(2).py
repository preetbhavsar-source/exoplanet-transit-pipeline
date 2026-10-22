import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os  # for being able to actually access my operating system to access files and make changes
import socket # allows for managment accross diffrent servers

socket.setdefaulttimeout(12) # 12 second timer on all incoming network requests

df = pd.read_csv("unstudied_candidates.csv") # reads my csv of my candidate dataset
os.makedirs("candidate_plots", exist_ok=True) 

bad_ids = ['194258999', '380157588'] # so these are "bad_ids", explained in the debug notes in the very bottom
df = df[~df['tic_id'].astype(str).str.contains('|'.join(bad_ids))]

targets_to_scan = df.iloc[10:60] # scans 50 targets so my computer doesn't crash

for idx, row in targets_to_scan.iterrows(): #start the loop to clean the ids
    raw_id = str(row['tic_id']).replace('TIC', '').strip() #replace the "tic" in the ids 
    tic_id = f"TIC {int(float(raw_id))}" 

try:
        # query MAST for TESS Light Curves
        search_results = lk.search_lightcurve(tic_id, mission="TESS")
        
        if len(search_results) == 0: # checks for light curves and if there are any
            print(f"   --> No TESS light curves found for {tic_id}. Skipping.\n")
            continue
            
        # download first dataset safely
        lc = search_results[0].download(quality_bitmask="default")
        
        if lc is None:
            print(f"   --> Empty light curve data for {tic_id}. Skipping.\n")
            continue
                        # clean and flatten baseline
            clean_lc = lc.remove_outliers(sigma=5)  # removes extreme noise spikes or outliers so it doesn't skew
            flat_lc = clean_lc.flatten(window_length=101) #uses lightcurves flatten method to remove long term stellar variablility. Basically
                                                            # flatten applies a Slatvitsky-Golay Filter to the data which fits a smooth curve through the 
                                                            # overall trends in starlight and then divides by the orginal light curve by the smooth fit and this all 
                                                            # prevents other brightness changes. The 101 window length is the period of the filter
                                                            # 101 candences is equal to 3.3 hours of obersvation by TESS
                                                            # which is longer than the expected 2.2 hours of transit so the filter won't factor an actual
                                                            # transit dip
         
           period_grid = np.linspace(0.5, 12, 1500) # tests 1500 dif orbit periods between 0.5 - 12 days of data, linspace method just creates a evenly spaced list
           bls = flat_lc.to_periodogram(method="bls", period=period_grid) # so box least squares (bls) is similar to the lsrl in ap stats where we fit a straight line to 
                                                                           # data points except here we fit a box shape to mimic the dip and my periodogram is a frequency
                                                                          # spectrum (x=trial#, y=power(not corealtion)) so it will show a giant spike on the orbit of the exo. 
                                                                           # period grid is just basically a list of potential guesses of orbit periods, and 1500 of them are tested.
        
           planet_p = bls.period_at_max_power   # extracts orbit at max power
           planet_t0 = bls.transit_time_at_max_power 
           max_power = bls.max_power.value # amount of power in integer form  

          # Power threshold filter: Ignore random scatter noise (Power < 12)
        if max_power < 12.0:
            print(f"   --> NOISE: Period = {planet_p.value:.4f} d | Max Power = {max_power:.2f} (Below signal threshold)\n")
            continue

        # folds all the light curve data collected over weeks and stacks them so the dip is easier to see
           folded_lc = flat_lc.fold(period=planet_p, epoch_time=planet_t0)
        
           fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8)) # creates two blank plots stacked vertically
           flat_lc.scatter(ax=ax1, s=1) # plots the raw light curves from flat_lc
           ax1.set_title(f"Cleaned Light Curve: {tic_id} (R_star = {row['st_rad']} R_sun)")
        
             folded_lc.scatter(ax=ax2, s=2, color='black', alpha=0.5) # plots the data for the folded or stacked data from folded_lc
             folded_lc.bin(time_bin_size=0.01).plot(ax=ax2, color='red', lw=2, label='Binned Profile') # bin just takes the average of the many data points that are close
                                                                                                      # and plots their average point or a singular point and does it by 
                                                                                                      #14.4 minutes (0.01*24hours*60mins)
             ax2.set_xlim(-0.3, 0.3) 
             ax2.set_title(f"Phase-Folded Signal (Period = {planet_p.value:.4f} d | Power = {max_power:.2f})") 
        
             filename = f"candidate_plots/{tic_id.replace(' ', '_')}_scan.png" # saves plot to file
             plt.tight_layout() # adjusts layout so no overlap of text
             plt.savefig(filename, dpi=150)
             plt.close(fig) # very important or else won't stop even after png is generated
             print(f"   --> Candidate plot saved to {filename}\n")
        
      except Exception as e: # this is an exception so if anything went wrong it would just skip and go to next star
          print(f"   --> Skipped {tic_id}: {e}\n")

print("Batch scan complete! Any candidate plots with Power > 12 are in 'candidate_plots'.")
 
DEBUGGING

bad_ids = ['194258999', '380157588']
df = df[~df['tic_id'].astype(str).str.contains('|'.join(bad_ids))]

So this was placed there because there was an issue with the second TIC
there was a valid search entry via NASA but there was nothing when it was downloaded
it was empty and python kept throwing an attribute error, so after many other iterations and work arounds I just decided to remove it from the set

if len(search_results) == 0: # checks for light curves and if there are any 

This was placed because in an early variation I kept getting no results logged for some targets so It caused problems 

These were the two main sources of error
