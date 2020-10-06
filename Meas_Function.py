#Libraries
import pyvisa
import sys
import time
import datetime
import matplotlib.pyplot as plt
import math
import numpy as np
from scipy.optimize import curve_fit
from scipy.integrate import quad
import itertools
import smaract.ctl as ctl

stage = {'z': 0, 'x': 1, 'y': 2}


# Address to the instrument
VISA_ADDRESS_SA = 'TCPIP0::192.168.132.6::hislip0::INSTR'
VISA_ADDRESS_SG = 'USB0::6833::1602::DG1ZA193804316::0::INSTR'
ADDRESS_POSITIONER = 'network:sn:MCS2-00002342'

# Create a connection (session) to the instrument
resourceManager = pyvisa.ResourceManager(
    'C:\\Program Files (x86)\\IVI Foundation\\VISA\\WinNT\\agvisa\\agbin\\visa32.dll')
SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
SignalGenerator = resourceManager.open_resource(VISA_ADDRESS_SG)


date = []
today = datetime.date.today()
date.append(today)

## ---------------------- SMARACT MCS2 -----------------------------

try:
    buffer = ctl.FindDevices("", 1024)
    if len(buffer) == 0:
        exit(1)
    locators = buffer.split("\n")
except:
    print("MCS2 failed to find devices. Exit.")
    input()
    exit(1)

d_handle = 0
try:
    # Open the first MCS2 device from the list
    d_handle = ctl.Open(locators[0], "")
    #print("MCS2 opened {}.".format(locators[0]))

    type = ctl.GetProperty_i32(d_handle, 1, ctl.PropertyKey.CHANNEL_TYPE)
    if type == ctl.ChannelModuleType.STICK_SLIP_PIEZO_DRIVER:
        ctl.SetProperty_i32(d_handle, 1, ctl.PropertyKey.MAX_CL_FREQUENCY, 6000)
        ctl.SetProperty_i32(d_handle, 1, ctl.PropertyKey.HOLD_TIME, 1000)
    elif type == ctl.ChannelModuleType.MAGNETIC_DRIVER:
        # Enable the amplifier (and start the phasing sequence).
        ctl.SetProperty_i32(d_handle, 1, ctl.PropertyKey.AMPLIFIER_ENABLED, ctl.ENABLED)

except ctl.Error as e:
    # Passing an error code to "GetResultInfo" returns a human readable string
    # specifying the error.
    print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}. Press return to exit."
          .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code, (sys.exc_info()[-1].tb_lineno)))

except Exception as ex:
    print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))
    raise

## ---------------------- SMARACT MCS2 -----------------------------

class measurement:

    def initialise_SA(startFreq, stopFreq, bW_Res, coupling_Type,sweep):

        try:
            SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
            SpectrumAnalyzer.write(":SENSe:FREQuency:STARt " + str(startFreq) + "Hz")
            SpectrumAnalyzer.write(":SENSe:FREQuency:STOP " + str(stopFreq) + "Hz")
            SpectrumAnalyzer.write("SENSe:BWIDth:RESolution " + str(bW_Res) + "Hz")
            SpectrumAnalyzer.write("INPut:COUPling " + str(coupling_Type))
            SpectrumAnalyzer.write("SENSe:SWEep:POINts " + str(sweep))
            SpectrumAnalyzer.write(":TRAC1:TYPE AVER")

        except pyvisa.Error as ex:
            print('Couldn\'t connect to \'%s\', exiting now...' % VISA_ADDRESS_SA)
            sys.exit()

    def save_trace(self):
        try:
            SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
            SpectrumAnalyzer.write(":TRAC1:TYPE WRIT")
            SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
            time.sleep(5)
            SpectrumAnalyzer.write(":TRAC? TRACE1")
            trace = SpectrumAnalyzer.read()
            return (trace)

        except pyvisa.Error as ex:
            print('Couldn\'t connect to \'%s\', exiting now...' % VISA_ADDRESS_SA)
            sys.exit()

    def find_peak_rough(self):
        try:
            SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
            count = 0
            SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
            peak_pos = []
            time.sleep(10)
            SpectrumAnalyzer.write(":CALCulate:MARKer1:MAX")
            SpectrumAnalyzer.write("CALC:MARK1:X?")
            freq = SpectrumAnalyzer.read()
            peak_pos.append(freq)
            data_old = freq
            while True:
                SpectrumAnalyzer.write(":CALCulate:MARKer1:MAXimum:NEXT")
                SpectrumAnalyzer.write("CALC:MARK1:X?")
                freq = SpectrumAnalyzer.read()
                if freq == data_old:
                    break
                data_old = freq
                count = count + 1
                peak_pos.append(freq)

            return peak_pos

        except pyvisa.Error as ex:
            print('Couldn\'t connect to \'%s\', exiting now...' % VISA_ADDRESS_SA)
            sys.exit()

    def find_peak_fine(Lorentzian_span,peak_UT,BW_res_Lorentzian):
        try:
            SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
            SpectrumAnalyzer.write(":SENSe:FREQuency:SPAN " + str(Lorentzian_span) + "Hz")
            SpectrumAnalyzer.write(":SENSe:FREQuency:CENTer " + str(peak_UT) + "Hz")
            SpectrumAnalyzer.write("SENSe:BWIDth:RESolution " + str(BW_res_Lorentzian) + "Hz")
            SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
            peak_pos = []
            count = 0
            time.sleep(10)
            SpectrumAnalyzer.write(":CALCulate:MARKer1:MAX")
            SpectrumAnalyzer.write("CALC:MARK1:X?")
            freq = SpectrumAnalyzer.read()
            peak_pos.append(freq)
            data_old = freq
            while True:
                SpectrumAnalyzer.write(":CALCulate:MARKer1:MAXimum:NEXT")
                SpectrumAnalyzer.write("CALC:MARK1:X?")
                freq = SpectrumAnalyzer.read()
                if freq == data_old:
                    break
                data_old = freq
                count = count + 1
                peak_pos.append(freq)
            return peak_pos

        except pyvisa.Error as ex:
            print('Couldn\'t connect to \'%s\', exiting now...' % VISA_ADDRESS_SA)
            sys.exit()

    def find_peak_list_at_point(chipname, sample, x_pos, y_pos, startFreq, stopFreq, bW_Res, coupling, sweeppoints, sm_lor_span, sm_bw_in):
        try:
            measurement.positioner_move(x_pos, y_pos)  # Move to point 1
            # Initialise the spectrum analyser
            measurement.initialise_SA(startFreq, stopFreq, sm_bw_in, coupling, sweeppoints)
            # Get trace
            trace = measurement.save_trace(1)
            # Save Trace Data
            # passdata = open(
            #     chipname + '_' + sample + '_' + 'Point_3' + '_' + str(startFreq) + 'to' + str(stopFreq) + '.csv', 'w')
            # passdata.write(trace)
            # passdata.close()
            # Get a rough spectrum with peak positions
            peak_pos = measurement.find_peak_rough(1)
            # Check to see if there are two peaks close by
            peak_list = []
            for i in peak_pos:
                peak_return = measurement.find_peak_fine(sm_lor_span, i, sm_bw_in)
                time.sleep(2)
                peak_list.append(peak_return)
            # Get the peak list and flatten list
            peaks_list = list(itertools.chain.from_iterable(peak_list))
            return [peaks_list,trace]
        except Exception as e:
                    print(e)

    def print_capacitances(self):
        try :
            for axis in sorted(ax.keys()):
                print(axis, anc.measureCapacitance(ax[axis]))
                print(axis, anc.getPosition(ax[axis]))
        except Exception as e:
            print(e)

    def measure_tomography_peaks(Lorentzian_span, peak_in, BW_res_Lorentzian,sweeppoints):
        try:
            averaging = 1
            time.sleep(1)
            for avg_time in [averaging]:
                peak_UT = float(peak_in)
                SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
                SpectrumAnalyzer.write(":SENSe:FREQuency:SPAN " + str(Lorentzian_span) + "Hz")
                SpectrumAnalyzer.write(":SENSe:FREQuency:CENTer " + str(peak_UT) + "Hz")
                SpectrumAnalyzer.write("SENSe:BWIDth:RESolution " + str(BW_res_Lorentzian) + "Hz")
                #SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
                time.sleep(1)
                SpectrumAnalyzer.write(":CALCulate:MARKer1:MAX")
                SpectrumAnalyzer.write(":CALCulate:MARKer1:SET:CENTer")
                #SpectrumAnalyzer.write("CALC:MARK1:X?")
                #freq = SpectrumAnalyzer.read()
                #SpectrumAnalyzer.write(":SENSe:FREQuency:CENTer " + str(peak_UT) + "Hz")
                time.sleep(1)
                SpectrumAnalyzer.write(":TRAC? TRACE1")
                trace = SpectrumAnalyzer.read()
                trace_array = tuple(trace.split(','))
                y = np.array(trace_array, np.float)
                Npoints = int(sweeppoints)
                sum_back = 0
                k = 0
                background_pts = int(0.2 * Npoints)
                peak_window = int(0.1 * Npoints)
                data_watts = np.power(10, (y - 30) / 10)
                sum_all = np.sum(data_watts) * BW_res_Lorentzian

                # noise background for the fitting
                while k < background_pts:
                    sum_back = sum_back + data_watts[k] + data_watts[Npoints - k - 1]
                    k = k + 1

                sum_back = sum_back / (2 * background_pts)
                y0 = sum_back
                y0 = np.min(data_watts)
                xi = np.argmax(data_watts[int(np.size(data_watts) / 2) - peak_window: int(np.size(data_watts) / 2) + peak_window: 1])
                xi = peak_UT + (xi - peak_window) / (Npoints / Lorentzian_span)

                x_fit = np.linspace(peak_UT - Lorentzian_span / 2, peak_UT + Lorentzian_span / 2, Npoints, endpoint=False)
                popt = [0, 0]
                try:

                    def func_lorentzian(x, gam, A):
                        return y0 + (A / ((np.power(x - xi, 2)) + math.pow(gam, 2)))

                    if np.max(data_watts[int(np.size(data_watts) / 2) - peak_window: int(np.size(data_watts) / 2) + peak_window: 1]) / sum_back > 5:
                        popt, pcov = curve_fit(func_lorentzian, x_fit, data_watts)
                        Gamma = popt[0]
                        Q = 2 * math.pi * peak_UT * (1.0 / (4 * math.pi * popt[0]))
                        I = math.pi * popt[1] / popt[0]
                        I_err = I * np.sqrt((pcov[0, 0] / popt[0] ** 2) + (pcov[1, 1] / popt[1] ** 2))
                    else:
                        I = 1e-13
                        I_err = 1e-13
                except RuntimeError:
                    I = 1e-13
                    I_err = 1e-13
            return [I, I_err, sum_all, trace]
        except Exception as e:
                    print(e)

    def plot_the_NPS(trace1,trace2,trace3, startFreq, stopFreq, final_list):
        try :
            xaxis = np.linspace(startFreq, stopFreq, len(trace1))
            tracemin = min(trace1)
            tracemax = max(trace1)
            ystem = [-20] * len(final_list)

            fig,axs = plt.subplots(3)

            axs[0].stem(final_list, ystem, bottom=tracemin, linefmt='r:', markerfmt='D')
            axs[0].plot(xaxis, trace1, color='blue')
            axs[0].set(xlabel='Frequency', ylabel='NPS at point 1')

            axs[1].stem(final_list, ystem, bottom=tracemin, linefmt='r:', markerfmt='D')
            axs[1].plot(xaxis, trace2, color='blue')
            axs[1].set(xlabel='Frequency', ylabel='NPS at point 2')

            axs[2].stem(final_list, ystem, bottom=tracemin, linefmt='r:', markerfmt='D')
            axs[2].plot(xaxis, trace3, color='blue')
            axs[2].set(xlabel='Frequency', ylabel='NPS at point 3')

            plt.savefig('NPS_ThreePoints.pdf', format='pdf', dpi=300)

            return fig

            plt.tight_layout()
        except Exception as e:
                    print(e)

    def Extract(list_in,rows,index):
        data_return = []
        j = 0
        i = 0
        data_return.append([])
        while j < len(fitted):
            data_return[i].append(list_in[j][index])
            j = j + 1;
            if (j % rows == 0) and i < rows - 1:
                i = i + 1
                data_return.append([])
        return data_returnd

    def find_NPS_and_Peaks(startFreq, stopFreq, bW_Res, coupling, sweeppoints, sm_lor_span, sm_bw_in):
        try:
            # Initialise the spectrum analyser
            measurement.initialise_SA(startFreq, stopFreq, sm_bw_in, coupling, sweeppoints)
            # Get trace
            trace = measurement.save_trace(1)
            # Save Trace Data
            # passdata = open(
            #     chipname + '_' + sample + '_' + 'Point_3' + '_' + str(startFreq) + 'to' + str(stopFreq) + '.csv', 'w')
            # passdata.write(trace)
            # passdata.close()
            # Get a rough spectrum with peak positions
            peak_pos = measurement.find_peak_rough(1)
            # Check to see if there are two peaks close by
            peak_list = []
            for i in peak_pos:
                peak_return = measurement.find_peak_fine(sm_lor_span, i, sm_bw_in)
                time.sleep(2)
                peak_list.append(peak_return)
            # Get the peak list and flatten list
            peaks_list = list(itertools.chain.from_iterable(peak_list))
            return [peaks_list,trace]
        except Exception as e:
                    print(e)

## ---------------- If SMARACT stage is used -----------------------------------------------------
    def positioner_move(x_pos, y_pos):
        try:
            move_mode = ctl.MoveMode.CL_ABSOLUTE
            ctl.SetProperty_i32(d_handle, 1, ctl.PropertyKey.MOVE_MODE, move_mode)
            ctl.SetProperty_i32(d_handle, 2, ctl.PropertyKey.MOVE_MODE, move_mode)

            ctl.SetProperty_i64(d_handle, 1, ctl.PropertyKey.MOVE_VELOCITY, 100000000)
            # Set move acceleration [in pm/s2].
            ctl.SetProperty_i64(d_handle, 1, ctl.PropertyKey.MOVE_ACCELERATION, 100000000)

            ctl.Move(d_handle, 1, x_pos, 0)


            ctl.SetProperty_i64(d_handle, 2, ctl.PropertyKey.MOVE_VELOCITY, 100000000)
            # Set move acceleration [in pm/s2].
            ctl.SetProperty_i64(d_handle, 2, ctl.PropertyKey.MOVE_ACCELERATION, 100000000)

            ctl.Move(d_handle, 2, y_pos, 0)


        except ctl.Error as e:

            print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}. Press return to exit."
                  .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code,
                          (sys.exc_info()[-1].tb_lineno)))

        except Exception as ex:
            print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))

    def positioner_move_slow(x_pos, y_pos):
        try:
            move_mode = ctl.MoveMode.CL_ABSOLUTE
            ctl.SetProperty_i32(d_handle, 1, ctl.PropertyKey.MOVE_MODE, move_mode)
            ctl.SetProperty_i32(d_handle, 2, ctl.PropertyKey.MOVE_MODE, move_mode)

            ctl.SetProperty_i64(d_handle, 1, ctl.PropertyKey.MOVE_VELOCITY, 10000000)
            # Set move acceleration [in pm/s2].
            ctl.SetProperty_i64(d_handle, 1, ctl.PropertyKey.MOVE_ACCELERATION, 10000000)

            ctl.Move(d_handle, 1, x_pos, 0)


            ctl.SetProperty_i64(d_handle, 2, ctl.PropertyKey.MOVE_VELOCITY, 10000000)
            # Set move acceleration [in pm/s2].
            ctl.SetProperty_i64(d_handle, 2, ctl.PropertyKey.MOVE_ACCELERATION, 10000000)

            ctl.Move(d_handle, 2, y_pos, 0)


        except ctl.Error as e:
            print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}. Press return to exit."
                  .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code,
                          (sys.exc_info()[-1].tb_lineno)))

        except Exception as ex:
            print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))

## ---------------- If Attocube stage is used -----------------------------------------------------
    def stage_move_xy(x_pos, y_pos):
        try:

            for axis in sorted(ax.keys()):
                anc.setFrequency(ax[axis], 200)
                anc.setAmplitude(ax[axis], 20)

            anc.setAxisOutput(ax['x'], 1, 0)
            anc.setTargetRange(ax['x'], 1e-6)
            anc.setTargetPosition(ax['x'], x_pos)
            anc.startAutoMove(ax['x'], 1, 0)

            # check what's happening
            # time.sleep(0.5)
            moving = 1
            target = 0
            while target == 0:
                connected, enabled, moving, target, eotFwd, eotBwd, error = anc.getAxisStatus(
                    ax['x'])  # find bitmask of status
                if abs(anc.getPosition(ax['x']) - x_pos) > 0.1e-6:
                    target = 0
                elif target == 1:
                    print('axis arrived at', anc.getPosition(ax['x']))
                    anc.startAutoMove(ax['x'], 0, 0)
                time.sleep(0.5)

            anc.setAxisOutput(ax['y'], 1, 0)
            anc.setTargetRange(ax['y'], 0.25e-6)
            anc.setTargetPosition(ax['y'], y_pos)
            anc.startAutoMove(ax['y'], 1, 0)
            moving = 1
            target = 0
            count = 0
            while target == 0:  # and count < 500:
                connected, enabled, moving, target, eotFwd, eotBwd, error = anc.getAxisStatus(
                    ax['y'])  # find bitmask of status

                if abs(anc.getPosition(ax['y']) - y_pos) > 0.1e-6:
                    target = 0

                if target == 1:
                    anc.startAutoMove(ax['y'], 0, 0)
                    print('axis arrived at', anc.getPosition(ax['y']))
                count += 1

        except Exception as e:
            print(e)


    def stage_move_xy_slow(x_pos, y_pos):
        try:

            for axis in sorted(ax.keys()):
                anc.setFrequency(ax[axis], 100)
                anc.setAmplitude(ax[axis], 10)

            anc.setAxisOutput(ax['x'], 1, 0)
            anc.setTargetRange(ax['x'], 1e-6)
            anc.setTargetPosition(ax['x'], x_pos)
            anc.startAutoMove(ax['x'], 1, 0)

            # check what's happening
            # time.sleep(0.5)
            moving = 1
            target = 0
            while target == 0:
                connected, enabled, moving, target, eotFwd, eotBwd, error = anc.getAxisStatus(
                    ax['x'])  # find bitmask of status
                if abs(anc.getPosition(ax['x']) - x_pos) > 0.1e-6:
                    target = 0
                elif target == 1:
                    print('axis arrived at', anc.getPosition(ax['x']))
                    anc.startAutoMove(ax['x'], 0, 0)
                time.sleep(0.5)

            anc.setAxisOutput(ax['y'], 1, 0)
            anc.setTargetRange(ax['y'], 0.25e-6)
            anc.setTargetPosition(ax['y'], y_pos)
            anc.startAutoMove(ax['y'], 1, 0)
            moving = 1
            target = 0
            count = 0
            while target == 0:  # and count < 500:
                connected, enabled, moving, target, eotFwd, eotBwd, error = anc.getAxisStatus(
                    ax['y'])  # find bitmask of status

                if abs(anc.getPosition(ax['y']) - y_pos) > 0.1e-6:
                    target = 0

                if target == 1:
                    anc.startAutoMove(ax['y'], 0, 0)
                    print('axis arrived at', anc.getPosition(ax['y']))
                count += 1

        except Exception as e:
            print(e)





SpectrumAnalyzer.close()
SignalGenerator.close()