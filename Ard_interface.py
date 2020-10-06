from time import sleep
import serial
import numpy as np
import time
import matplotlib.pyplot as plt
from toptica.lasersdk.dlcpro.v1_9_0 import DLCpro, NetworkConnection, CurrDrv2,  Dpss1
import os

import datetime
date = []
today = datetime.date.today()
date.append(today)


#sample = 'DM_11x8_10V_PS__25pts'
sample = 'DL_v2_C2_5'
wavelength = 1520.0
wavelength_f = 1630.0
step = 0.1
data_pts = int((wavelength_f - wavelength)/step + 1)
wavelength_array = np.linspace(wavelength, wavelength_f, data_pts)
AVGs = 10

file = open(sample + '_Wavelength_sweep_' + str(wavelength) + '_to_' + str(wavelength_f) + '_step' + str(step) + str(date) + str(time.time()) +'.txt', "w")
file.write('Date: ' + str(date[0]) + '\n')
file.write('start: ' + str(wavelength) + ' nm, End: ' + str(wavelength_f) + ' nm, Step: ' + str(step) + ' nm\n')
file.write('Wavelength[nm]\tReflected[V]\tStd_dev\tReference[V]\tstd_dev\n')

#file2 = open(sample + '_reference_Wavelength_sweep_' + str(wavelength) + '_to_' + str(wavelength_f) + '_step' + str(step) + str(date) + str(time.time()) +'.txt', "w")
#file2.write('Date: ' + str(date[0]) + '\n')
#file2.write('start: ' + str(wavelength) + ' nm, End: ' + str(wavelength_f) + ' nm, Step: ' + str(step) + ' nm\n')
#file2.write('Wavelength[nm]\tVoltage[V]\n')

temp_data = np.empty(shape=[AVGs, 1])
temp_data2 = np.empty(shape=[AVGs, 1])


data = np.empty(shape=[data_pts, 1])
data2 = np.empty(shape=[data_pts, 1])
#ard = serial.Serial("COM4",115200)
ard = serial.Serial(
    port = 'COM4',
    baudrate = 115200,
    bytesize = 8,
    parity = 'N',
    stopbits = 1,
    timeout = 1,
    xonxoff = 0,
    rtscts = 0
    )

if ard.isOpen():
    ard.close()
ard.open()
ard.isOpen()

sleep(8)
ref_channel = 2
measure_channel = 1

ard.write(b'1')
ard.write(b'2')
ard.write(b'3')
ard.write(b'4')
ard.write(b'1')
ard.write(b'2')
ard.write(b'3')
ard.write(b'4')
ard.write(b'1')
ard.write(b'2')
ard.write(b'3')
ard.write(b'4')
time.sleep(0.100)


wavelength_count = 0
with DLCpro(NetworkConnection('192.168.132.1')) as dlcpro:
         while wavelength_count < data_pts:
                dlcpro.laser1.ctl.wavelength_set.set(wavelength + wavelength_count * step)
                time.sleep(0.025)
                if (((wavelength + wavelength_count * step) > 1556) and ((wavelength + wavelength_count * step) < 1560) or ((wavelength + wavelength_count * step) > 1616) and ((wavelength + wavelength_count * step) < 1620)):
                    print("increased waiting time")
                    time.sleep(0.25)
                if wavelength_count == 0:
                    temp_count = 0
                    sleep(5)
                    #while temp_count < 300:
                    #    ard.write(1)
                    #    msg = ard.read(10)
                    #    temp_count += 1
                print(dlcpro.laser1.ctl.wavelength_set.get())
                counter = 0
                #time.sleep(0.05)
                while counter < AVGs:
                    ard.write(b'2')
                    msg = ard.readline().decode('ascii')
                    msg = float(msg)

                    ard.write(b'1')
                    msg2 = ard.readline().decode('ascii')
                    msg2 = float(msg2)
                    #time.sleep(0.025)

                    temp_data[counter] = msg
                    temp_data2[counter] = msg2
                    counter = counter + 1
                #time.sleep(0.025)
                temp_data = temp_data#/10
                average = np.mean(temp_data)
                std_dev = np.std(temp_data)
                #data[wavelength_count] = average
                data2[wavelength_count] = average
                average2 = np.mean(temp_data2)
                #print(average2)
                std_dev2 = np.std(temp_data2)
                #data2[wavelength_count] = average2
                data[wavelength_count] = average2
                file.write(str(wavelength + wavelength_count * step) + '\t' + str(average) + '\t' + str(std_dev)
                           + '\t' + str(average2) + '\t' + str(std_dev2) + '\n')
                #file2.write(str(wavelength + wavelength_count * step) + '\t' + str(average2) + '\t' + str(std_dev2) + '\n')
                wavelength_count = wavelength_count + 1
                #if wavelength + wavelength_count * step == 1550 or wavelength + wavelength_count * step == 1610:
                #   input()

         dlcpro.laser1.ctl.wavelength_set.set(1520.0)

plt.plot(wavelength_array, data2, 'r-o', label='Reference')
plt.plot(wavelength_array, data, 'b-o', label='Reflected')
plt.legend()
plt.title('Voltage vs Wavelength')
plt.xlabel('Wavelength [nm]')
plt.ylabel('Voltage [V]')
plt.savefig(sample + '_Wavelength_sweep_' + str(wavelength) + '_to_' + str(wavelength_f) + '_step' + str(step) + str(date) + str(time.time()) + '.png')
plt.close()
plt.plot(wavelength_array[1:], np.divide(data, data2)[1:], 'b-o')
plt.xlabel('Wavelength [nm]')
plt.ylabel('Reflectivity')
plt.savefig(sample + '_Reflectivity_' + str(wavelength) + '_to_' + str(wavelength_f) + '_step' + str(step) + str(date) + str(time.time()) + '.png')
plt.show()
plt.close()

# data_mirror = np.genfromtxt('Mirror_10V_PS__Wavelength_sweep_1520.0_to_1630.0_step0.25[datetime.date(2019, 3, 28)]1553783327.8710752.txt', skip_header=3, delimiter='\t')
# freqM = data_mirror[:, 0]
# reflectedM = data_mirror[:, 1]
# error1M = data_mirror[:, 2]
# referenceM = data_mirror[:, 3]
# error2M = data_mirror[:, 4]
# refM = np.divide(reflectedM, referenceM)
#
# reference = data2
#
# norm_ref = np.divide(reference, referenceM)*(1/0.982)
#
# plt.plot(wavelength_array, norm_ref, 'b-o')
# plt.xlabel('Wavelength [nm]')
# plt.ylabel('Reflectivity')
# plt.savefig(sample + 'Norm_Reflectivity_' + str(wavelength) + '_to_' + str(wavelength_f) + '_step' + str(step) + str(date) + str(time.time()) + '.png')
# plt.close()
# file.close()
# #file2.close()
