import numpy as np

from BOP50_8D import KEPCO_BOP
from HP8673G import HP_CWG
from SRS_SR830 import SRS_SR830

# Define instruments
PS = KEPCO_BOP() # Power Supply
SG = HP_CWG() # HP Signal Generator
LIA = SRS_SR830() # SRS 380 Lock-in Amplifier


# PS parameters
ps_current_values = np.linspace(0, 8, 20)

# SG parameters
sg_frequency_values = np.linspace(4, 20, 20)

# An N x M x 2 array of numbers where N = len(ps_current_values), M = len(sg_frequency_values).
# One 2D array contains the PS amperage and the other has SG frequency values

input_params = np.zeros((len(ps_current_values), len(sg_frequency_values), 2))