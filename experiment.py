# Some generic packages we need
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Let's import our instrument classes
from hp_8673g import HP_CWG
from srs_sr830_RS232 import SRS_SR830
from bop50_8d import KEPCO_BOP

class Experiment():
    def __init__(self, logFilePath=None):
        now = datetime.now()
        self.timestring = '{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
        
        if not logFilePath:
            logFilePath = './Experiment_Logs/FMR_log_' + self.timestring + '.log'
            with open(logFilePath, 'w') as log:
                log.write('SpinLab Experiment Logfile' + self.timestring + '\n')
        elif not os.path.isfile(logFilePath):
            with open(logFilePath, 'w') as log:
                log.write('SpinLab Instruments LogFile' + self.timestring + '\n')
        self._logFile = os.path.abspath(logFilePath)
        self._logWrite('OPEN_')

        # Initialise our Instruments
        self.SG = HP_CWG(logFile=self._logFile)
        self.PS = KEPCO_BOP(logFile=self._logFile)
        self.PS.CurrentMode()
        self.PS.voltage = 40
        self.PS.current = 0
        self.LIA = SRS_SR830(ResourceName='ASRL4::INSTR', logFile=self._logFile)

        self.read_delay = 1
        self.from_0_delay = 5
        self.sensitivity_delay = 5
        self.default_sensitivity = 0.0002
        self.read_repetitions = 30
        self.read_repetition_delay = 0.1

        self.welcome()

    def __del__(self):
        self._logWrite('CLOSE')
        del self.PS
        del self.SG
        del self.LIA

    def __str__(self):
        return 'FMR Experiment @ ' + self.timestring
    
    def _logWrite(self, action, value=''):
            if self._logFile is not None:
                with open(self._logFile, 'a') as log:
                    timestamp = datetime.utcnow()
                    log.write('%s %s : %s \n' % (timestamp, action, repr(value)))
    _log = _logWrite

    def update_parameters(self):
        self.parameters = {
            'PS Output Current (A)': self.PS.MeasuredCurrent,
            'PS Output Voltage (V)': self.PS.MeasuredVoltage,
            'PS Output Mode (Current/Voltage)': self.PS.OperationMode,
            'SG Frequency': self.SG.frequency,
            'SG RF Output': self.SG.rf_output,
            'SG RF Output Level': self.SG.level,
            'LIA Sensitivity': self.LIA.SEN,
            'Default Sensitivity': self.default_sensitivity,
            'LIA Time Constant': self.LIA.TC,
            'Read Delay (s)': self.read_delay,
            'From 0 Delay (s)': self.from_0_delay,
            'Sensivity Delay (s)': self.sensitivity_delay,
            'Read Repetition Delay': self.read_repetition_delay,
            'Read Repetitions': self.read_repetitions,
            'Log File': self._logFile}


    def print_parameters(self):
        print('The parameters presently are:\n')
        self.update_parameters()
        for key, val in self.parameters.items():
            print(key, ':\t', val)


    def welcome(self):
        print("Welcome to the FMR Experiment!")
        print("You might want to update some experiment parameters.")
        self.print_parameters()


    def multisweep(self, primary_parameter=None, save_dir=None, fields=None, frequencies=None, closefig=True, savefig=True, reset_sens=True):
        '''constant_parameter can be "frequency" or "field"'''
        if (frequencies is None) or (fields is None):
            self._log('ERR ', 'Sweep parameter Error! Valid inputs are "frequency" and "field".')
            print('Error: You must pass in your frequency and field ranges.\n')
            return None
        if primary_parameter not in ['frequency', 'field']:
            self._log('ERR ', 'Primary Parameter Error! Choose whether "frequency" or "field" will be primary.')
            print('Error: Primary Parameter Error! Choose whether "frequency" or "field" will be primary.')
            return None
        if save_dir is None:
            save_dir = self._get_save_dir()
        
        if primary_parameter == 'frequency':
            for frequency, field_range in zip(frequencies, fields):
                self.sweep_field(frequency, field_range, save_dir=save_dir, closefig=closefig, savefig=savefig, default_sen=reset_sens)

        else:
            for field, frequency_range in zip(fields, frequencies):
                self.sweep_frequency(field, frequency_range, save_dir=save_dir, closefig=closefig, savefig=savefig, default_sen=reset_sens)


    def uniform_multisweep(self, primary_parameter=None, save_dir=None, fields=None, frequencies=None, closefig=True, savefig=True, reset_sens=True):
        '''constant_parameter can be "frequency" or "field"'''
        if (frequencies is None) or (fields is None):
            self._log('ERR ', 'Sweep parameter Error! Valid inputs are "frequency" and "field".')
            print('Error: You must pass in your frequency and field ranges.\n')
            return None
        if primary_parameter not in ['frequency', 'field']:
            self._log('ERR ', 'Primary Parameter Error! Choose whether "frequency" or "field" will be primary.')
            print('Error: Primary Parameter Error! Choose whether "frequency" or "field" will be primary.')
            return None
        if save_dir is None:
            save_dir = self._get_save_dir()
        
        if primary_parameter == 'frequency':
            for frequency in frequencies:
                self.sweep_field(frequency, fields, save_dir=save_dir, closefig=closefig, savefig=savefig, default_sen=reset_sens)
        else:
            for field in fields:
                self.sweep_frequency(field, frequencies, save_dir=save_dir, closefig=closefig, savefig=savefig, default_sen=reset_sens)
    
    def sweep_field(self, frequency, fields, save_dir=None, savefig=True, closefig=False, default_sen=True):
        if default_sen:
            self.LIA.SEN = self.default_sensitivity
        if save_dir is None:
            save_dir = self._get_save_dir()
        else:
            if not os.path.isdir(save_dir):
                os.mkdir(save_dir)
        self.SG.frequency = '{} GHz'.format(frequency)
        currents = self.field2current(fields)
        # Janky solution to the current not immediately jumping from 0 to first value
        self.PS.current = currents[0]
        time.sleep(self.from_0_delay)
        plot_title = 'Field Sweep {:.4g}–{:.4g} Oe @ {:.4g} GHz'.format(fields.min(), fields.max(), frequency)
        self.make_fig(plot_title, 'Field (Oe)', 'Voltage (AU)')
        X_array, Y_array = [], []
        for i, current in enumerate(currents):
            self.PS.current = current
            time.sleep(self.read_delay)
            X_array.append(self.readLIA('X', 'mean mid-50'))
            Y_array.append(self.readLIA('Y', 'mean mid-50'))
            self.update_plot(fields[0:i + 1], X_array, Y_array)
        df = pd.DataFrame({'current_A': currents, 'field_Oe': fields, 'X': X_array, 'Y': Y_array})
        filename = r'\freq_{:.4g}_GHz_field_{:.4g}-{:.4g}_Oe'.format(frequency, fields.min(), fields.max())
        df.to_csv(save_dir + filename + '.csv', index=False)
        self.PS.current = 0
        if closefig:
            plt.close(self.fig)
        if savefig:
            self.fig.savefig(save_dir + filename + '.png', dpi=1200)

    def sweep_frequency(self, field, frequencies, save_dir=None, savefig=True, closefig=False, default_sen=True):
        if default_sen:
            self.LIA.SEN = self.default_sensitivity
        if save_dir is None:
            save_dir = self._get_save_dir()
        else:
            if not os.path.isdir(save_dir):
                os.mkdir(save_dir)
        current = self.field2current(field)
        # Janky solution to the current not immediately jumping from 0 to first value
        self.PS.current = current
        self.SG.frequency = '{} GHz'.format(frequencies[0])
        time.sleep(self.from_0_delay)
        plot_title = 'Frequency Sweep {:.4g}–{:.4g} GHz @ {:.4g} Oe'.format(frequencies.min(), frequencies.max(), field)
        self.make_fig(plot_title, 'Frequency (GHz)', 'Voltage (AU)')
        X_array, Y_array = [], []
        for i, frequency in enumerate(frequencies):
            self.SG.frequency = '{} GHz'.format(frequency)
            time.sleep(self.read_delay)
            X_array.append(self.readLIA('X', 'mean mid-50'))
            Y_array.append(self.readLIA('Y', 'mean mid-50'))
            self.update_plot(frequencies[0:i + 1], X_array, Y_array)
        df = pd.DataFrame({'frequency_ghz': frequencies, 'X': X_array, 'Y': Y_array})
        filename = r'\field_{:.4g}_Oe_freq_{:.4g}-{:.4g}_GHz'.format(field, frequencies.min(), frequencies.max())
        df.to_csv(save_dir + filename + '.csv', index=False)
        self.PS.current = 0
        if closefig:
            plt.close(self.fig)
        if savefig:
            self.fig.savefig(save_dir + filename + '.png', dpi=1200)


    def _get_save_dir(self):
        save_dir = input("Please enter the directory path where you'd like to save your files. It's always good to give it a good name that you'll recognise later.\n")
        save_dir = os.path.abspath(save_dir)

        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        return save_dir
    

    def field2current(self, field):
        return field / 669
    
    def current2field(self, current):
        return current * 669
    

    def make_fig(self, title, xlabel, ylabel):
        self.fig = plt.figure(figsize=(9, 6))
        self.ax = self.fig.add_subplot(111)

        self.l1, = self.ax.plot([], [], alpha=0.5, label='Channel 1 (X)')
        self.l2, = self.ax.plot([], [], alpha=0.5, label='Channel 2 (Y)')
        self.sc1 = self.ax.scatter([], [], s=10)
        self.sc2 = self.ax.scatter([], [], s=10)

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        plt.show()

    def update_plot(self, xdata, ch1_data, ch2_data):
        self.l1.remove()
        self.l2.remove()
        self.sc1.remove()
        self.sc2.remove()

        self.l1, = self.ax.plot(xdata, ch1_data, alpha=0.5, label='Channel 1 (X)', color='green')
        self.l2, = self.ax.plot(xdata, ch2_data, alpha=0.5, label='Channel 2 (Y)', color='purple')
        self.sc1 = self.ax.scatter(xdata, ch1_data, s=10, c='green')
        self.sc2 = self.ax.scatter(xdata, ch2_data, s=10, c='purple')

        self.ax.set_xlim(min(xdata), max(xdata))
        min_y = min(min(ch1_data), min(ch2_data))
        max_y = max(max(ch1_data), max(ch2_data))
        self.ax.set_ylim(min_y - 0.05 * abs(min_y), max_y + 0.05 * abs(max_y))

        self.ax.legend()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def readX(self):
        X_arr = np.array([], dtype=float)
        for i in range(self.read_repetitions):
            X_arr = np.append(X_arr, self.LIA.X)
            time.sleep(self.read_repetition_delay)
        X = np.average(X_arr)
        sen_ratio = abs(X)/self.LIA.SEN
        if sen_ratio > 0.8:
            self.LIA.decrease_sensitivity()
            time.sleep(self.sensitivity_delay)
        return X
    
    def readY(self):
        Y_arr = np.array([], dtype=float)
        for i in range(self.read_repetitions):
            Y_arr = np.append(Y_arr, self.LIA.Y)
            time.sleep(self.read_repetition_delay)
        Y = np.average(Y_arr)
        sen_ratio = abs(Y)/self.LIA.SEN
        if sen_ratio > 0.8:
            self.LIA.decrease_sensitivity()
            time.sleep(self.sensitivity_delay)
        return Y
    
    def readLIA(self, channel, averaging):
        read_command = [self.LIA.X, self.LIA.Y][['X', 'Y'].index(channel)]
        avg_func = [np.average, self.avg_mid_50][['mean', 'mean mid-50'].index(averaging)]

        arr = np.array([], dtype=float)
        for i in range(self.read_repetitions):
            arr = np.append(arr, read_command())
            time.sleep(self.read_repetition_delay)
        val = avg_func(arr)

        sen_ratio = abs(val)/self.LIA.SEN
        if sen_ratio > 0.8:
            self.LIA.decrease_sensitivity()
            time.sleep(self.sensitivity_delay)
        return val
    
    def avg_mid_50(self, arr):
        return np.mean(arr[np.logical_and(arr >= np.percentile(arr, 25), arr <= np.percentile(arr, 75))])


### Here lie some helper functions

def get_midpoint(csv_path, channel='both'):
    df = pd.read_csv(csv_path)
    if 'field_Oe' in df.columns:
        parameter = 'field_Oe'
    else:
        parameter = 'frequency_ghz'
    minX = df.iloc[df['X'].idxmin()][parameter]
    maxX = df.iloc[df['X'].idxmax()][parameter]
    minY = df.iloc[df['Y'].idxmin()][parameter]
    maxY = df.iloc[df['Y'].idxmax()][parameter]

    midpoint_X = (minX + maxX) / 2
    midpoint_Y = (minY + maxY) / 2
    if channel == 'X':
        return midpoint_X
    if channel == 'Y':
        return midpoint_Y
    if channel == 'both':
        return (midpoint_X + midpoint_Y) / 2
    print('Channel Error! Atgument channel must be "X", "Y", or "both".')
    return None