import Tomo_Measure_New
import matplotlib.pyplot as plt
from datetime import date
import os
import time

today = date.today()
chipname = "DL_v2"
sample = "TestRun"

current_dir = os.getcwd()
data_path = str(today) + ' ' + chipname + ' ' + sample + ' ' + 'Data'

if os.path.exists(data_path) :
    # Change the current working Directory
    os.chdir(data_path)
else :
    os.mkdir(data_path)
    os.chdir(data_path)

# --------------- Measurement parameters -----------------------

startFreq = 300E+3
stopFreq = 400E+3
calibration_peak = 200E+3
bW_Res = 50
coupling = 'DC'
sweeppoints = 1000

# ---------------Small Window measurement parameters ----------------
sm_lor_span = 5000
sm_bw_in = 5
calpeak_span = 500


# ----------------------Number of devices Rows x Columns -----------

N_devicesV = 4
N_devicesH = 3

Vertical_Step = float(500E6) #Distance between devices vertically
Horizontal_Step = float(500E6) #Distance between devices horizontally


# ------------------------- Get the starting position of the tomography ---------------

print("Enter start position x co-ordinate: ")
x_start = int(float(input()) * float(1E6))
print("Enter start position y co-ordinate: ")
y_start = int(float(input()) * float(1E6))

# ------------------------- Get the end position of the tomography ---------------

print("Enter end position x co-ordinate: ")
x_end = int(float(input()) * float(1E6))
print("Enter end position y co-ordinate: ")
y_end = int(float(input()) * float(1E6))

# ----------------------------- Slope of the device --------------------

slope = (y_end - y_start) / (x_end - x_start)

# ------------------------------ Get NPS at each point

x_pos = x_start
y_pos = y_start
x_thisrow = x_start
y_thisrow = y_start

for j in range(0, N_devicesH):
    Tomo_Measure_New.measurement.positioner_move(x_pos, y_pos)

    for k in range(0,N_devicesV):

        Tomo_Measure_New.measurement.positioner_move(x_pos, y_pos)
        print('NewRow')

        device_tag = str(j+1) + 'x' + str(k+1)
        os.mkdir(device_tag)
        os.chdir(device_tag)

        [peak_list1, trace1] = Tomo_Measure_New.measurement.find_NPS_and_Peaks(startFreq,stopFreq,bW_Res,coupling,sweeppoints,sm_lor_span,sm_bw_in)

        # --------------------------------- Sort and save data ------------------------------------------------------------
        peak_list1.sort(key=float)
        final_peaks = []
        val_old = peak_list1[0]
        final_peaks.append(val_old)
        for i in peak_list1:
            if (float(str(i)) - float(val_old)) > 2.5E3:
                final_peaks.append(i)
            val_old = float(i)
        print(final_peaks)

        passdata = open(
            chipname + '_' + sample + str(startFreq / 1E3) + 'to' + str(stopFreq / 1E3) + '_' + 'Peak_Pos.txt', 'w')
        passdata.write(str(peak_list1))
        passdata.write('\n')
        passdata.write(str(final_peaks))
        passdata.close()

        tracedata = open(
            chipname + '_' + sample + str(startFreq / 1E3) + 'to' + str(stopFreq / 1E3) + '_' + 'trace.csv', 'w')
        tracedata.write(trace1)
        tracedata.close()

        # ---------------------- Set next position ----------------------------------------------------
        y_pos = int(y_thisrow + (k + 1) * Vertical_Step)
        x_pos = int(x_thisrow + (k + 1) * Vertical_Step / slope)

        time.sleep(1)

    # ----------------------- Set next row -------------------------------------------------------------
    x_pos = int(float(x_thisrow + Horizontal_Step))
    y_pos = int(float(y_thisrow + Horizontal_Step / slope))
    print('NewCol')

    # ----------------------- Set hold value for next iteration --------------------------------------
    y_thisrow = y_pos
    x_thisrow = x_pos






