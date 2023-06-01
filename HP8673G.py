from instrument_base import InstrumentBase as _InstrumentBase

class HP_CWG(_InstrumentBase):
    def __init__(self, GPIB_Address=15, GPIB_Device=0, ResourceName=None, logFile=None):
        if ResourceName is None:
            ResourceName = 'GPIB%d::%d::INSTR' % (GPIB_Device, GPIB_Address)
        super().__init__(ResourceName, logFile)
        self._IDN = 'HP 8673G CW Gen'
        self.VI.write_termination = self.VI.LF
        self.VI.read_termination = self.VI.LF
        self.VI.clear()
        
    def __del__(self):
        "We'll reset the HP8673G and turn off the RF output"
        self.VI.clear()
        self.write('R0')
        super().__del__()
    
    def _frequency_out(self, frq_val, mode, units):
        valid_units = ['Hz', 'Mz', 'Gz']
        
        if units in valid_units:
            unit_str = ['HZ', 'MZ', 'GZ'][valid_units == units]
            self.write('{0} {1} {2}').format(mode, frq_val, unitStr)
        else:
            self._log('ERR ', 'Frequency error code. Invalid units! Valid units are "Hz", "Mz", and "Gz".')
            return None
    
    ### Main frequency/Centre frequency (they seem to be the same thing to me) methods
    @property
    def frequency(self):
        return self.query('OK')
    
    @frequency.setter
    def frequency(self, frq_val, units='Hz'):
        self._frequency_out(frq_val, 'FR', units)
    
    
    ### Start frequency methods
    @property
    def start_frequency(self):
        return self.query('FA OA')
    
    @start_frequency.setter
    def start_frequency(self, frq_val, units='Hz'):
        self._frequency_out(frq_val, 'FA', units)
        
        
    ### Stop frequency methods
    @property
    def stop_frequency(self):
        self.query('FB OA')
        
    @stop_frequency.setter
    def stop_frequency(self, frq_val, units='Hz'):
        self._frequency_out(frq_val, 'FB', units)
    
    
    ### Delta frequency methods
    @property
    def delta_frequency(self):
        self.query('FS OA')
    
    @delta_frequency.setter
    def delta_frequency(self, frq_val, units='Hz'):
        self._frequency_out(frq_val, 'FS', units)
        
        
    ### Frequency increment methods
    @property
    def frequency_increment(self):
        self.query('FI OA')
    
    @frequency_increment.setter
    def frequency_increment(self, frq_val, units='Hz'):
        self._frequency_out(frq_val, 'FI', units)
    
    
    ### Step size methods
    @property
    def step_size(self):
        self.query('FI OA')
    
    @frequency_increment.setter
    def frequency_increment(self, frq_val, units='Hz'):
        self._frequency_out(frq_val, 'FI', units)
    
    
    def SetRange(self, r):
        '''
        Change operating range for output current or voltage

        Usage :
            SetRange('Full' / '1/4' / 'AUTO')
        '''
        validCodes = ['Full', '1/4', 'AUTO']
        if r in validCodes:
            rangeStr = ['1', '4', 'AUTO'][validCodes == r]
            mode = ['VOLT', 'CURR'][self.query_int('FUNC:MODE?')]
            self.write('%s:RANG:%s' % (mode, rangeStr))
        else:
            self._log('ERR ', 'Range error code')

    def Output(self, out):
        '''
        Enable or disable power supply output

        Usage :
            Output('ON'/'OFF')
        '''
        if out in ['ON', 'OFF']:
            self.write('OUTPUT ' + out)
        else:
            self._log('ERR ', 'Output error code')

    def CurrentMode(self):
        ''' Changes to constant current operation mode '''
        self.write('FUNC:MODE CURR')

    def VoltageMode(self):
        ''' Changes to constant voltage operation mode '''
        self.write('FUNC:MODE VOLT')

    @property
    def OperationMode(self):
        ''' Returns actual operation mode '''
        modes = ['Constant Voltage', 'Constant Current']
        return modes[self.query_int('FUNC:MODE?')]

    def VoltageOut(self, vOut):
        '''
        Sets the Output/Protection Voltage

        Usage :
            VoltageOut(voltage)
        '''
        self.write('VOLT %0.4f' % vOut)

    @property
    def voltage(self):
        '''
        On Voltage mode:
            Sets output voltage or return programed voltage
        On Current mode:
            Sets or return protection voltage
        '''
        return self.query_float('VOLT?')

    @voltage.setter
    def voltage(self, vOut):
        self.VoltageOut(vOut)

    def CurrentOut(self, cOut):
        '''
        Sets the Output/Protection Current

        Usage :
            CurrentOut(current)
        '''
        self.write('CURR %0.4f' % cOut)

    @property
    def current(self):
        '''
        On Voltage mode:
            Sets or return protection current
        On Current mode:
            Sets output current or return programed current
        '''
        return self.query_float('CURR?')

    @current.setter
    def current(self, cOut):
        self.CurrentOut(cOut)

    def BEEP(self):
        '''BEEP'''
        self.write('SYST:BEEP')

    @property
    def MeasuredVoltage(self):
        '''Measured Voltage Value'''
        return self.query_float('MEAS:VOLT?')

    @property
    def MeasuredCurrent(self):
        '''Measured Current Value'''
        return self.query_float('MEAS:CURR?')