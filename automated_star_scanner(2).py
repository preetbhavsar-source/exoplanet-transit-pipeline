import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os  -- for 
import socket

socket.setdefaulttimeout(12)

df = pd.read_csv("unstudied_candidates.csv")
os.makedirs("candidate_plots", exist_ok=True)

bad_ids = ['194258999', '380157588']
df = df[~df['tic_id'].astype(str).str.contains('|'.join(bad_ids))]

targets_to_scan = df.iloc[10:60]
