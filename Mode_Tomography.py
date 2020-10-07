from datetime import date
import os
import time
import itertools

import numpy as np
import matplotlib.pyplot as plt

import Meas_Function


today = date.today()
chipname = "testcipname"#"DL_v2_C5"
sample = "testsample3"#"Circ_Matrix_2x4_Dev_1x3_1580nm"

current_dir = "E:\Measurement\Double_Layer_Devices"
data_path = str(today) + '-' + chipname + '-' + sample + '-' + 'Data'

os.chdir(current_dir)
os.mkdir(data_path)
# -----------------Geometry of the device-----------------------
L_pad = 90E6
W_pad = 90E6
Vertical_step = 2E6
Horz_step = 2E6
H_steps = int(W_pad/Horz_step)
V_steps = int(L_pad/Vertical_step)

# --------------- Measurement parameters -----------------------

startFreq = 180E+3
stopFreq = 1E+6
calibration_peak = 200E+3
bW_Res = 50
coupling = 'DC'
sweeppoints = 1000

# ---------------Small Window measurement parameters ----------------
sm_lor_span = 3000
sm_bw_in = 5
calpeak_span = 500

#print('-------------------------------------------------------------')
#print('capacitances:')

#Meas_Function.measurement.print_capacitances(1)

# -------------------- Get peak lists for the membrane -------------------------------
# 1. Go to the point mentioned
# 2. Get a NPS and save the trace
# 3. Run a rough peak search and get the peak positions
# 4. Go to each peak position and check if there are 2 peaks that are close by
# 5. Get peak list for each point
# 6. Repeat for 2 other points
# 7. Merge all the lists for every point & have a criteria to remove peaks that have shifted due to position dependence
# --------------------------------------------------------------------------------------



# ------------------------- Get the starting position of the tomography ---------------

print("Enter start position x co-ordinate: ")
x_start = int(float(input()) * float(1E6))
print("Enter start position y co-ordinate: ")
y_start = int(float(input()) * float(1E6))

# ------------------------ Get the three points ---------------------------------------


[(x_target1, y_target1), (x_target2, y_target2), (x_target3, y_target3)] = Meas_Function.get_points(x_start, x_start+W_pad, y_start, y_start+L_pad, showGuide=True)
print([(x_target1, y_target1), (x_target2, y_target2), (x_target3, y_target3)])

# ---------------------------Get peak list for point 1----------------------------------
# List of peaks from point 2
[peak_list1,trace1] = Meas_Function.measurement.find_peak_list_at_point(chipname, sample,x_target1,y_target1,startFreq,stopFreq,bW_Res,coupling,sweeppoints,sm_lor_span,sm_bw_in)
print(peak_list1)

# List of peaks from point 2
[peak_list2,trace2] = Meas_Function.measurement.find_peak_list_at_point(chipname, sample,x_target2,y_target2,startFreq,stopFreq,bW_Res,coupling,sweeppoints,sm_lor_span,sm_bw_in)
print(peak_list2)

# List of peaks from point 3
[peak_list3,trace3] = Meas_Function.measurement.find_peak_list_at_point(chipname, sample,x_target3,y_target3,startFreq,stopFreq,bW_Res,coupling,sweeppoints,sm_lor_span,sm_bw_in)
print(peak_list3)

trace1_list = trace1.split(",")
trace2_list = trace2.split(",")
trace3_list = trace3.split(",")

trace1_list_num = list(map(float,trace1_list))
trace2_list_num = list(map(float,trace2_list))
trace3_list_num = list(map(float,trace3_list))

# ------------ Sort peaks from all points and then remove duplicates with window criteria----------------

# Combine all the lists
peaks_list_together = peak_list1 + peak_list2 + peak_list3
# Sort the points
peaks_list_together.sort(key=float)
# Convert to numbers
peaks_list_num = [float(p) for p in peaks_list_together]
# Remove duplicates from the list using window criteria
penultimate_peak_list = []  # Define the list for the penultimate peak list
val_old = peaks_list_num[0]  # Define holder for the previous value
penultimate_peak_list.append(peaks_list_num[0])
for i in peaks_list_num:
    if (float(str(i)) - float(val_old)) > 1.5E3:
        penultimate_peak_list.append(i)
    val_old = float(i)

fig = Meas_Function.plot_the_NPS([trace1_list_num, trace2_list_num, trace3_list_num],
                                 startFreq, stopFreq, penultimate_peak_list)

plt.show(block=False)
plt.pause(1)

final_peak_list = Meas_Function.frequency_chooser(penultimate_peak_list)

plt.close()

# ---------------------------------------------------------------------------------------------------------

# ----------------Write peaklists from all the points and sorted peaks to a txt file-----------------------
os.chdir(data_path)
peaklist_together = open('PeakLists_New.txt','w')
peaklist_together.write(str(peak_list1))
peaklist_together.write('\n')
peaklist_together.write(str(peak_list2))
peaklist_together.write('\n')
peaklist_together.write(str(peak_list3))
peaklist_together.write('\n')
peaklist_together.write('Final peaks list \n')
peaklist_together.write(str(final_peak_list))
peaklist_together.close()
os.chdir(current_dir)


#final_peaks_num = list(map(float,final_peak_list))
print(final_peak_list)

#tracemin = min(trace1)
#ystem = [-50] * len(final_peaks_num)


os.chdir(data_path)
# ----------------------------------------------------------------------------------------------------------


# ---------------------- Move to the start position for tomography -----------------------------------------
Meas_Function.measurement.positioner_move(x_start, y_start)

# Variables to store
x_position = []
y_position = []
fitted_data = []
error_data = []
summed_data = []
peak_data = []
x_pos = x_start
y_pos = y_start
index = 0
cal_peak_in = 219997.578

#os.chdir(data_path)


for i in range(0, H_steps):
    Meas_Function.measurement.positioner_move(x_pos, y_start)
    for j in range(0, V_steps):
        print(index, "out of", H_steps * V_steps)

        #-------------------------------------------------------------
        TomoData_fitted = open('Tomography_data_fitted.txt', 'a+')
        TomoData_summed = open('Tomography_data_summed.txt', 'a+')
        TomoData_error = open('Tomography_data_error.txt', 'a+')
        TomoData_peaks = open('Tomography_data_peaks.txt', 'a+')

        #-------------------------------------------------------------
        fitted_data.append([])
        error_data.append([])
        summed_data.append([])
        peak_data.append([])
        for p in final_peak_list:
            if p == calibration_peak:
                [fitted, error, summed,trace] = Meas_Function.measurement.measure_tomography_peaks(calpeak_span, p, sm_bw_in, sweeppoints)
            else:
                [fitted, error, summed,trace] = Meas_Function.measurement.measure_tomography_peaks(sm_lor_span, p, sm_bw_in,sweeppoints)
            fitted_data[index].append(float(fitted))
            error_data[index].append(float(error))
            summed_data[index].append(float(summed))
            peak_data[index].append(p)

            TomoData_trace = open('Tomography_data_trace.txt', 'a+')
            TomoData_trace.write(trace)
            TomoData_trace.write('\n')
            TomoData_trace.close()

            print(p, fitted, error, summed)

        TomoData_fitted.write(str(fitted_data[index]))
        TomoData_fitted.write('\n')
        TomoData_fitted.close()
        TomoData_summed.write(str(summed_data[index]))
        TomoData_summed.write('\n')
        TomoData_summed.close()
        TomoData_error.write(str(error_data[index]))
        TomoData_error.write('\n')
        TomoData_error.close()
        TomoData_peaks.write(str(peak_data[index]))
        TomoData_peaks.write('\n')
        TomoData_peaks.close()


        index = index + 1


        y_pos = int(y_start + (j + 1) * Vertical_step)

        Meas_Function.measurement.positioner_move_slow(x_pos, y_pos)

    x_pos = int(x_start + (i + 1) * Horz_step)
# ---------------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------- Write tomography data to file------------------------------------------------------------------

TomoData_toFile = open('Tomography_data_New.txt','w')
TomoData_toFile.write('Fitted data \n')
TomoData_toFile.write(str(fitted_data))
TomoData_toFile.write('\n')
TomoData_toFile.write('Summed data \n')
TomoData_toFile.write(str(summed_data))
TomoData_toFile.write('\n')
TomoData_toFile.write('Error data \n')
TomoData_toFile.write(str(error_data))
TomoData_toFile.write('\n')
TomoData_toFile.close()

# ----------------------------------------------------------------------------------------------------------------------------------------

print('-------------------------------------------------------------')
print('closing connection...')
print('-------------------------------------------------------------')
