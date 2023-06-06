# Some generic packages we need
import os
import time
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

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
        self.PS.voltage = 20
        self.PS.current = 0
        self.LIA = SRS_SR830(ResourceName='ASRL4::INSTR', logFile=self._logFile)

        # Initial experiment parameters here
        self.parameters = None
        self.frequency_sweep = None
        self.field_sweep = None
        self.read_delay = 0.5

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
        parameters = {
            'Field Sweep': self.field_sweep,
            'Frequency Swep': self.frequency_sweep,
            'PS Output Current (A)': self.PS.MeasuredCurrent,
            'PS Output Voltage (V)': self.PS.MeasuredVoltage,
            'PS Output Mode (Current/Voltage)': self.PS.OperationMode,
            'SG Frequency': self.SG.frequency,
            'SG RF Output': self.SG.rf_output,
            'SG RF Output Level': self.SG.level,
            'LIA Sensitivity': self.LIA.SEN,
            'LIA Time Constant': self.LIA.TC,
            'Read Delay (s)': self.read_delay,
            'Log File': self._logFile}
        if not self.parameters:
            self.parameters = parameters
        else:
            self.parameters.update(parameters)

    def print_parameters(self):
        print('The parameters presently are:\n')
        self.update_parameters()
        for key, val in self.parameters.items():
            print(key, ':\t', val)

    def welcome(self):
        print("Welcome to the FMR Experiment!")
        print("You might want to update some experiment parameters.")
        self.print_parameters()

    def begin_sweep(self, constant_parameter='frequency'):
        '''constant_parameter can be "frequency" or "field"'''
        if (self.frequency_sweep is None) or (self.field_sweep is None):
            print('Set all parameters before beginning sweep.\n')
            self.print_parameters()
            return None
        
        if constant_parameter not in ['frequency', 'field']:
            self._log('ERR ', 'Sweep parameter Error! Valid inputs are "frequency" and "field".')
            print('ERR ', 'Sweep parameter Error! Valid inputs are "frequency" and "field".')
            return None
        
        self.print_parameters()
        begin_now = self.ask_begin_now()

        if not begin_now:
            return None
        elif constant_parameter == 'frequency':
            self.frequency_field()
        else:
            self.field_frequency()
    
    def ask_begin_now(self):
        begin_now = input('Do you want to begin sweep (Y/N)?\n')
        if begin_now not in ['Y', 'N']:
            print('Must enter either "Y(es)" or "N(o)". Try again.')
            return self.ask_begin_now()
        return [True, False][['Y', 'N'].index(begin_now)]
    
    def frequency_field(self):
        save_dir = self._get_save_dir()
        self._current_sweep = self.field2current(self.field_sweep)
        
        plt.ion()
        self.fig = plt.figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, 200)
        self.ax.set_ylim(-1, 1)
        self.l1, = self.ax.plot([], [])
        plt.show()

        for frequency in self.frequency_sweep:
            X_array = []
            Y_array = []
            self.SG.frequency = '{} GHz'.format(frequency)
            for i, curr in enumerate(self._current_sweep):
                self.PS.current = curr
                time.sleep(self.read_delay)
                X_array.append(self.LIA.X)
                Y_array.append(self.LIA.Y)
                self.update_line(self.field_sweep[0:i+1], X_array)
            df = pd.DataFrame({'current_A': self._current_sweep, 'field_Oe': self.field_sweep,
                               'X': X_array, 'Y': Y_array})
            df.to_csv(save_dir + '\\freq_{}_ghz_field_{}-{}_oe.csv'.format(frequency,
                                                                           self.field_sweep.min(),
                                                                           self.field_sweep.max()), index=False)
        self.PS.current = 0
        print('Sweep Complete!')
    
    def field_frequency(self):
        save_dir = self._get_save_dir()
        self._current_sweep = self.field2current(self.field_sweep)
        for curr in self._current_sweep:
            X_array = []
            Y_array = []
            self.PS.current = curr
            for frequency in self.frequency_sweep:
                self.SG.frequency = '{} GHz'.format(frequency)
                time.sleep(self.read_delay)
                X_array.append(self.LIA.X)
                Y_array.append(self.LIA.Y)
            df = pd.DataFrame({'frequency_ghz': self.frequency_sweep, 'X': X_array, 'Y': Y_array})
            df.to_csv(save_dir + '\\field_{}_oe.csv'.format(self.field_sweep[i]), index=False)
        self.PS.current = 0
        print("Sweep Complete!")

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

    def update_line(self, x_data, y_data):
        self.l1.set_xdata(x_data)
        self.l1.set_ydata(y_data)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()