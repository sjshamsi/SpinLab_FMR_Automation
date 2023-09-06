import pyvisa
import datetime
import os
import numpy as np
import time
from typing import Any

def findResource(search_string: str, filter_string: str='', query_string: str='*IDN?',
                 open_delay: float=2.0, **kwargs) -> str | None:
    """Helps you look for a particular VISA instrument. You can cycle through all available VISA
    resources and initialise them (minimise the resources you initialise with filter_string), query
    them for their identity with query_string, and look for the search_string in the identity.
    Return the resource identity string if there is a match. 
    
    Args:
        search_string (str): If this substring is in the the resource's identity string, return
        the identity string.
        filter_string (str, optional): If this substring is in the resource name, query it for
        its identity. Defaults to ''.
        query_string (str, optional): The command to query the instrument for its identity.
        Defaults to '*IDN?'.
        open_delay (float, optional): Delay after the the resource is opened before the identity
        query is made. Defaults to 2.0.

    Returns:
        str | None: Resource name of the searched instrument. If instrument isn't found, None is returned
    """

    if os.name == 'nt':
        rm = pyvisa.ResourceManager()
    else:
        rm = pyvisa.ResourceManager('@py')
    for resource in rm.list_resources():
        if filter_string in resource:
            VI = rm.open_resource(resource, **kwargs)
            time.sleep(open_delay)
            try:
                VI.clear()
                if search_string in VI.query(query_string):
                    return resource
            except:
                pass
    return None


class ValuesFormat(object):
    def __init__(self):
        # Info: 
        #  http://pyvisa.readthedocs.io/en/stable/rvalues.html
        #   query_binary_values
        #   query_ascii_values
        # datatype info:
        #  https://docs.python.org/3/library/struct.html#format-characters
        self.is_binary = True
        self.container = np.array
        self.delay = None

        # Binary format
        self.datatype = 'd'  # float 64 bits
        self.is_big_endian = False
        self.header_fmt = 'ieee'

        # Ascii format
        self.converter = 'f'
        self.separator = ','

        
class InstrumentBase(object):
    """A base class for all instrument classes in Spinlab"""

    def __init__(self, ResourceName: str, logFile: str | None=None, **kargs) -> None:
        if os.name == 'nt':
            rm = pyvisa.ResourceManager()
        else:
            rm = pyvisa.ResourceManager('@py')
        self.VI = rm.open_resource(ResourceName, **kargs)
        self._IDN = self.VI.resource_name
        if logFile is None:
            self._logFile = None
        else:
            if not os.path.isfile(logFile):
                with open(logFile, 'w') as log:
                    log.write('SpinLab Instruments LogFile\n')
            self._logFile = os.path.abspath(logFile)
        self._logWrite('OPEN_')
        self.values_format = ValuesFormat()

    def __del__(self) -> None:
        self._logWrite('CLOSE')
        self.VI.close()

    def __str__(self) -> str:
        return "%s : %s" % ('spinlab.instrument', self._IDN)

    def _logWrite(self, action: str, value: str='') -> None:
        if self._logFile is not None:
            with open(self._logFile, 'a') as log:
                timestamp = datetime.datetime.utcnow()
                log.write('%s %s %s : %s \n' %
                          (timestamp, self._IDN, action, repr(value)))
    _log = _logWrite

    def write(self, command: str) -> None:
        self._logWrite('write', command)
        self.VI.write(command)

    def read(self) -> str:
        self._logWrite('read ')
        returnR = self.VI.read()
        self._logWrite('resp ', returnR)
        return returnR
    
    def query(self, command: str) -> str:
        self._logWrite('query', command)
        returnQ = self.VI.query(command)
        self._logWrite('resp ', returnQ)
        return returnQ

    def query_type(self, command: str, type_caster: type) -> Any:
        try:
            returnQ = self.query(command)
            return type_caster(returnQ)
        except Exception as E:
            self._logWrite('ERROR', E.__repr__())
            returnQ = self.query(command)
            return type_caster(returnQ)

    def query_int(self, command: str) -> int:
        return self.query_type(command, int)

    def query_float(self, command: str) -> float:
        return self.query_type(command, float)

    def query_values(self, command: str) -> Any:
        # NOTE: self.values_format should be set to the adequate format
        if self.values_format.is_binary:
            read_term = self.VI.read_termination
            self.VI.read_termination = None
            self._logWrite('query_binary_values', command)
            options = {'datatype': self.values_format.datatype,
                       'is_big_endian': self.values_format.is_big_endian,
                       'header_fmt': self.values_format.header_fmt,
                       'delay': self.values_format.delay,
                       'container': self.values_format.container}
            data = self.VI.query_binary_values(command, **options)
            self.VI.read_termination = read_term
        else:
            self._logWrite('query_ascii_values', command)
            options = {'converter': self.values_format.converter,
                       'separator': self.values_format.separator,
                       'delay': self.values_format.delay,
                       'container': self.values_format.container}
            data = self.VI.query_ascii_values(command, **options)
        self._logWrite('len return data:', str(len(data)))
        return data
    
    
class InstrumentChild(object):
    '''Base class for instrument subclasses in Spinlab'''

    def __init__(self, parent) -> None:
        self.parent = parent
        self._logWrite = parent._logWrite
        self._log = parent._log
        self.write = parent.write
        self.query = parent.query
        self.query_type = parent.query_type
        self.query_int = parent.query_int
        self.query_float = parent.query_float
        self.query_values = parent.query_values
        self._IDN = parent._IDN + ' %s' % self.__class__.__name__

    def __del__(self) -> None:
        del self.parent
        del self._logWrite
        del self._log
        del self.write
        del self.query
        del self.query_type
        del self.query_int
        del self.query_float
        del self.query_values

    def __str__(self) -> str:
        return "%s : %s" % ('spinlab.instrument', self._IDN)