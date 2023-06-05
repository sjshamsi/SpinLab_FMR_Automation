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
        self.RF_ON = True
        self.SWEEP_MODE = 'Off'
        self.error_codes = {
            '00': 'NO ERROR.',
            '01': 'FREQUENCY OUT OF RANGE.',
            '02': 'FREQUENCY INCR OUT OF RANGE.',
            '04': 'CANNOT STORE REGISTER 0.',
            '05': 'STEP SIZE OUT OF RANGE.',
            '07': 'NUMBER OF STEPS OUT OF RANGE.',
            '08': 'DWELL OUT OF RANGE.',
            '09': 'MARKER NUMBER NOT 1-5.',
            '10': 'START FREQ=STOP FREQ. NO SWEEP.',
            '11': 'SWEEP SCAN RESULTS IN START FREQUENCY OUT OF RANGE. Truncated sweep will result.',
            '12': 'SWEEP SCAN RESULTS IN STOP FREQUENCY OUT OF RANGE. Truncated sweep will result.',
            '13': 'NUMBER OF STEPS ADJUSTED TO GIVE STEP SIZE IN EVEN KHz. Press STEP to see result.',
            '14': 'STEP SIZE TOO SMALL FOR SPAN. Press STEP to see result (maximum number of steps is 9999).',
            '15': 'STEP SIZE>SPAN. Step size is set to span.',
            '16': 'BAND CROSSING IN AUTO SWEEP.',
            '20': 'INVALID HP-IB CODE.',
            '21': 'HP-IB DATA WITHOUT VALID PREFIX.',
            '22': 'INVALID HP-IB ADRESS ENTRY.',
            '23': 'TALK FUNCTION NOT PROPERLY SPECIFIED.',
            '24': 'OUTPUT LEVEL OUT OF RANGE.',
            '90': 'AUTO PEAK MALFUNCTION.',
            '92': 'RECALL CHECKSUM ERROR.',
            '95': 'LOSS OF DATA ON POWER UP.',
            '96': 'MEMORY TEST FAILURE.',
            '97': 'ROM TEST FAILURE. A2A10.',
            '98': 'RAM TEST FAILURE. A2A11.',
            '99': 'RAM NOT FUNCTIONAL AT POWER UP.'
        }
        
    def __del__(self):
        "We'll reset the HP8673G and turn off the RF output"
        self.VI.clear()
        self.RF_ON = False
        super().__del__()
    
    def _frequency_out(self, frq_val, mode, units):
        valid_units = ['Hz', 'KHz', 'MHz', 'GHz']

        frq_val = round(float(frq_val), 5)
        
        if units in valid_units:
            unit_str = ['HZ', 'KZ', 'MZ', 'GZ'][valid_units.index(units)]
            self.write('{0} {1} {2}'.format(mode, frq_val, unit_str))
        else:
            self._log('ERR ', 'Frequency error code. Invalid units! Valid units are "Hz", "KHz", "MHz", and "GHz".')
            return None
    
    ### Main frequency/Centre frequency (they seem to be the same thing to me) methods
    @property
    def frequency(self):
        return self.query('OK')
    
    @frequency.setter
    def frequency(self, frequency):
        frq_val, units = frequency.split(' ')
        self._frequency_out(frq_val, 'FR', units)
        self.check_message()
    
    
    ### Start frequency methods
    @property
    def start_frequency(self):
        return self.query('FA OA')
    
    @start_frequency.setter
    def start_frequency(self, frequency):
        frq_val, units = frequency.split(' ')
        self._frequency_out(frq_val, 'FA', units)
        self.check_message()
    

    ### Stop frequency methods
    @property
    def stop_frequency(self):
        return self.query('FB OA')
        
    @stop_frequency.setter
    def stop_frequency(self, frequency):
        frq_val, units = frequency.split(' ')
        self._frequency_out(frq_val, 'FB', units)
        self.check_message()
    
    
    ### Delta frequency methods
    @property
    def delta_frequency(self):
        return self.query('FS OA')
    
    @delta_frequency.setter
    def delta_frequency(self, frequency):
        frq_val, units = frequency.split(' ')
        self._frequency_out(frq_val, 'FS', units)
        self.check_message()
        
        
    ### Frequency increment methods
    @property
    def frequency_increment(self):
        return self.query('FI OA')
    
    @frequency_increment.setter
    def frequency_increment(self, frequency):
        frq_val, units = frequency.split(' ')
        self._frequency_out(frq_val, 'FI', units)
        self.check_message()
    
    
    ### Step size and step number methods
    @property
    def steps(self):
        return self.query('SPOA')

    @steps.setter
    def steps(self, step_num_size):
        step_val, step_units = step_num_size.split(' ')

        if step_units not in ['Steps', 'Hz', 'KHz', 'MHz', 'GHz']:
            self._log('ERR ', 'Number of steps/step size error code. Invalid units! Valid units are "Steps", "Hz", "Kz", "Mz", and "Gz".')
        elif step_units == 'Steps':
            self.write('SP {} SS'.format(step_val))
        else:
            self._frequency_out(step_val, 'SP', step_units)
        self.check_message()


    ### RF output mehtods
    @property
    def rf_output(self):
        if self.RF_ON:
            return 'On'
        return 'Off'
    
    @rf_output.setter
    def rf_output(self, status):
        valid_statuses = ['On', 'Off']
        
        if status not in valid_statuses:
            self._log('ERR ', 'RF output error code. Invalid input! Valid inputs are "On" and "Off".')
        elif ((status == 'On') and self.RF_ON) or ((status == 'Off') and (not self.RF_ON)):
            pass
        else:
            command = ['R1', 'R0'][valid_statuses.index(status)]
            print(command)
            self.write(command)
            self.RF_ON = not self.RF_ON


    ### Level, RANGE, and VERNIER methods
    @property
    def level(self):
        return self.query('LE OA')
    
    @level.setter
    def level(self, value):
        self.write('LE {} DB'.format(value))
        self.check_message()

    
    @property
    def range(self):
        return self.query('RA OA')
    
    @range.setter
    def range(self, value):
        self.write('RA {} DB'.format(value))
        self.check_message()


    @property
    def vernier(self):
        return self.query('VE OA')
    
    @vernier.setter
    def vernier(self, value):
        self.write('VE {} DB'.format(value))
        self.check_message()

    
    def increase_range(self):
        self.write('RU')

    def decrease_range(self):
        self.write('RD')


    ### Message and error handling methods
    @property
    def message(self):
        code = self.query('MG')
        return code, self.error_codes[code]
    
    def check_message(self):
        code, description = self.message
        if code == '00':
            return None
        self._log('ERR ', 'Device message code {0}: {1}'.format(code, description))
        raise ValueError('Device message code {0}: {1}'.format(code, description))
    

    ### Trigger and sweep methods
    def trigger(self):
        self.write('TR')

    def configure_trigger(self, command):
        self.write('CT {}'.format(command))

    @property
    def sweep_mode(self):
        return self.SWEEP_MODE
    
    @sweep_mode.setter
    def sweep_mode(self, mode):
        valid_modes = ['Auto', 'Manual', 'Off']

        if mode not in valid_modes:
            self._log('ERR ', 'Sweep mode error. Invalid input! Valid inputs are "Auto", "Manual", and "Off".')
        elif ((mode == 'Auto') and (self.SWEEP_MODE == 'Auto')) or ((mode == 'Manual') and (self.SWEEP_MODE == 'Manual')):
            pass
        else:
            self.write('W{}'.format([0, 2, 3][['Off', 'Auto', 'Manual'].index(mode)]))

    def begin_single_sweep(self):
        self.write('W6')