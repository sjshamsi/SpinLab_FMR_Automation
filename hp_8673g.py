from instrumentBase import InstrumentBase as _InstrumentBase

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
        self.VI.write('R0')
        self.RF_ON = False
        super().__del__()

    def _frequencyIn(self, command):
        frequency_hz = self.query(command)[2:-2]
        return float(frequency_hz) / 1E9
    
    def _frequencyOut(self, frequency_val, mode):
        self.write('{} {:.9f} GZ'.format(mode, frequency_val))
    
    ### Main frequency/Centre frequency (they seem to be the same thing to me) methods
    @property
    def frequency(self):
        return self._frequencyIn('OK')
    
    @frequency.setter
    def frequency(self, frequency_val):
        self._frequencyOut(frequency_val, 'FR')
        self._check_message()

    def setFrequency(self, frequency_val):
        self._frequencyOut(frequency_val, 'FR')
        self._check_message()
    
    
    ### Start frequency methods
    @property
    def startFrequency(self):
        return self._frequencyIn('FA OA')
    
    @startFrequency.setter
    def startFrequency(self, frequency_val):
        self._frequencyOut(frequency_val, 'FA')
        self._check_message()
    

    ### Stop frequency methods
    @property
    def stopFrequency(self):
        return self._frequencyIn('FB OA')
        
    @stopFrequency.setter
    def stopFrequency(self, frequency_val):
        self._frequencyOut(frequency_val, 'FB')
        self._check_message()
    
    
    ### Delta frequency methods
    @property
    def deltaFrequency(self):
        return self._frequencyIn('FS OA')
    
    @deltaFrequency.setter
    def deltaFrequency(self, frequency_val):
        self._frequencyOut(frequency_val, 'FS')
        self._check_message()
        
        
    ### Frequency increment methods
    @property
    def frequencyIncrement(self):
        return self._frequencyIn('FI OA')
    
    @frequencyIncrement.setter
    def frequencyIncrement(self, frequency_val):
        self._frequencyOut(frequency_val, 'FI')
        self._check_message()
    
    
    ### Step size and step number methods
    @property
    def numSteps(self):
        steps = self.query('SPOA').split(',')[-1]
        return int(steps[2:-2])

    @numSteps.setter
    def numSteps(self, number):
        if not (type(number) == int):
            self._log('ERR ', 'Number of steps must be "int"!.')
        else:
            self.write('SP {} SS'.format(number))
            self._check_message()
        

    @property
    def stepSize(self):
        step_size = self.query('SPOA').split(',')[0]
        return float(step_size[2:-2]) / 1E9
    
    @stepSize.setter
    def stepSize(self, step_size):
        if not (type(step_size) in [int, float]):
            self._log('ERR ', 'Step size must be "int" or "float"!.')
        else:
            self._frequencyOut(step_size, 'SP')
            self._check_message()

    
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
            self.write(command)
            self.RF_ON = not self.RF_ON


    ### Level, RANGE, and VERNIER methods
    @property
    def level(self):
        level_string = self.query('LE OA')
        return float(level_string[2:-2])
    
    @level.setter
    def level(self, value):
        if not (type(value) in [int, float]):
            self._log('ERR ', 'Level must be "int" or "float"!.')
        elif (value > 13) or (value < -102):
            self._log('ERR ', 'Level must be between 13 dB and -102 dB inclusive!')
        else:
            self.write('LE {:.1f} DB'.format(value))
            self._check_message()

    
    @property
    def range(self):
        range_string = self.query('RA OA')
        return int(range_string[2:-2])
    
    @range.setter
    def range(self, value):
        if type(value) != int:
            self._log('ERR ', 'Range must be "int"!.')
        elif (value > 10) or (value < -90):
            self._log('ERR ', 'Range must be between 10 dB and -90 dB inclusive!')
        elif value % 10 != 0:
            self._log('ERR ', 'Range must be a multiple of 10!')
        else:
            self.write('RA {} DB'.format(value))
            self._check_message()


    @property
    def vernier(self):
        vernier_string = self.query('VE OA')
        return float(vernier_string[2:-2])
    
    @vernier.setter
    def vernier(self, value):
        if not (type(value) in [int, float]):
            self._log('ERR ', 'Vernier must be "int" or "float"!')
        elif (value > 3) or (value < -12):
            self._log('ERR ', 'Vernier must be between 3 dB and -12 dB inclusive!')
        else:
            self.write('VE {:.1f} DB'.format(value))
            self._check_message()

    
    def increase_range(self):
        self.write('RU')

    def decrease_range(self):
        self.write('RD')


    ### Message and error handling methods
    @property
    def message(self):
        code = self.query('MG')
        return code, self.error_codes[code]
    
    def _check_message(self):
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