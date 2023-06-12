# Some generic packages we need
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Let's import our instrument classes
from hp_8673g import HP_CWG
from srs_sr830 import SRS_SR830
from bop50_8d import KEPCO_BOP

class Experiment():
    def __init__(self, logFilePath=None):
        now = datetime.now()
        self.timestring = '{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)

        if logFilePath is None:
            logFilePath = './Experiment_Logs/FMR_log_{}.log'.format(self.timestring)
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
        self.from_0_delay = 3
        self.sensitivity_delay = 3

        self.welcome()

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

    def update_parameters(self):
        self.parameters = {
            'PS Output Current (A)': self.PS.MeasuredCurrent,
            'PS Output Voltage (V)': self.PS.MeasuredVoltage,
            'PS Output Mode (Current/Voltage)': self.PS.OperationMode,
            'SG Frequency': self.SG.frequency,
            'SG RF Output': self.SG.rf_output,
            'SG RF Output Level': self.SG.level,
            'LIA Time Constant': self.LIA.TC,
            'From 0 Delay (s)': self.from_0_delay,
            'Sensivity Delay (s)': self.sensitivity_delay,
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

    
    def sweep_field(self, frequency, fields, save_dir=None, savefig=True, closefig=False,
                    file_prefix='', sen=0.0002, read_delay=0.1, read_reps=20, rep_delay=0.1,
                    avg_func=None, return_XY=False):
        if save_dir is None:
            save_dir = self._get_save_dir()
        elif not os.path.isdir(save_dir):
            os.mkdir(save_dir)

        if avg_func is None:
            avg_func = self.avg_mid_50

        currents = self.field2current(fields)

        # Janky solution to the current not immediately jumping from 0 to first value
        self.SG.set_frequency_ghz(frequency)
        self.PS.set_current(currents[0])
        time.sleep(self.from_0_delay)

        plot_title = 'Field Sweep {:.4g} – {:.4g} Oe @ {:.4g} GHz, {:.4g} dB'.format(
            fields.min(), fields.max(), frequency, float(self.SG.level[2:-2]))
        filename = file_prefix + r'freq_{:.4g}_GHz_field_{:.4g}-{:.4g}_Oe_{:.4g}_dB'.format(
            frequency, fields.min(), fields.max(), float(self.SG.level[2:-2]))
        
        x_arr, y_arr = self._sweep_parameter(plot_title, 'Field (Oe)', currents, self.PS.set_current,
                                            read_delay, read_reps, rep_delay, save_dir, filename,
                                            savefig, closefig, sen, avg_func, fields=True)

        df = pd.DataFrame({'current_A': currents, 'field_Oe': fields, 'X': x_arr, 'Y': y_arr})
        df.to_csv(save_dir + r'\\' + filename + '.csv', index=False)

        if return_XY:
            return x_arr, y_arr

    
    def sweep_frequency(self, field, frequencies, save_dir=None, savefig=True, closefig=False,
                        file_prefix='', sen=0.0002, read_delay=0.1, read_reps=20, rep_delay=0.1,
                        avg_func=None, return_XY=False):
        if save_dir is None:
            save_dir = self._get_save_dir()
        elif not os.path.isdir(save_dir):
            os.mkdir(save_dir)

        if avg_func is None:
            avg_func = self.avg_mid_50

        current = self.field2current(field)

        # Janky solution to the current not immediately jumping from 0 to first value
        self.SG.set_frequency_ghz(frequencies[0])
        self.PS.set_current(current)
        time.sleep(self.from_0_delay)
        
        plot_title = 'Frequency Sweep {:.4g} – {:.4g} GHz @ {:.4g} Oe, {:.4g} dB'.format(
            frequencies.min(), frequencies.max(), field, float(self.SG.level[2:-2]))
        filename = file_prefix + r'\field_{:.4g}_Oe_freq_{:.4g}-{:.4g}_GHz_{:.4g}_dB'.format(
            field, frequencies.min(), frequencies.max(), float(self.SG.level[2:-2]))
        
        x_arr, y_arr = self._sweep_parameter(plot_title, 'Frequency (GHz)', frequencies,
                                            self.SG.set_frequency_ghz, read_delay, read_reps,
                                            rep_delay, save_dir, filename, savefig, closefig,
                                            sen, avg_func)
        
        df = pd.DataFrame({'frequency_ghz': frequencies, 'X': x_arr, 'Y': y_arr})
        df.to_csv(save_dir + r'\\' + filename + '.csv', index=False)

        if return_XY:
            return x_arr, y_arr


    def _sweep_parameter(self, plot_title, xlabel, param_range, set_param, read_delay, read_reps,
                        rep_delay, save_dir, filename, savefig, closefig, sen, avg_func, fields=False):
        self.LIA.SEN = sen
        self.make_fig(plot_title, xlabel, 'Voltage (AU)')

        if fields:
            xrange = self.current2field(param_range)
        else:
            xrange = param_range

        X_array, Y_array = np.array([], dtype=float), np.array([], dtype=float)
        for i, param in enumerate(param_range):
            set_param(param)
            time.sleep(read_delay)
            X, Y = self.readXY(avg_func, read_reps, rep_delay)
            X_array = np.append(X_array, X)
            Y_array = np.append(Y_array, Y)
            self.update_plot(xrange[0:i + 1], X_array, Y_array)
            
        self.PS.current = 0
        if savefig:
            self.fig.savefig(save_dir + '\\' + filename + '.png', dpi=600)
        if closefig:
            plt.close(self.fig)
        return X_array, Y_array
    

    def make_2D_figs(self, frequencies, fields, save_dir, primary='frequency', channel='X', savefig=True,
                closefig=True, file_prefix='', sen=0.002, read_delay=0.02, read_reps=1, rep_delay=0,
                avg_func=np.average, integrate=True):
        arr = np.zeros((len(frequencies), len(fields)))

        if primary == 'frequency':
            for i, freq in enumerate(frequencies):
                X_arr, Y_arr = self.sweep_field(freq, fields, save_dir=save_dir, savefig=savefig, closefig=closefig,
                                                file_prefix=file_prefix, sen=sen, read_delay=read_delay, read_reps=read_reps,
                                                rep_delay=rep_delay, avg_func=avg_func, return_XY=True)
                if channel == 'X':
                    arr[i] = X_arr
                if channel == 'Y':
                    arr[i] = Y_arr

        if primary == 'fields':
            for i, field in enumerate(fields):
                X_arr, Y_arr = self.sweep_frequency(field, frequencies, save_dir=save_dir, savefig=savefig, closefig=closefig,
                                                    file_prefix=file_prefix, sen=sen, read_delay=read_delay, read_reps=read_reps,
                                                    rep_delay=rep_delay, avg_func=avg_func, return_XY=True)
                if channel == 'X':
                    arr[:, i] = X_arr
                if channel == 'Y':
                    arr[:, i] = Y_arr
        filename = file_prefix + 'frequency_{:.4g}-{:.4g}_GHz_field_{:.4g}-{:.4g}_Oe_{:.4g}_dB'.format(
            frequencies.min(), frequencies.min(), fields.min(), fields.max(), float(self.SG.level[2:-2]))
        title = '2D Sweep: Frequency {} – {} GHz, Field {} – {} Oe, {} dB'.format(
            frequencies.min(), frequencies.min(), fields.min(), fields.max(), float(self.SG.level[2:-2]))
        np.save(save_dir + '\\' + filename, arr)
        
        plt.figure(figsize=(10, 7))
        plot = plt.pcolormesh(fields, frequencies, arr, cmap='coolwarm')
        plt.colorbar(plot)
        plt.xlabel('Field (Oe)')
        plt.ylabel('Frequency (GHz)')
        plt.title(title)
        plt.savefig(save_dir + '\\' + filename + '.png', dpi=600)

    def make_2D(self, frequencies, fields, save_dir, primary='frequency', channel='X',
                file_prefix='', sen=0.002, read_delay=0.02, read_reps=1, rep_delay=0,
                avg_func=np.average, integrate=True):
        self.LIA.SEN = sen
        arr = np.zeros((len(frequencies), len(fields)))

        fig, ax = plt.subplots(figsize=(10,7))
        plot = ax.pcolormesh(fields, frequencies, arr, cmap='coolwarm')
        cbar = fig.colorbar(plot)

        ax.set_xlabel('Field (Oe)')
        ax.set_ylabel('Frequency (GHz)')
        title = '2D Sweep: Frequency {} – {} GHz, Field {} – {} Oe, {} dB'.format(
            frequencies.min(), frequencies.min(), fields.min(), fields.max(), float(self.SG.level[2:-2]))
        ax.set_title(title)
        plt.show()

        currents = self.field2current(fields)
        if primary == 'frequency':
            for i, freq in enumerate(frequencies):
                X_arr, Y_arr = np.array([], dtype=float), np.array([], dtype=float)
                self.SG.set_frequency_ghz(freq)
                self.PS.set_current(currents[0])
                time.sleep(self.from_0_delay)
                for curr in currents:
                    self.PS.set_current(curr)
                    time.sleep(read_delay)
                    x, y = self.readXY(avg_func, read_reps, rep_delay)
                    X_arr = np.append(X_arr, x)
                    Y_arr = np.append(Y_arr, y)
                if channel == 'X':
                    if integrate:
                        arr[i] = self._integrate(fields, X_arr)[1]
                    else:
                        arr[i] = X_arr
                if channel == 'Y':
                    if integrate:
                        arr[i] = self._integrate(fields, Y_arr)[1]
                    else:
                        arr[i] = Y_arr
                ax.clear()
                plot = ax.pcolormesh(fields, frequencies[:i + 1], arr[:i + 1], cmap='coolwarm')
                ax.set_xlabel('Field (Oe)')
                ax.set_ylabel('Frequency (GHz)')
                ax.set_title(title)
                cbar.update_normal(plot)
                fig.canvas.draw()
                fig.show()
                plt.pause(0.01)

        if primary == 'fields':
            for i, curr in enumerate(currents):
                X_arr, Y_arr = np.array([], dtype=float), np.array([], dtype=float)
                self.SG.set_frequency_ghz(frequencies[0])
                self.PS.set_current(curr)
                time.sleep(self.from_0_delay)
                for freq in frequencies:
                    self.SG.set_frequency_ghz(freq)
                    time.sleep(read_delay)
                    x, y = self.readXY(np.average, read_reps, rep_delay)
                    X_arr = np.append(X_arr, x)
                    Y_arr = np.append(Y_arr, y)
                if channel == 'X':
                    if integrate:
                        arr[i] = self._integrate(frequencies, X_arr)[1]
                    else:
                        arr[:, i] = X_arr
                if channel == 'Y':
                    if integrate:
                        arr[i] = self._integrate(frequencies, Y_arr)[1]
                    else:
                        arr[:, 1] = Y_arr
                ax.clear()
                plot = ax.pcolormesh(fields[:i + 1], frequencies, arr, cmap='coolwarm')
                ax.colorbar(plot)

        filename = file_prefix + 'frequency_{:.4g}-{:.4g}_GHz_field_{:.4g}-{:.4g}_Oe_{:.4g}_dB'.format(
            frequencies.min(), frequencies.min(), fields.min(), fields.max(), float(self.SG.level[2:-2]))
        np.save(save_dir + '\\' + filename, arr)
        plt.savefig(save_dir + '\\' + filename + '.png', dpi=600)
        self.PS.current = 0
        return arr
    

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

    
    def readXY(self, avg_func, read_reps, rep_delay):
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
            time.sleep(self.sensitivity_delay)
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