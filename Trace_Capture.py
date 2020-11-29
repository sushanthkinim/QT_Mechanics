import Meas_Function
import pyvisa
import matplotlib.pyplot as plt
from datetime import date
import numpy as np
from matplotlib import ticker
with DLCpro(NetworkConnection('192.168.132.1')) as dlcpro
from toptica.lasersdk.dlcpro.v1_9_0 import DLCpro, NetworkConnection, CurrDrv2,  Dpss1
import os

VISA_ADDRESS_SA = 'TCPIP0::192.168.132.6::hislip0::INSTR'

resourceManager = pyvisa.ResourceManager(
    'C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll')
SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)

today = date.today()
chipname = "DL_v2_38"
sample = "9_5_1"
wavelength = "1580nm_150mA"

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

print("Enter start position x co-ordinate: ")
x_start = int(float(input()) * float(1E6))
print("Enter start position y co-ordinate: ")
y_start = int(float(input()) * float(1E6))

# - - - Get measurement - - -
trace_map = []
set_wl =
for i in range(10):
    trace_map.append([])
    set_wl = set_wl + i
    dlcpro.laser1.ctl.wavelength_set.set(set_wl)
    SpectrumAnalyzer.write(":TRAC? TRACE1")
    trace = SpectrumAnalyzer.read()
    trace_map[i].append(float(trace))




#[peak_list1,trace1] = Meas_Function.measurement.find_peak_list_at_point(chipname, sample,x_start,y_start,startFreq,stopFreq,bW_Res,coupling,sweeppoints,sm_lor_span,sm_bw_in)
#print(peak_list1)


final_peak_num = list(map(float,peak_list1))

trace1_list = trace1.split(",")
trace1_list_num = np.array(list(map(float,trace1_list)))
tracemin = np.amin(trace1_list_num)
ystem = [-20] * len(final_peak_num)
#peak_list = peak_list1.strip()
peak_list = list(map(lambda x:x.strip(),peak_list1))
peak_str =  str(peak_list1).strip('[]')
peak_list.sort(key=float)
print(peak_list)

np.savetxt(str(today)+'-'+chipname+'-'+sample+'-'+wavelength, trace1_list_num, header=f"bandwidth: {bW_Res}")


xaxis = np.linspace(startFreq,stopFreq,len(trace1_list_num))

fig, axs = plt.subplots()

plt.stem(final_peak_num, ystem, bottom=tracemin, linefmt='r:', markerfmt='D')
plt.plot(xaxis,trace1_list_num)
plt.xlabel('Frequency (kHz)')
plt.ylabel('NPS (dBm)')
plt.title('NPS of ' + sample + ' at ' + wavelength)


ticks_x = ticker.FuncFormatter(lambda xaxis, pos: '{0:g}'.format(xaxis / 1e3))
axs.xaxis.set_major_formatter(ticks_x)

plt.savefig('NPS of ' + sample + ' at ' + wavelength+'.pdf')
#plt.xlabel('Length in µm')
#plt.subplots_adjust(left=0.25)
#plt.gcf().text(0.0, 0.0, peak_str, fontsize=8)
plt.show()




