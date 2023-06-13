# Some generic packages we need
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Let's import our instrument classes
from hp_8673g import HP_CWG
from srs_sr830 import SRS_SR830
from bop50_8d import KEPCO_BOP

class Experiment():
    def __init__(self, logFilePath=None):
        if logFilePath is None:
            if not os.path.isdir(os.path.abspath('./Experiment_Logs')):
                os.mkdir(os.path.abspath('./Experiment_Logs'))
            logFilePath = './Experiment_Logs/FMR_log_{}.log'.format(self._get_timestring())
        with open(logFilePath, 'w') as log:
            log.write('SpinLab Instruments LogFile @ {}'.format(datetime.utcnow()) + '\n')
        self._logFile = os.path.abspath(logFilePath)
        self._logWrite('OPEN_')

        # Initialise our Instruments
        self.SG = HP_CWG(logFile=self._logFile)
        self.PS = KEPCO_BOP(logFile=self._logFile)
        self.LIA = SRS_SR830(logFile=self._logFile)

        # Some initial PS settings
        self.PS.CurrentMode()
        self.PS.voltage = 40
        self.PS.current = 0
        
        # Various delays here
        
        self.sen = 0.0002
        self.sen_delay = 3
        self.read_reps = 1
        self.rep_delay = 0
        self.avg_func = np.mean
        self.read_delay = 0.02
        self.from0delay = 4

        self._welcome()

    
    def __del__(self):
        self._logWrite('CLOSE')
        del self.PS
        del self.SG
        del self.LIA

    def __str__(self):
        return 'FMR Experiment @ ' + datetime.utcnow()
    
    def _logWrite(self, action, value=''):
            if self._logFile is not None:
                with open(self._logFile, 'a') as log:
                    timestamp = datetime.utcnow()
                    log.write('%s %s : %s \n' % (timestamp, action, repr(value)))
    _log = _logWrite        

    def _welcome(self):
        print("Welcome to the FMR Experiment!")
        print("Here are some default experiment parameters.\n")
        self._print_parameters()
        
    def _print_parameters(self):
        parameters = {
            'PS Output Current (A)': self.PS.MeasuredCurrent,
            'PS Output Voltage (V)': self.PS.MeasuredVoltage,
            'PS Output Mode (Current/Voltage)': self.PS.OperationMode,
            'SG Frequency': self.SG.frequency,
            'SG RF Output': self.SG.rf_output,
            'SG RF Output Level': self.SG.level,
            'LIA Time Constant': self.LIA.TC,
            'LIA Sensivity': self.sen,
            'Sensivity Delay (s)': self.sen_delay,
            'Read Repetitions': self.read_reps,
            'Read Repetition Delay': self.rep_delay,
            'Repetition Averaging Function': self.avg_func,
            'Read Delay': self.read_delay,
            'From 0 Delay (s)': self.from0delay,
            'Log File': self._logFile}
        for key, val in parameters.items():
            print(key, ':\t', val)

    def _get_timestring(self):
        now = datetime.now()
        return '{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    
    def _get_sen(self, sen):
        if sen is None:
            sen = self.sen
        return sen
    
    def _get_sen_delay(self, sen_delay):
        if sen_delay is None:
            sen_delay = self.sen_delay
        return sen_delay
    
    def _get_read_reps(self, read_reps):
        if read_reps is None:
            read_reps = self.read_reps
        return read_reps
    
    def _get_rep_delay(self, rep_delay):
        if rep_delay is None:
            rep_delay = self.rep_delay
        return rep_delay
    
    def _get_avg_func(self, avg_func):
        if avg_func is None:
            avg_func = self.avg_mid_50
        return avg_func
    
    def _get_read_delay(self, read_delay):
        if read_delay is None:
            read_delay = self.read_delay
        return read_delay
    
    def _get_from0delay(self, from0delay):
        if from0delay is None:
            from0delay = self.from0delay
        return from0delay


    def sweep_field(self, frequency, fields, save_dir, livefig=True, savefig=True, closefig=False,
                    file_prefix='', sen=0.002, sen_delay=None, read_reps=None, rep_delay=None,
                    read_delay=None, from0delay=None, avg_func=None, return_XY=False):
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        currents = self.field2current(fields)

        # Janky solution to the current not immediately jumping from 0 to first value
        self.SG.set_frequency_ghz(frequency)
        self.PS.set_current(currents[0])
        time.sleep(self._get_from0delay(from0delay))

        filename = file_prefix + r'freq_{:.4g}_GHz_field_{:.4g}-{:.4g}_Oe_{:.4g}_dB'.format(
            frequency, fields.min(), fields.max(), float(self.SG.level[2:-2]))
        
        if livefig:
            plot_title = 'Field Sweep {:.4g} – {:.4g} Oe @ {:.4g} GHz, {:.4g} dB'.format(
                fields.min(), fields.max(), frequency, float(self.SG.level[2:-2]))
            self._make_fig(plot_title, 'Field (Oe)', 'Voltage (AU)')
            
        x_arr, y_arr = self._sweep_parameter(currents, self.PS.set_current, save_dir, livefig,
                                             savefig, closefig, sen, sen_delay, read_reps,
                                             rep_delay, read_delay, avg_func, fields, filename)
        
        df = pd.DataFrame({'current_A': currents, 'field_Oe': fields, 'X': x_arr, 'Y': y_arr})
        df.to_csv(save_dir + r'\\' + filename + '.csv', index=False)

        if return_XY:
            return x_arr, y_arr
        
    
    def sweep_frequency(self, field, frequencies, save_dir, livefig=True, savefig=True, closefig=False,
                        file_prefix='', sen=None, sen_delay=None, read_reps=None, rep_delay=None,
                        read_delay=None, from0delay=None, avg_func=None, return_XY=False):
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        current = self.field2current(field)

        # Janky solution to the current not immediately jumping from 0 to first value
        self.SG.set_frequency_ghz(frequencies[0])
        self.PS.set_current(current)
        time.sleep(self._get_from0delay(from0delay))

        filename = file_prefix + r'\field_{:.4g}_Oe_freq_{:.4g}-{:.4g}_GHz_{:.4g}_dB'.format(
            field, frequencies.min(), frequencies.max(), float(self.SG.level[2:-2]))
        
        if livefig:
            plot_title = 'Frequency Sweep {:.4g} – {:.4g} GHz @ {:.4g} Oe, {:.4g} dB'.format(
                frequencies.min(), frequencies.max(), field, float(self.SG.level[2:-2]))
            self._make_fig(plot_title, 'Frequency (GHz)', 'Voltage (AU)')
            
        x_arr, y_arr = self._sweep_parameter(frequencies, self.SG.set_frequency_ghz, save_dir, livefig,
                                             savefig, closefig, sen, sen_delay, read_reps,
                                             rep_delay, read_delay, avg_func, frequencies, filename)
        
        df = pd.DataFrame({'frequency_ghz': frequencies, 'X': x_arr, 'Y': y_arr})
        df.to_csv(save_dir + r'\\' + filename + '.csv', index=False)
        
        if return_XY:
            return x_arr, y_arr


    def _sweep_parameter(self, params, setter_method, save_dir, livefig, savefig, closefig, sen,
                         sen_delay, read_reps, rep_delay, read_delay, avg_func, xrange, filename):
        self.LIA.SEN = self._get_sen(sen)
        X_array, Y_array = np.array([], dtype=float), np.array([], dtype=float)
        for i, param in enumerate(params):
            setter_method(param)
            time.sleep(self._get_read_delay(read_delay))
            X, Y = self.readXY(avg_func, read_reps, rep_delay, sen_delay)
            X_array = np.append(X_array, X)
            Y_array = np.append(Y_array, Y)
            if livefig:
                self._update_sweep_plot(xrange[0:i + 1], X_array, Y_array)
        self.PS.current = 0
        if livefig and savefig:
            self.fig.savefig(save_dir + '\\' + filename + '.png', dpi=600)
        if livefig and closefig:
            plt.close(self.fig)
        return X_array, Y_array
    

    def make2D(self, frequencies, fields, save_dir, primary='frequency', channel='X', livefig=False,
               savefig=False, closefig=False, file_prefix='', sen=None, sen_delay=None, read_reps=None,
               rep_delay=None, read_delay=None, from0delay=None, avg_func=None, integrate=False):
        arr = np.zeros((len(frequencies), len(fields)))
        if primary=='frequency':
            param1 = frequencies
            param2 = fields
            sweep_param2 = self.sweep_field
        elif primary=='field':
            param1 = fields
            param2 = frequencies
            sweep_param2 = self.sweep_frequency

        fig, ax = plt.subplots(figsize=(10,7))
        plot = ax.pcolormesh(fields, frequencies, arr, cmap='coolwarm')
        cbar = fig.colorbar(plot)
        plt.show()
        
        for i, val1 in enumerate(param1):
            X_arr, Y_arr = sweep_param2(val1, param2, save_dir, livefig=livefig, savefig=savefig,
                                        closefig=closefig, file_prefix=file_prefix, sen=sen, sen_delay=sen_delay,
                                        read_reps=read_reps, rep_delay=rep_delay, read_delay=read_delay,
                                        from0delay=from0delay, avg_func=avg_func, return_XY=True)
            if channel == 'X':
                channel_arr = X_arr
            elif channel == 'Y':
                channel_arr = Y_arr
            
            intstatus = 'Unintegrated'

            if integrate:
                channel_arr = self._integrate(param2, channel_arr)[1]
                intstatus = 'Integrated'
            
            title = '2D Sweep: Frequency {:.4g} – {:.4g} GHz, Field {:.4g} – {:.4g} Oe, {:.4g} dB, Channel {}, {}'.format(
            frequencies.min(), frequencies.max(), fields.min(), fields.max(), float(self.SG.level[2:-2]), channel, intstatus)
            ax.clear()

            if primary == 'frequency':
                arr[i] = channel_arr
                plot = ax.pcolormesh(fields, frequencies[:i + 1], arr[:i + 1], cmap='coolwarm')
            elif primary == 'field':
                arr[:, i] = channel_arr
                plot = ax.pcolormesh(fields[:i + 1], frequencies, arr[:, :i + 1], cmap='coolwarm')

            ax.set_xlabel('Field (Oe)')
            ax.set_ylabel('Frequency (GHz)')
            ax.set_title(title)
            cbar.update_normal(plot)
            fig.canvas.draw()
            plt.pause(0.05)
            
        filename = file_prefix + '2Dsweep_freq_{:.4g}-{:.4g}_GHz_field_{:.4g}-{:.4g}_Oe_{:.4g}_dB_channel_{}_{}'.format(
            frequencies.min(), frequencies.min(), fields.min(), fields.max(), float(self.SG.level[2:-2]), channel, intstatus)
        np.save(save_dir + '\\' + filename, arr)
        plt.savefig(save_dir + '\\' + filename + '.png', dpi=600)
    

    def field2current(self, field):
        return field / 669
    
    def current2field(self, current):
        return current * 669
    

    def _make_fig(self, title, xlabel, ylabel):
        self.fig, self.ax = plt.subplots(figsize=(9,6))

        self.l1, = self.ax.plot([], [], alpha=0.4, label='Channel 1 (X)')
        self.l2, = self.ax.plot([], [], alpha=0.4, label='Channel 2 (Y)')
        self.sc1 = self.ax.scatter([], [], s=10)
        self.sc2 = self.ax.scatter([], [], s=10)

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        self.ax.legend()
        plt.show()

    def _update_sweep_plot(self, xdata, ch1_data, ch2_data):
        self.l1.remove()
        self.l2.remove()
        self.sc1.remove()
        self.sc2.remove()

        self.l1, = self.ax.plot(xdata, ch1_data, alpha=0.4, label='Channel 1 (X)', color='green')
        self.l2, = self.ax.plot(xdata, ch2_data, alpha=0.4, label='Channel 2 (Y)', color='purple')
        self.sc1 = self.ax.scatter(xdata, ch1_data, s=10, c='green')
        self.sc2 = self.ax.scatter(xdata, ch2_data, s=10, c='purple')

        min_y = min(ch1_data.min(), ch2_data.min())
        max_y = max(ch1_data.max(), ch2_data.max())
        # self.ax.set_ylim(min_y - 0.05 * abs(min_y), max_y + 0.05 * abs(max_y))

        # self.ax.legend()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    
    def readXY(self, avg_func, read_reps, rep_delay, sen_delay):
        read_reps = self._get_read_reps(read_reps)
        rep_delay = self._get_rep_delay(rep_delay)
        avg_func = self._get_avg_func(avg_func)
        sen_delay = self._get_sen_delay(sen_delay)
                
        X_arr, Y_arr = np.array([], dtype=float), np.array([], dtype=float)
        for i in range(read_reps):
            X, Y = self.LIA.returnXY()
            X_arr = np.append(X_arr, X)
            Y_arr = np.append(Y_arr, Y)
            time.sleep(rep_delay)
        Xval = avg_func(X_arr)
        Yval = avg_func(Y_arr)

        sen_ratio = abs(max(abs(Xval), abs(Yval)))/self.LIA.SEN
        if sen_ratio > 0.8:
            self.LIA.decrease_sensitivity()
            time.sleep(sen_delay)
        return Xval, Yval
    
    def avg_mid_50(self, arr):
        return np.mean(arr[np.logical_and(arr >= np.percentile(arr, 25), arr <= np.percentile(arr, 75))])
    

    def _integrate(self, xarr, varr, c=0.0):
        varr = varr - np.mean(varr)
        intg_x = np.insert(xarr, 0, xarr[0] - (xarr[1] - xarr[0]))
        intg_y = np.array([c])
        
        for i in range(len(xarr)):
            dydx = varr[i]
            intg_y = np.append(intg_y, dydx * (intg_x[i + 1] - intg_x[i]) + intg_y[i])
        return intg_x[1:], intg_y[1:]

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