import pyvisa
import datetime
import os
import numpy as np
import time

def findResource(search_string, filter_string='', query_string='*IDN?', open_delay=2, **kwargs):
    

    """Helps you look for a particular VISA instrument. You can cycle through all visable VISA
    resources and initialise them (initialise only the resources you want with filter_string), query
    them for their identity (can specify different identity commands), and look for the
    search_string in the returned identity.
    
    Note: Do not use for the HP 8673G as I don't know its HP-IB query command. LMK if you do.
    
    Parameters:
    search_string (str): Filter resources'  The substring that you want to search for when you query resources for
    their identity.
    filter_string (str): The substring that you want your resources' names to have.
    query_string (str): The command you want to send to query a resource for its identity.
    open_delay (float): Delay after the the resource is opned before the identity query is made.
    
    Returns: None | ResourceManager object
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
    '''
    Base class for all instrument classes in spinlab
    '''

    def __init__(self, ResourceName, logFile=None, **kargs):
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

    def __del__(self):
        self._logWrite('CLOSE')
        self.VI.close()

    def __str__(self):
        return "%s : %s" % ('spinlab.instrument', self._IDN)

    def _logWrite(self, action, value=''):
        if self._logFile is not None:
            with open(self._logFile, 'a') as log:
                timestamp = datetime.datetime.utcnow()
                log.write('%s %s %s : %s \n' %
                          (timestamp, self._IDN, action, repr(value)))
    _log = _logWrite

    def write(self, command):
        self._logWrite('write', command)
        self.VI.write(command)

    def read(self):
        self._logWrite('read ')
        returnR = self.VI.read()
        self._logWrite('resp ', returnR)
        return returnR
    
    def query(self, command):
        self._logWrite('query', command)
        returnQ = self.VI.query(command)
        self._logWrite('resp ', returnQ)
        return returnQ

    def query_type(self, command, type_caster):
        try:
            returnQ = self.query(command)
            return type_caster(returnQ)
        except Exception as E:
            self._logWrite('ERROR', E.__repr__())
            returnQ = self.query(command)
            return type_caster(returnQ)

    def query_int(self, command):
        return self.query_type(command, int)

    def query_float(self, command):
        return self.query_type(command, float)

    def query_values(self, command):
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
    '''
    Base class for instrument subclasses in magdynlab
    '''

    def __init__(self, parent):
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

    def __del__(self):
        del self.parent
        del self._logWrite
        del self._log
        del self.write
        del self.query
        del self.query_type
        del self.query_int
        del self.query_float
        del self.query_values

    def __str__(self):
        return "%s : %s" % ('spinlab.instrument', self._IDN)