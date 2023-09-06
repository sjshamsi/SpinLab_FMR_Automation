from instrument_base import InstrumentBase as _InstrumentBase

class KEPCO_BOP(_InstrumentBase):
    """The class for the Kepco BOP 50-8D Power Supply"""
    def __init__(self, GPIB_Address: int=6, GPIB_Device: int=0,
                 ResourceName: str | None=None, logFile: str | None=None) -> None:
        """The initialising method for the KEPCO_BOP class

        Args:
            GPIB_Address (int, optional): Instrument specific address. Defaults to 6.
            GPIB_Device (int, optional): Instrument specific device number. Defaults to 0.
            ResourceName (str | None, optional): The instrument's resource name
            from the pyvisa resource manager's resource list. Defaults to None.
            logFile (str | None, optional): The path to the logfile. Defaults to None.
        """

        if ResourceName is None:
            ResourceName = 'GPIB%d::%d::INSTR' % (GPIB_Device, GPIB_Address)
        super().__init__(ResourceName, logFile)
        self._IDN = 'KEPCO BOP 50-8D'
        self.VI.write_termination = None
        self.VI.read_termination = self.VI.LF
        self.write('*CLS')
        self.write('*RST')
        self.write('OUTPUT ON')


    def __del__(self) -> None:
        self.write('VOLT 0')
        super().__del__()


    def SetRange(self, r: str) -> None:
        """Change operating range for output current or voltage.

        Args:
            r (str): Any of the strings, 'Full', '1/4', or 'AUTO'
            for full range, quarter range, and automatic range respectively.
        """

        validCodes = ['Full', '1/4', 'AUTO']
        if r in validCodes:
            rangeStr = ['1', '4', 'AUTO'][validCodes.index(r)]
            mode = ['VOLT', 'CURR'][self.query_int('FUNC:MODE?')]
            self.write('%s:RANG:%s' % (mode, rangeStr))
        else:
            self._log('ERR ', 'Range error code')


    def Output(self, out: str) -> None:
        """Enable or disable power supply output.

        Args:
            out (str): Either 'ON' or 'OFF'.
        """

        if out in ['ON', 'OFF']:
            self.write('OUTPUT ' + out)
        else:
            self._log('ERR ', 'Output error code')


    def CurrentMode(self) -> None:
        """Changes to constant current operation mode."""
        self.write('FUNC:MODE CURR')


    def VoltageMode(self) -> None:
        """Changes to constant voltage operation mode."""
        self.write('FUNC:MODE VOLT')


    @property
    def OperationMode(self) -> str:
        """Returns actual operation mode.

        Returns:
            str: Either 'Constant Voltage' or 'Constant Current'.
        """

        modes = ['Constant Voltage', 'Constant Current']
        return modes[self.query_int('FUNC:MODE?')]
    

    def VoltageOut(self, vOut: float) -> None:
        """Sets the Output/Protection Voltage.

        Args:
            vOut (float): The voltage you wish to set.
        """

        self.write('VOLT %0.4f' % vOut)


    @property
    def voltage(self) -> float:
        """On Voltage mode: Returns programed voltage/sets output voltage.
        On Current mode: Returns protection voltage/sets protection voltage.
        It sets the voltage by forwarding the input to the VoltageOut method. This
        method exists separately from VoltageOut as this is a getter/setter method.

        Args:
            vOut (float): The output/protection voltage you wish to set.

        Returns:
            float: The output voltage (when in voltage mode) or the protection
            voltage (when in cuurent mode)
        """

        return self.query_float('VOLT?')
    

    @voltage.setter
    def voltage(self, vOut: float) -> None:
        """On Voltage mode: Returns programed voltage/sets output voltage.
        On Current mode: Returns protection voltage/sets protection voltage.
        It sets the voltage by forwarding the input to the VoltageOut method. This
        method exists separately from VoltageOut as this is a getter/setter method.

        Args:
            vOut (float): The output/protection voltage you wish to set.

        Returns:
            float: The output voltage (when in voltage mode) or the protection
            voltage (when in cuurent mode)
        """
        self.VoltageOut(vOut)


    def CurrentOut(self, cOut: float) -> None:
        """Sets the Output/Protection Current.

        Args:
            cOut (float): The current you wish to set.
        """

        self.write('CURR %0.4f' % cOut)


    @property
    def current(self) -> float:
        """On Voltage mode: Returns protection current/sets protection current.
        On Current mode: Returns programmed current/sets output current.
        It sets the current by forwarding the input to the CurrentOut method. This
        method exists separately from CurrentOut as this is a getter/setter method.

        Args:
            cOut (float): The output/protection current you wish to set.

        Returns:
            float: The protection current (when in voltage mode) or the output
            current (when in current mode)
        """

        return self.query_float('CURR?')
    

    @current.setter
    def current(self, cOut: float) -> None:
        """On Voltage mode: Returns protection current/sets protection current.
        On Current mode: Returns programmed current/sets output current.
        It sets the current by forwarding the input to the CurrentOut method. This
        method exists separately from CurrentOut as this is a getter/setter method.

        Args:
            cOut (float): The output/protection current you wish to set.

        Returns:
            float: The protection current (when in voltage mode) or the output
            current (when in current mode)
        """

        self.CurrentOut(cOut)


    def BEEP(self) -> None:
        """Make the power supply go BEEP"""

        self.write('SYST:BEEP')


    @property
    def MeasuredVoltage(self) -> float:
        """Returns the measured voltage value. The measured voltage is
        different from the set output/protection value. 

        Returns:
            float: The measured voltage.
        """

        return self.query_float('MEAS:VOLT?')
    

    @property
    def MeasuredCurrent(self) -> float:
        """Returns the measured current value. The measured current is
        different from the set output/protection value. 

        Returns:
            float: The measured current.
        """

        return self.query_float('MEAS:CURR?')