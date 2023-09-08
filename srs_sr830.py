import numpy as _np
from instrument_base import InstrumentBase as _InstrumentBase

class SRS_SR830(_InstrumentBase):
    """The class for the Stanford Research Systems SR830 Lock-in Amplifier."""
    def __init__(self, GPIB_Address: int=8, GPIB_Device: int=0, RemoteOnly: bool=False,
                 ResourceName: str | None=None, logFile: str | None=None) -> None:
        """The initialising method for the SRS_SR830 class

        Args:
            GPIB_Address (int, optional): Instrument specific address. Defaults to 8.
            GPIB_Device (int, optional): Instrument specific device number. Defaults to 0.
            ResourceName (str | None, optional): The instrument's resource name
            from the pyvisa resource manager's resource list. Defaults to None.
            logFile (str | None, optional): The path to the logfile. Defaults to None.
        """

        if ResourceName is None:
            ResourceName = 'GPIB%d::%d::INSTR' % (GPIB_Device, GPIB_Address)
        super().__init__(ResourceName, logFile)
        self._IDN = 'SRS_SR830'
        self.VI.write_termination = self.VI.LF
        self.VI.read_termination = self.VI.LF
        self.write('OUTX 1')  # GPIB Mode
        self.RemoteOnly(RemoteOnly)

    def RemoteOnly(self, rO: bool=True) -> None:
        """Make the SRS830 remote-only or not remote only.

        Args:
            rO (bool, optional): True for remote-only, False for the opposite. Defaults to True.
        """

        if rO:
            self.write('OVRM 0')
        else:
            self.write('OVRM 1')

    @property
    def TC(self) -> float:
        """Sets or returns the Filter Time Constant setted values are rounded to available
        hardware value.

        Args:
            tc (float): The time constant (in s) that you'd like to set.

        Returns:
            float: The LIA's time constant (in s).
        """

        # #Documentation#
        # TC Codes :
        # '0'  = 10 us
        # '1'  = 30 us
        # '2'  = 100 us
        # '3'  = 300 us
        # '4'  = 1 ms
        # '5'  = 3 ms
        # '6'  = 10 ms
        # '7'  = 30 ms
        # '8'  = 100 ms
        # '9'  = 300 ms
        # '10' = 1 s
        # '11' = 3 s
        # '12' = 10 s
        # '13' = 30 s
        # '14' = 100 s
        # '15' = 300 s
        # '16' = 1 ks
        # '17' = 3 ks
        # '18' = 10 ks
        # '19' = 30 ks
        tc_i = self.query_int('OFLT?')
        bins = [10E-6, 30E-6, 100E-6, 300E-6, 1E-3, 3E-3, 10E-3,
                30E-3, 100E-3, 300E-3, 1.0, 3.0, 10.0, 30.0,
                100.0, 300.0, 1E3, 3E3, 10E3, 30E3]
        return bins[tc_i]

    @TC.setter
    def TC(self, tc: float) -> None:
        """Sets or returns the Filter Time Constant setted values are rounded to available
        hardware value.

        Args:
            tc (float): The time constant (in s) that you'd like to set.

        Returns:
            float: The LIA's time constant (in s).
        """

        tc = _np.abs(tc)
        bins = [10E-6, 30E-6, 100E-6, 300E-6, 1E-3, 3E-3, 10E-3,
                30E-3, 100E-3, 300E-3, 1.0, 3.0, 10.0, 30.0,
                100.0, 300.0, 1E3, 3E3, 10E3, 30E3]
        tc_i = _np.abs(_np.array(bins) - tc).argmin()
        self.write('OFLT %d' % tc_i)


    @property
    def SEN(self) -> float:
        """Sets or returns the Full Scale Sensitivity setted values rounded to available
        hardware value.

        Args:
            vSen (float): The sensitivity (in V when input mode in one of the voltage
            modes and A when input mode is in one of the current modes) that you'd
            like to set.

        Returns:
            float: vSen (float): The LIA's sensitivity (in V when input mode in one of
            the voltage modes and A when input mode is in one of the current modes).
        """

        # #Documentation#
        # SEN  Codes
        # Codes : Voltage  Current
        #  '0'  = 2 nV     2 fA
        #  '1'  = 5 nV     5 fA
        #  '2'  = 10 nV    10 fA
        #  '3'  = 20 nV    20 fA
        #  '4'  = 50 nV    50 fA
        #  '5'  = 100 nV   100 fA
        #  '6'  = 200 nV   200 fA
        #  '7'  = 500 nV   500 fA
        #  '8'  = 1 uV     1 pA
        #  '9'  = 2 uV     2 pA
        #  '10' = 5 uV     5 pA
        #  '11' = 10 uV    10 pA
        #  '12' = 20 uV    20 pA
        #  '13' = 50 uV    50 pA
        #  '14' = 100 uV   100 pA
        #  '15' = 200 uV   200 pA
        #  '16' = 500 uV   500 pA
        #  '17' = 1 mV     1 nA
        #  '18' = 2 mV     2 nA
        #  '19' = 5 mV     5 nA
        #  '20' = 10 mV    10 nA
        #  '21' = 20 mV    20 nA
        #  '22' = 50 mV    50 nA
        #  '23' = 100 mV   100 nA
        #  '24' = 200 mV   200 nA
        #  '25' = 500 mV   500 nA
        #  '26' = 1 V      1 uA
        sen_i = self.query_int('SENS?')
        vSen = [2E-15, 5E-15, 10E-15, 20E-15, 50E-15, 100E-15, 200E-15,
                500E-15, 1E-12, 2E-12, 5E-12, 10E-12, 20E-12, 50E-12,
                100E-12, 200E-12, 500E-12, 1E-9, 2E-9, 5E-9, 10E-9,
                20E-9, 50E-9, 100E-9, 200E-9, 500E-9, 1E-6][sen_i]
        inputMode = self.query('ISRC?')
        if inputMode in ['0', '1']:
            # Voltage mode
            vSen *= 1.0E6
        return vSen

    @SEN.setter
    def SEN(self, vSen: float) -> None:
        """Sets or returns the Full Scale Sensitivity setted values rounded to available
        hardware value.

        Args:
            vSen (float): The sensitivity (in V when input mode in one of the voltage
            modes and A when input mode is in one of the current modes) that you'd
            like to set.

        Returns:
            float: vSen (float): The LIA's sensitivity (in V when input mode in one of
            the voltage modes and A when input mode is in one of the current modes).
        """

        vSen = _np.abs(vSen)
        if self.query('ISRC?') in ['0', '1']:
            # Voltage mode
            vSen *= 1.0E-6
        bins = [2E-15, 5E-15, 10E-15, 20E-15, 50E-15, 100E-15, 200E-15,
                500E-15, 1E-12, 2E-12, 5E-12, 10E-12, 20E-12, 50E-12,
                100E-12, 200E-12, 500E-12, 1E-9, 2E-9, 5E-9, 10E-9,
                20E-9, 50E-9, 100E-9, 200E-9, 500E-9, 1E-6]
        sen_i = _np.abs(_np.array(bins) - vSen).argmin()
        self.write('SENS %d' % sen_i)

    def decrease_sensitivity(self) -> None:
        """Go down one sensitivity level (as long as it's not already at its lowest)."""
        sen_i = self.query_int('SENS?')
        if sen_i == 26:
            self._log('decrease_sensitivity ERR ', 'Sensivity already at minimum! Changing nothing.')
        else:
            self.write('SENS %d' % sen_i + 1)

    def increase_sensitivity(self) -> None:
        """Go up one sensitivity level (as long as it's not already at its highest)."""
        sen_i = self.query_int('SENS?')
        if sen_i == 0:
            self._log('increase_sensitivity ERR ', 'Sensivity already at maximum! Changing nothing.')
        else:
            self.write('SENS %d' % sen_i - 1)


    def FilterSlope(self, sl: str) -> None:
        """Set the output filter slope.

        Args:
            sl (str): One of the following: '0' (6 dB/octave), '1' (12 dB/octave),
            '2' (18 dB/octave), '3' (24 dB/octave).
        """

        if sl in ['0', '1', '2', '3']:
            self.write('OFSL %s' % sl)
        else:
            self._log('ERR ', 'Wrong Slope Code')


    def InputMode(self, imode: str) -> None:
        """Current/Voltage mode Input Selector.

        Args:
            imode (str): One of the following: '0' (Voltage Mode A), '1' (Voltage Mode A-B),
            '2' (Current Mode 1 Mega Ohm), '3' (Current Mode 100 Mega Ohm).
        """

        if imode in ['0', '1', '2', '3']:
            self.write('ISRC %s' % imode)
        else:
            self._log('ERR ', 'Wrong Input Mode Code')


    def Sync(self, Sy: bool=True) -> None:
        """Enable or disable Synchonous time constant.

        Args:
            Sy (bool, optional): True to Synch, Flase to not. Defaults to True.
        """

        if Sy:
            self.write('SYNC 1')
        else:
            self.write('SYNC 0')


    def setOscilatorFreq(self, freq: int | float) -> None:
        """Set the internal Oscilator Frequency.

        Args:
            freq (int | float): The frequency you'd like to set. Frequency limits are
            0.001 to 102000 Hz. Frequency is rounded off to 5 digits or 0.0001 Hz,
            whichever is greater.
        """

        self.write('FREQ %0.6f' % freq) # Does this rounding off match the rounding off rules for FREQ in the documentation? Does it matter?


    def setOscilatorAmp(self, amp: int | float) -> None:
        """Set the internal Oscilator Amplitude.

        Args:
            amp (int | float): Amplitude in voltage. Amplitude is rounded to 0.002V.
            The amplitude limits are 0.004 to 5.000 V.
        """

        self.write('SLVL %0.6f' % amp)


    def setRefPhase(self, ph: int | float) -> None:
        """Set the phase reference.

        Args:
            ph (int | float): The phase shift value in degrees. Will be rounded to 0.01°.
            Limits are -360.00° to 729.99° and phase will be wrapped around at ±180°.
            For example, the PHAS 541.0 command will set the phase to -179.00° (541-360=181=-179)
        """

        self.write('PHAS %0.6f' % ph)


    def getRefPhase(self) -> float:
        """Get the programed phase reference."""

        return self.query_float('PHAS?')
    

    def ConfigureInput(self, InDev: str='FET', Coupling: str='AC',
                       Ground: str='GND', AcGain: str='Auto') -> None:
        """IDK man."""
        # TODO Implement
        pass


    # Some functions I added myself, but individually querying the X/Y channels is slowww
    def getX(self) -> float:
        """Query the Channel X value.

        Returns:
            float: Channel X value in V.
        """

        return self.query_float('OUTP? 1')

    def getY(self) -> float:
        """Query the Channel Y value.

        Returns:
            float: Channel Y value in V.
        """

        return self.query_float('OUTP? 2')
    
    def getXY(self) -> tuple[float, float]:
        """Query the Channel X and Y values together.

        Returns:
            float: Channel X and Y values in V.
        """

        X, Y = self.query('SNAP?1,2').split(',')
        return float(X), float(Y)
    

    @property
    def Magnitude(self) -> float:
        """Return the magnitude.

        Returns:
            float: Magnitude in V.
        """

        return self.query_float('OUTP? 3')


    @property
    def Phase(self) -> float:
        """Return the phase between signal and lock-in reference.

        Returns:
            float: Phase difference in degrees.
        """

        return self.query_float('OUTP? 4')


    @property
    def Freq(self) -> float:
        """Return the internal oscillator frequency.

        Returns:
            float: Frequency in Hz.
        """

        return self.query_float('FREQ?')


    @property
    def AUX_In_1(self) -> float:
        """Return the value for AUX input 1.

        Returns:
            float: Voltage in ASCII value with resolution of 1/3 mV.
        """

        return self.query_float('OAUX?1')


    @property
    def AUX_In_2(self) -> float:
        """Return the value for AUX input 2.

        Returns:
            float: Voltage in ASCII value with resolution of 1/3 mV.
        """

        return self.query_float('OAUX?2')


    @property
    def AUX_In_3(self) -> float:
        """Return the value for AUX input 3.

        Returns:
            float: Voltage in ASCII value with resolution of 1/3 mV.
        """

        return self.query_float('OAUX?3')


    @property
    def AUX_In_4(self) -> float:
        """Return the value for AUX input 4.

        Returns:
            float: Voltage in ASCII value with resolution of 1/3 mV.
        """

        return self.query_float('OAUX?4')