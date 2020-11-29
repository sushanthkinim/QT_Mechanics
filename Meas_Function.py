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
            measurement.initialise_SA(startFreq, stopFreq, bW_Res, coupling, sweeppoints)
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

    def lorentzian_fit_QFactor(Lorentzian_span, peak_in, BW_res_Lorentzian,sweeppoints):
        try:
            averaging = 1
            time.sleep(1)
            for avg_time in [averaging]:
                trace = []
                trace_array = []
                data_watts = []
                y0 = []
                popt = []
                pcov =[]

                peak_UT = float(peak_in)
                SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
                SpectrumAnalyzer.write(":SENSe:FREQuency:SPAN " + str(Lorentzian_span) + "Hz")
                SpectrumAnalyzer.write(":SENSe:FREQuency:CENTer " + str(peak_UT) + "Hz")
                SpectrumAnalyzer.write("SENSe:BWIDth:RESolution " + str(BW_res_Lorentzian) + "Hz")
                time.sleep(1)#1
                SpectrumAnalyzer.write(":CALCulate:MARKer1:MAX")
                SpectrumAnalyzer.write(":CALCulate:MARKer1:SET:CENTer")
                SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
                time.sleep(20)#5
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
                Q = 0
                Gamma = 0

                # noise background for the fitting
                while k < background_pts:
                    sum_back = sum_back + data_watts[k] + data_watts[Npoints - k - 1]
                    k = k + 1

                sum_back = sum_back / (2 * background_pts)
                y0 = np.mean(sum_back)
                #y0 = np.min(data_watts)
                xi = []
                xi = np.argmax(data_watts[int(np.size(data_watts) / 2) - peak_window: int(np.size(data_watts) / 2) + peak_window: 1])
                xi = peak_UT + (xi - peak_window) / (Npoints / Lorentzian_span)
                x_fit = []
                x_fit = np.linspace(peak_UT - Lorentzian_span / 2, peak_UT + Lorentzian_span / 2, Npoints, endpoint=False)
                #popt = [0, 0]
                try:

                    def func_lorentzian(x, gam, A):
                        return y0 + (A / ((np.power(x - xi, 2)) + math.pow(gam, 2)))

                    def func_lorentzian_new(x, gam, A, y0):
                        return y0 + A * gam**2 / ((x - xi)**2 + gam**2)

                    guess = (1,1,y0)
                    if np.max(data_watts[int(np.size(data_watts) / 2) - peak_window: int(np.size(data_watts) / 2) + peak_window: 1]) / sum_back > 5:
                        popt, pcov = curve_fit(func_lorentzian_new, x_fit, data_watts,guess)
                        Gamma = abs(2 * math.pi * popt[0])
                        Q = 2 * math.pi * peak_UT * (1.0 / (2 * math.pi * abs(popt[0])))
                        #I = math.pi * popt[1] / popt[0]
                        #I_err = I * np.sqrt((pcov[0, 0] / popt[0] ** 2) + (pcov[1, 1] / popt[1] ** 2))
                    else:
                        continue
                except RuntimeError:
                    I = 1e-13
                    I_err = 1e-13

                y_fit = np.array(func_lorentzian_new(x_fit, abs(popt[0]),popt[1], popt[2]))
                y_back = np.full((1,len(x_fit)),popt[2])
                plt.semilogy(x_fit, y_fit, 'b', label='Q = ' + str(int(Q)) ,linewidth=2.0)
                plt.semilogy(x_fit, data_watts, 'r', Linewidth=0.5)
                #plt.semilogy([x_fit[0], x_fit[-1]], [y_back[0], y_back[-1]], 'g-', Linewidth=0.5)
                plt.hlines(popt[2],x_fit[0],x_fit[-1],linestyles='dashed',colors='g')
                plt.xlabel('Freq [Hz]')
                plt.ylabel('log(Power) [a.u.]')
                plt.legend()
                plt.savefig('Q_fit ' + str(float(peak_in)) + '.pdf')
                plt.close()
                #print(*popt)
            return [Q, Gamma, trace]
            #return fig
        except Exception as e:
                    print(e)

    def ringdown_Qfactor(peak_UT,Npoints):

        try:
            peak_in = float(peak_UT)
            BW = 1000
            sweep_time = 2
            peak_peak_voltage = 0.0025
            SpectrumAnalyzer = resourceManager.open_resource(VISA_ADDRESS_SA)
            SignalGenerator = resourceManager.open_resource(VISA_ADDRESS_SG)

            SignalGenerator.write(":SOURce1:VOLTage " + str(peak_peak_voltage))
            SignalGenerator.write(":SOURce1:FREQuency " + str(int(peak_in)))
            SignalGenerator.write("OUTPut1 1")

            #Set zero-span in spectrum analyzer
            SpectrumAnalyzer.write("SENSe:BWIDth:RESolution " + str(BW) + "Hz")
            SpectrumAnalyzer.write(":SENSe:FREQuency:SPAN 0")
            SpectrumAnalyzer.write(":SENSe:SWEep:TIME " + str(sweep_time))
            SpectrumAnalyzer.write(":SENSe:FREQuency:CENT " + str(peak_in) + "Hz")
            SpectrumAnalyzer.write(":SENSe:SWEep:TIME " + str(0.01))
            SpectrumAnalyzer.write(":TRAC1:TYPE WRIT")
            time.sleep(1)

            peak_shift = 0
            peak_shift_prev = 0
            multiply_V = 2
            timestep = 0.2
            search_window = 100 * math.ceil(peak_in / 50000)
            abs_diff = 0
            abs_diff_prev = abs_diff - 10
            flag = 0

            while (abs_diff < 15 or (abs_diff - abs_diff_prev > 3 and abs_diff < 20) or (
                    math.fabs(peak_shift - peak_shift_prev) > 2)) and flag == 0 and abs_diff < 20:
                SignalGenerator.write(":SOURce1:VOLTage " + str(peak_peak_voltage))
                time.sleep(1)
                peak_pow = np.empty(shape=[search_window, 1])

                j = 0
                while j < search_window:
                    SignalGenerator.write(":SOURce1:FREQuency " + str(int(peak_in + j - search_window / 2.0)))
                    if j == 0:
                        time.sleep(3)
                    time.sleep(timestep)
                    SpectrumAnalyzer.write("CALC:MARK1:Y?")
                    peak_pow[j] = SpectrumAnalyzer.read()
                    # print(peak_pow2[j])
                    j = j + 1
                    #print(j)
                peak_shift_prev = peak_shift
                peak_shift = np.argmax(peak_pow) - int(search_window / 2)
                abs_diff_prev = abs_diff
                abs_diff = np.max(peak_pow) - (np.average(peak_pow[0:int(search_window / 10):1]) + np.average(
                    peak_pow[search_window - int(search_window / 10): search_window:1])) / 2.0

                peak_peak_voltage = peak_peak_voltage * multiply_V

                if peak_peak_voltage > 5.5:
                    flag = 1

            if flag == 0:
                corrected_peak = int(peak_in) + peak_shift
                print("corrected_peaks: " + str(corrected_peak))
            else:
                corrected_peak = int(peak_in)
            time.sleep(1)

            window = np.linspace(0, search_window - 1, search_window)
            plt.plot(window, peak_pow, 'r-o', label='Forward Sweep')
            plt.xlabel('Frequency [Hz]')
            plt.ylabel('log(Power) [a.u.]')
            plt.legend()
            plt.savefig('ShiftSweep_' + str(peak_in) + '.pdf')
            plt.close()

            #Start Burst mode
            Gen_peak = corrected_peak
            SignalGenerator.write(":SOURce1:FREQuency " + str(Gen_peak))
            time.sleep(2)
            Ncycles_array = [10, 15, 20]
            index = 0
            Q_RD = []

            if flag == 0:
                for l in Ncycles_array:
                    # calculate background noise level
                    index = index + 1
                    BURST_V = 5
                    PER = 2
                    Ncycles = l + 5 + l * (peak_peak_voltage / 2) / 0.005
                    SpectrumAnalyzer.write(":TRIG:SOUR IMM")
                    SignalGenerator.write('BURST OFF')
                    SignalGenerator.write("OUTPut1 0")
                    SpectrumAnalyzer.write(":TRAC1:TYPE WRIT")
                    SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
                    time.sleep(5)
                    SpectrumAnalyzer.write(":TRAC? TRACE1")
                    backgnd_temp = SpectrumAnalyzer.read()
                    backgnd_temp = tuple(backgnd_temp.split(','))
                    backgnd_array = np.array(backgnd_temp, np.float)
                    avg_noise = np.average(backgnd_array)
                    # start Burst
                    SignalGenerator.write("OUTPut1 1")
                    SignalGenerator.write(":SOURce1:BURSt:STATe ON")
                    SignalGenerator.write(":SOURce1:VOLTage " + str(BURST_V))
                    SignalGenerator.write(":SOURce1:BURSt:NCYCLes " + str(Ncycles))
                    SignalGenerator.write(":SOURce1:BURSt:INT:PER " + str(PER / 2))
                    SpectrumAnalyzer.write(":SENSe:SWEep:TIME " + str(PER))
                    SpectrumAnalyzer.write(":TRAC1:TYPE WRIT")
                    time.sleep(PER * 2)
                    SpectrumAnalyzer.write(":CALCulate:MARKer1:MAX")
                    SpectrumAnalyzer.write("CALC:MARK1:Y?")
                    Y = SpectrumAnalyzer.read()
                    tri_peak = np.array(Y, np.float)
                    SpectrumAnalyzer.write(":TRIG:SOUR VID")
                    SpectrumAnalyzer.write("TRIG:VID:LEV " + str(tri_peak - 3))
                    time.sleep(PER * 3)

                    reduce_span = int(Npoints / 10)
                    SpectrumAnalyzer.write(":TRAC? TRACE1")
                    ringdown_temp = SpectrumAnalyzer.read()
                    ringdown_temp = tuple(ringdown_temp.split(','))
                    ringdown_array = np.array(ringdown_temp, np.float)
                    ringdown_arrayf = ringdown_array[reduce_span:Npoints - reduce_span:1]
                    start_index = np.argmax(ringdown_arrayf)
                    peak_index = start_index
                    end_index = Npoints - reduce_span
                    delta = np.max(ringdown_arrayf) - avg_noise
                    print("peak " + str(peak_index))
                    new_index = int((start_index + end_index) / 2)
                    delta_2 = ringdown_arrayf[new_index] - avg_noise
                    upper_limit = delta - 6
                    lower_limit = delta - 10
                    count_stuck = 0
                    while count_stuck < 100 and (delta_2 < lower_limit or delta_2 > upper_limit):
                        if delta_2 < lower_limit:
                            end_index = new_index
                            new_index = int((start_index + new_index) / 2)
                        else:
                            start_index = new_index
                            new_index = int((end_index + new_index) / 2)
                        delta_2 = ringdown_arrayf[new_index] - avg_noise
                        count_stuck = count_stuck + 1
                        #print("delta2 " + str(delta_2))
                        #print("index" + str(new_index))

                    slope = -(delta - delta_2) / (peak_index - new_index)
                    x_width = delta / slope
                    #print("x_wid" + str(x_width))
                    PER = round(x_width * 4 * PER / Npoints, 1)
                    #print("PER " + str(PER))
                    #file_log.write('period: ' + str(PER) + '\n')
                    SignalGenerator.write(":SOURce1:BURSt:INT:PER " + str(PER / 2))
                    SpectrumAnalyzer.write(":SENSe:SWEep:TIME " + str(PER))
                    SpectrumAnalyzer.write(":TRAC1:TYPE AVER")
                    time.sleep(PER * 5)

                    SpectrumAnalyzer.write(":TRAC? TRACE1")
                    ringdown_temp = SpectrumAnalyzer.read()
                    ringdown_temp1 = tuple(ringdown_temp.split(','))
                    ringdown_array = np.array(ringdown_temp1, np.float)
                    data = ringdown_array[reduce_span:Npoints - reduce_span:1]

                    # passdataQ = open(chipname + '_' + sample + '_Qfactor_' + str(peak_in) + '_' + str(Ncycles) + '.csv',
                    #                  'w')
                    # passdataQ.write(ringdown_temp)
                    # passdataQ.close()

                    # start fitting ringdown
                    x = np.linspace(0, PER, Npoints - reduce_span * 2)
                    data_watts = np.power(10, (data - 30) / 10)
                    data_in = np.log(data_watts)
                    x_fit = x[np.argmax(data) + int(Npoints / 40): np.argmax(data) + int(Npoints / 10): 1]
                    data_fit = data_in[np.argmax(data) + int(Npoints / 40): np.argmax(data) + int(Npoints / 10): 1]

                    def func(x, y0, m, x0):
                        return y0 - m * (x - x0)

                    popt, pcov = curve_fit(func, x_fit, data_fit)
                    Q = int(2 * math.pi * int(peak_in) * (1.0 / popt[1]))

                    #file_log.write('Q_ring: ' + str(Q) + '\n')
                    #file2.write(str(Q) + '\t')
                    plt.plot(x_fit, func(x_fit, *popt), 'r--', label='Q = ' + str(Q), linewidth=3.0)
                    plt.plot(x, data_in, 'b')
                    plt.xlabel('time [s]')
                    plt.ylabel('Power')
                    plt.legend()
                    plt.savefig('Ringdown with ' + str(Ncycles) + ' cycles Freq -' + str(peak_in) + '.pdf')
                    Q_RD.append(Q)
                    plt.close()
                    SpectrumAnalyzer.write(":TRIG:SOUR IMM")
                    SignalGenerator.write('BURST OFF')
                    SpectrumAnalyzer.write(":TRAC1:TYPE WRIT")
                    SignalGenerator.write("OUTPut1 0")

                return Q_RD, x_fit.tolist(), data_fit.tolist(), data_in.tolist()

            if flag == 1:
                Q_RD = [1,1,1]
                return Q_RD, 1, 1, 1
                    # plt.show()
                    #plt.close()
        except Exception as e:
            print(e)


# Graphical point picker, picks three points
def get_points(xmin, xmax, ymin, ymax, showGuide=True):

    fig, ax = plt.subplots()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.axis('equal')
    
    if showGuide:
        t = np.linspace(0, 2*np.pi)
        r = (xmin - xmax) / 2
        c_x, c_y = (xmin + xmax) / 2, (ymin + ymax) / 2
        x = c_x + r*np.cos(t)
        y = c_y + r*np.sin(t)
        ax.plot(x,y,"--k")

    print("Click on the plot three times. Right-click removes last point.")
    points = fig.ginput(3)
    plt.close()
    points = [(int(x), int(y)) for (x,y) in points]
    return points

def frequency_chooser(freqs):
    # Print selection dialog
    print(" ====== select frequencies ======")
    for i in range(len(freqs)):
        print(f"{i:2d}: {float(freqs[i])/1000:.1f} kHz")
    print("Which frequencies do you want to measure?")
    # Get input
    indices = input("Enter a list of integers, separated by commas: ")
    # Validate input, get new if invalid
    done = False
    while not done:
        try:
            str_array = indices.split(",")
            ind_array = [int(str_index) for str_index in str_array]
            filtered_freqs = [freqs[ind] for ind in ind_array]
        except (ValueError, IndexError):
            indices = input("Invalid, try again: ")
        else:
            done = True

    return filtered_freqs


def plot_the_NPS(traces, startFreq, stopFreq, final_list):
    n = len(traces[0])
    xaxis = np.linspace(startFreq, stopFreq, n)

    fig, axs = plt.subplots(3,1,sharex=True)


    arrowprops = {'width': 1, 'headwidth': 1, 'headlength': 1, 'shrink':0.05 }
    for i in range(len(axs)):
        axs[i].plot(xaxis, traces[i], color='blue')
        axs[i].set(xlabel='Frequency', ylabel=f'NPS at point {i}')
        for j in range(len(final_list)):
            x = final_list[j]
            ind = round((x - startFreq) / (stopFreq - startFreq) * n)
            y = np.max(traces[i][ind-1:ind+2])
            #ax.axvline(x=x, color='k', linestyle='--')
            axs[i].annotate(str(j), xy=(x, y), xytext=(-5, 8), textcoords='offset points',
                rotation=0, va='bottom', ha='center', annotation_clip=False, arrowprops=arrowprops)


    #if savedir[-1] != "/":
     #   savedir += "/"
    plt.savefig('NPS.pdf', format='pdf', dpi=300)

    return fig

    plt.tight_layout()




SpectrumAnalyzer.close()
SignalGenerator.close()
