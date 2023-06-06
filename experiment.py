# Some generic packages we need
import os
import time
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
        self.PS.voltage = 20
        self.PS.current = 0
        self.LIA = SRS_SR830(ResourceName='ASRL4::INSTR', logFile=self._logFile)

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
        self.parameters = {
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


    def print_parameters(self):
        print('The parameters presently are:\n')
        self.update_parameters()
        for key, val in self.parameters.items():
            print(key, ':\t', val)


    def welcome(self):
        print("Welcome to the FMR Experiment!")
        print("You might want to update some experiment parameters.")
        self.print_parameters()


    def multisweep(self, primary_parameter=None, save_dir=None, fields=None, frequencies=None, closefig=True, savefig=False):
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
                self.sweep_field(frequency, field_range, save_dir=save_dir, closefig=closefig, savefig=savefig)
        else:
            for field, frequency_range in zip(fields, frequencies):
                self.sweep_frequency(field, frequency_range, save_dir=save_dir, closefig=closefig, savefig=savefig)


    def uniform_multisweep(self, primary_parameter=None, save_dir=None, fields=None, frequencies=None, closefig=True, savefig=False):
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
                self.sweep_field(frequency, fields, save_dir=save_dir, closefig=closefig, savefig=savefig)
        else:
            for field in fields:
                self.sweep_frequency(field, frequencies, save_dir=save_dir, closefig=closefig, savefig=savefig)
    
    def sweep_field(self, frequency, fields, save_dir=None, savefig=False, closefig=False):
        if save_dir is None:
            save_dir = self._get_save_dir()
        else:
            if not os.path.isdir(save_dir):
                os.mkdir(save_dir)
        self.SG.frequency = '{} GHz'.format(frequency)
        plot_title = 'Field Sweep {}–{} Oe @ {} GHz'.format(fields.min(), fields.max(), frequency)
        self.make_fig(plot_title)
        X_array, Y_array = [], []
        currents = self.field2current(fields)
        for i, current in enumerate(currents):
            self.PS.current = current
            time.sleep(self.read_delay)
            X_array.append(self.readX())
            Y_array.append(self.readY())
            self.update_plot(fields[0:i + 1], X_array, Y_array)
        df = pd.DataFrame({'current_A': currents, 'field_Oe': fields, 'X': X_array, 'Y': Y_array})
        filename = r'\freq_{}_GHz_field_{}–{}_Oe'.format(frequency, fields.min(), fields.max())
        df.to_csv(save_dir + filename + '.csv', index=False)
        self.PS.current = 0
        if closefig:
            plt.close(self.fig)
        if savefig:
            self.fig.savefig(save_dir + filename + '.png')

    def sweep_frequency(self, field, frequencies, save_dir=None, savefig=False, closefig=False):
        if save_dir is None:
            save_dir = self._get_save_dir()
        else:
            if not os.path.isdir(save_dir):
                os.mkdir(save_dir)
        current = self.field2current(field)
        self.PS.current = current
        X_array, Y_array = [], []
        plot_title = 'Frequency Sweep {}–{} GHz @ {} Oe'.format(frequencies.min(), frequencies.max(), field)
        self.make_fig(plot_title)
        for i, frequency in enumerate(frequencies):
            self.SG.frequency = '{} GHz'.format(frequency)
            time.sleep(self.read_delay)
            X_array.append(self.readX())
            Y_array.append(self.readY())
            self.update_plot(frequencies[0:i + 1], X_array, Y_array)
            df = pd.DataFrame({'frequency_ghz': frequencies, 'X': X_array, 'Y': Y_array})
            filename = r'\field_{}_Oe_freq_{}–{}_GHz'.format(field, frequencies.min(), frequencies.max())
            df.to_csv(save_dir + filename + '.csv', index=False)
        self.PS.current = 0
        if closefig:
            plt.close(self.fig)
        if savefig:
            self.fig.savefig(save_dir + filename + '.png')


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
    

    def make_fig(self, title):
        self.fig = plt.figure(figsize=(9, 6))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Field (Oe)')
        self.ax.set_ylabel('Voltage (AU)')
        self.ax.set_title(title)
        self.l1, = self.ax.plot([], [], label='Channel 1 (X)')
        self.l2, = self.ax.plot([], [], label='Channel 2 (Y)')
        plt.legend()
        plt.show()

    def update_plot(self, xdata, ch1_data, ch2_data):
        self.l1.set_xdata(xdata)
        self.l1.set_ydata(ch1_data)

        self.l2.set_xdata(xdata)
        self.l2.set_ydata(ch2_data)

        self.ax.set_xlim(min(xdata), max(xdata))
        self.ax.set_ylim(min(min(ch1_data), min(ch2_data)), max(max(ch1_data), max(ch2_data)))

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def readX(self):
        X = self.LIA.X
        sen_ratio = abs(X)/self.LIA.SEN
        if sen_ratio > 0.8:
            self.LIA.decrease_sensitivity()
            time.sleep(5)
        return X
    
    def readY(self):
        Y = self.LIA.Y
        sen_ratio = abs(Y)/self.LIA.SEN
        if sen_ratio > 0.8:
            self.LIA.decrease_sensitivity()
            time.sleep(5)
        return Y