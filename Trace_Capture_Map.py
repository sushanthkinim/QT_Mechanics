import Meas_Function
import pyvisa
import matplotlib.pyplot as plt
import time
from datetime import date
import numpy as np
from matplotlib import ticker
from toptica.lasersdk.dlcpro.v1_9_0 import DLCpro, NetworkConnection, CurrDrv2,  Dpss1

import os

VISA_ADDRESS_SA = 'TCPIP0::192.168.132.6::hislip0::INSTR'

resourceManager = pyvisa.ResourceManager(
    'C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll')
SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)

today = date.today()
chipname = "DL_v2_38"
sample = "3_5"
wavelength = "Sweep"

startFreq = 100E+3
stopFreq = 3E+6#1
calibration_peak = 200E+3
bW_Res = 50
coupling = 'DC'
sweeppoints = 1000

# ---------------Small Window measurement parameters ----------------
sm_lor_span = 2000
sm_bw_in = 5
calpeak_span = 500

trace_map = [];
set_wl = 1600.0
# - - - Get measurement - - -
with DLCpro(NetworkConnection('192.168.132.1')) as dlcpro:

    for i in range(200):
        trace_map.append([])
        print(set_wl)
        dlcpro.laser1.ctl.wavelength_set.set(set_wl)
        set_wl = set_wl + 0.1
        time.sleep(0.5)
        SpectrumAnalyzer.write(":TRAC1:TYPE WRIT")
        SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
        time.sleep(1)
        SpectrumAnalyzer.write(":TRAC? TRACE1")
        trace = SpectrumAnalyzer.read()
        trace_map[i].append((trace))

        Data_trace = open(str(today) + '_Data_trace_New' + chipname + '-' + sample + '.txt', 'a+')
        Data_trace.write(trace)
        Data_trace.write('\n')
        Data_trace.close()







