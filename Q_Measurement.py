import Meas_Function
import matplotlib.pyplot as plt
from datetime import date
import os
import time
import numpy as np
from PIL import Image

today = date.today()
chipname = "DLW1C_50"
sample = "14_3_membrane_159mA_1550"

current_dir = "E:\Measurement\Double_Layer_Devices\Q_Measurements"
data_path = str(today) + '-' + chipname + '-' + sample + '-' + 'Data'

os.chdir(current_dir)

#---- If Q_Factor measurement via lorentzian fit is required set 'Q_factor_via_Lorentzian_Fit' to 1 else set to 0
Q_factor_via_Lorentzian_Fit = 1

#---- If Q_Factor measurement via ringdown is required set 'Q_factor_via_Ringdown_Fit' to 1 else set to 0
Q_factor_via_Ringdown_Fit = 1

if os.path.exists(data_path) :
    # Change the current working Directory
    os.chdir(data_path)
else :
    os.mkdir(data_path)
    os.chdir(data_path)

# --------------- Measurement parameters -----------------------

startFreq = 200E+3
stopFreq = 1.6E+6
calibration_peak = 200E+3
bW_Res = 50
coupling = 'DC'
sweeppoints = 10000

# ---------------Small Window measurement parameters ----------------
sm_lor_span = 5000
sm_bw_in = 5

calpeak_span = 500


# ----------------------Number of devices Rows x Columns -----------

N_devicesV = 1 #Vertical on the screen (Y axis of the positioner)
N_devicesH = 1  #Horizontal on the screen (X axis of the positioner)

Vertical_Step = float(250E6) #Distance between devices vertically
Horizontal_Step = float(250E6) #Distance between devices horizontally


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
    Meas_Function.measurement.positioner_move(x_pos, y_pos)
    time.sleep(10)
    for k in range(0,N_devicesV):

        Meas_Function.measurement.positioner_move(x_pos, y_pos)
        time.sleep(10)
        print('NewRow')

        #device_tag = str(j+1) + 'x' + str(k+1)
        device_tag = str(N_devicesH - j) + 'x' + str(N_devicesV - k)
        os.mkdir(device_tag)
        os.chdir(device_tag)

        [peak_list1, trace1] = Meas_Function.measurement.find_NPS_and_Peaks(startFreq,stopFreq,bW_Res,coupling,sweeppoints,sm_lor_span,sm_bw_in)

        trace1_list = trace1.split(",")
        trace1_list_num = list(map(float, trace1_list))
        xaxis = np.linspace(startFreq, stopFreq, len(trace1_list_num))
        plt.plot(xaxis,trace1_list_num,'r')
        plt.savefig('NPS.pdf')
        plt.close()


        # --------------------------------- Sort and save data ------------------------------------------------------------
        peak_list1.sort(key=float)
        final_peaks = []
        val_old = peak_list1[0]
        final_peaks.append(val_old)
        for i in peak_list1:
            if (float(str(i)) - float(val_old)) > 0.5E3:
                final_peaks.append(i)
            val_old = float(i)
        #final_peaks.rstrip()
        print(peak_list1)
        print(final_peaks)

        passdata = open(
            chipname + '_' + sample + str(startFreq / 1E3) + 'to' + str(stopFreq / 1E3) + '_' + 'Peak_Pos.txt', 'w')
        passdata.write(str(peak_list1))
        passdata.write('\n')
        passdata.write(str(final_peaks))
        passdata.close()

        tracedata = open(
            chipname + '_' + sample + '_' +  str(startFreq / 1E3) + 'to' + str(stopFreq / 1E3) + '_' + 'trace.csv', 'w')
        tracedata.write(trace1)
        tracedata.close()

        peaks_list_num = [float(p) for p in final_peaks]


        #Meas_Function.plot_the_NPS(trace1,startFreq,stopFreq,final_peaks,savedir=os.getcwd())
        #xaxis = np.linspace(startFreq,stopFreq,len(trace1))
        #plt.plot(xaxis,trace1,'r')
        #plt.savefig('NPS.pdf')
        #
        if (Q_factor_via_Lorentzian_Fit == 1 and Q_factor_via_Ringdown_Fit == 1) :
            Q_factor_fitted = []
            Gamma_fitted = []
            Q_fit_trace = []
            Q_factor_Ringdown = []
            index = 0

            Q_fit_tracelog = open('Trace_log_Q_fit' + chipname + device_tag + '.txt', 'a+')
            Q_RD_tracelog = open('Trace_log_Q_ringdown' + chipname + device_tag + '.txt', 'a+')

            Q_data = open('Q_factor_' + chipname + device_tag + '.txt', 'a+')

            Q_fit_data = open('Q_factor_fit' + chipname + device_tag + '.txt', 'a+')
            Q_RD_data =  open('Q_factor_ringdown' + chipname + device_tag + '.txt', 'a+')

            Q_data.write(str(today) + ' ' + chipname + ' ' + sample + '\n')
            Q_data.write('Frequency' + '\t' + 'Q_factor_Fit' + '\t' + 'Ringdown' + '\n')

            Q_fit_data.write(str(today) + ' ' + chipname + ' ' + sample + '\n')
            Q_fit_data.write('Frequency' + '\t' + 'Q_factor_Fit' + '\t' + 'Gamma' + '\n')

            Q_RD_data.write(str(today) + ' ' + chipname + ' ' + sample + '\n')
            Q_RD_data.write('Frequency' + '\t' + 'Ringdown' + '\n')

            #Q_factor_fitted.append([])
            #Gamma_fitted.append([])
            #Q_fit_trace.append([])
            for p in final_peaks:
                #peak_in = Meas_Function.measurement.Q_factor_peak_fine(sm_lor_span,p,sm_bw_in)
                bw_in = 1
                [Q_fit,Gamma,trace] = Meas_Function.measurement.lorentzian_fit_QFactor(sm_lor_span,p,sm_bw_in,sweeppoints)


                #Open files for writng
                Q_fit_data = open('Q_factor_fit' + chipname + device_tag + '.txt', 'a+')
                Q_fit_tracelog = open('Trace_log_Q_fit' + chipname + device_tag + '.txt', 'a+')

                #Q_factor_fitted[index].append(Q)
                #Gamma_fitted[index].append(Gamma)

                Q_fit_tracelog.write(trace)
                Q_fit_tracelog.write('\n')

                Q_fit_data.write(str(round(float(p),2)) + '\t' + str(round(Q_fit,2)) + '\t\t' + str(round(Gamma,2)))
                Q_fit_data.write('\n')

                Q_fit_data.close()
                Q_fit_tracelog.close()

                if (Gamma < 300 and Gamma > 15):

                    Q_RD, x_fit, data_fit, data_watts = Meas_Function.measurement.ringdown_Qfactor(p,sweeppoints)

                    Q_RD_tracelog.write('\n Data_Fit \n')
                    Q_RD_tracelog.write(str(data_fit))
                    Q_RD_tracelog.write('\n xfit \n')
                    Q_RD_tracelog.write(str(x_fit))
                    Q_RD_tracelog.write('\n Data_watts \n')
                    Q_RD_tracelog.write(str(data_watts))

                    print(Q_RD)

                    Q_RD_data.write(str(round(float(p),2)) + '\t')
                    Q_RD_data.write(str(Q_RD[0]) + '\t' + str(Q_RD[1]) + '\t' + str(Q_RD[2]) + '\t' + str(round(sum(Q_RD)/len(Q_RD),2)))
                    Q_RD_data.write('\n')

                    Q_data.write(str(round(float(p),2)) + '\t' + str(round(Q_fit,2)) + '\t\t' + str(round(sum(Q_RD)/len(Q_RD),2)))
                    Q_data.write('\n')



        # ---------------------- Set next position ----------------------------------------------------
        y_pos = int(y_thisrow + (k + 1) * Vertical_Step)
        x_pos = int(x_thisrow + (k + 1) * Vertical_Step / slope)


        Q_RD_data.close()
        Q_data.close()
        Q_RD_tracelog.close()

        time.sleep(1)

        os.chdir(current_dir)
        os.chdir(data_path)

    # ----------------------- Set next row -------------------------------------------------------------
    x_pos = int(float(x_thisrow + Horizontal_Step))
    y_pos = int(float(y_thisrow + Horizontal_Step / slope))
    print('NewCol')

    os.chdir(current_dir)
    os.chdir(data_path)
    # ----------------------- Set hold value for next iteration --------------------------------------
    y_thisrow = y_pos
    x_thisrow = x_pos







