# -*- coding: utf-8 -*

#
#          EduBeam is an education project to develop a free structural
#                   analysis code for educational purposes.
#
#                             (c) 2011 Borek Patzak 
#
#       EduBeam is free software; you can redistribute it and/or modify it 
#         under the terms of the GNU General Public License as published 
#        by the Free Software Foundation; either version 2 of the License, 
#                        or (at your option) any later version.
#
# EduBeam is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details. You should have received a copy of 
# the GNU General Public License along with File Hunter; if not, write to 
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

##################################################################
#
# ebinit.py file
# this file is imported by ebfem.py file
# imports required modules and define a few functions used in both
# ebfem.py and ebgui.py files
#
##################################################################

"""
EduBeam module, imports some important libraries and sets global variables and functions
"""


import sys
sys.path += ['.']
import os
import re
#import codecs
import locale
import time
import logging
import copy
import importlib

"""current version"""
version = '4.0.0'

"""date of last modification"""
date = '2019-12-26'
#ebdir = sys.path[0]
#Use for PyInstaller to have access to splash screen
if getattr(sys, 'frozen', None):
     ebdir = sys._MEIPASS
else:
     ebdir = os.path.dirname(__file__)
"""path to edubeam.py"""


class EduBeamError(Exception):
    """EduBeam exception"""
    def __init__(self,value=None):
        self.value = value
    def __str__(self):
        return repr(self.value)


##################################################################
#
# language
#
##################################################################
defaultLang = 'en'
supportedLangs = ('cz','en')
eblang = locale.getdefaultlocale()[0].lower()
"""Language of session"""

if not eblang: eblang = defaultLang
elif 'cz' in eblang.lower(): eblang = 'cz'
elif 'sk' in eblang.lower(): eblang = 'cz'
elif 'cs' in eblang.lower(): eblang = 'cz'
elif 'en' in eblang.lower(): eblang = 'en'
else: eblang = defaultLang

#importlib.reload(sys)
#sys.setdefaultencoding("utf-8")

def langStr(*arg):
    """return string in dependency on lang variable
    
    usage:

    .. code-block:: python

        langStr('Only english specified') # one string
        langStr('English first','Čeština jako druhá') # two strings
        langStr(['English first','Čeština jako druhá']) # list
        langStr({'cz':'Něco česky','en':'and in English'}) # dictionary
        """
    lArg = len(arg)
    if lArg==0: return ''
    if lArg==1:
        if isinstance(arg[0],dict):
            return unicode(arg[0][eblang], 'utf-8')
        if isinstance(arg[0],list):
            return unicode(arg[0][0], 'utf-8') if eblang=='en' else unicode(arg[0][1], 'utf-8') if eblang=='cz' else ''
        if isinstance(arg[0],str):
            return unicode(arg[0], 'utf-8')
    else:
        return arg[0] if eblang=='en' else arg[1] if eblang=='cz' else ''
    return ''


def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.
    If strings_only is True, don't convert (some) non-string-like objects.
    Downloaded from https://code.djangoproject.com/browser/django/tags/releases/1.1.1/django/utils/encoding.py?order=name
    
    :rtype: str
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    if not isinstance(s, str):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, str):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

##################################################################


def description():
    return langStr('EduBeam is an educational project to develop a free structural analysis code','EduBeam je výukový projekt, jehož cílem je vývoj volně šiřitelného programu pro analýzu konstrukcí')


licence = '''EduBeam is free software; you can redistribute it and/or modify it 
under the terms of the GNU General Public License as published by the Free Software Foundation; 
either version 2 of the License, or (at your option) any later version.

EduBeam is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. You should have received a copy of 
the GNU General Public License along with File Hunter; if not, write to 
the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA'''

def helpMessage():
    return '''
EduBeam %s on %s
%s

usage: [python] edubeam.py [options]
options:
  -h, --help    show this help message and exit
  -l, --lang    (str) language of program [en,cz], default='en'
  -f, --file    (str) immediately load and compute EduBeam file
  -t, --term    leave standard and error messages on terminal
  -b, --basic   run EduBeam basic version, without any
                extensions (for testing and debugging)
  -o, --output  (str) file name to save messages
  -d, --debug   set logger level to DEBUG
  --loglevel    (str) set logger level to defined value
                [DEBUG, INFO, WARN, ERROR, FATAL]
  -e, --execute execute a python script from a file
'''%(version, date, description().encode('utf-8'))







##################################################################
#
# logger
#
##################################################################
class Logger:
    """Logger class, inspired by logging module (logging module is not used because of not redirecting to glframe console)

    :param str level: levelof the logger (options are 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL' and 'NOTSET')
    :param file file: file opened for writing to write output (apart from stdout)
    """

    LOG_LEVEL_FATAL    = 50
    LOG_LEVEL_CRITICAL = 50
    LOG_LEVEL_ERROR    = 40
    LOG_LEVEL_WARNING  = 30
    LOG_LEVEL_INFO     = 20
    LOG_LEVEL_DEBUG    = 10
    LOG_LEVEL_NOTSET   = 0

    logLevelInt2str = {
        LOG_LEVEL_FATAL   : 'FATAL',
        LOG_LEVEL_ERROR   : 'ERROR',
        LOG_LEVEL_WARNING : 'WARN',
        LOG_LEVEL_INFO    : 'INFO',
        LOG_LEVEL_DEBUG   : 'DEBUG',
        LOG_LEVEL_NOTSET  : 'NOTSET',
    }

    logLevelStr2int = {
        'NOTSET'   : LOG_LEVEL_NOTSET,
        'DEBUG'    : LOG_LEVEL_DEBUG,
        'INFO'     : LOG_LEVEL_INFO,
        'WARN'     : LOG_LEVEL_WARNING,
        'WARNING'  : LOG_LEVEL_WARNING,
        'ERROR'    : LOG_LEVEL_ERROR,
        'FATAL'    : LOG_LEVEL_FATAL,
        'CRITICAL' : LOG_LEVEL_CRITICAL,
    }

    level = LOG_LEVEL_INFO
    file = None

    def __init__(self,level='INFO',file=None, printMsgType=False):
        self.setLevel(level)
        self.file = file
        self.printMsgType = printMsgType

    def giveLevelAsInt(self,level):
        if isinstance(level,str):
            level = level.upper()
            return self.logLevelStr2int.get(level,self.LOG_LEVEL_NOTSET)
        if isinstance(level,(float,int)):
            return int(level)
        raise TypeError

    def setLevel(self,level):
        self.level = self.giveLevelAsInt(level)

    def quit(self):
        if self.file:
            self.file.close()

    def log(self,level,msg):
        level = self.giveLevelAsInt(level)
        if level < self.level:
            return
        name = self.logLevelInt2str.get(level)
        #print(type(name))
        msg = '%s%s'%('%s: '%name if self.printMsgType else '', smart_str(msg).decode("utf-8"))
        print (msg)
        if self.file:
            self.file.write(msg + '\n')
            self.file.flush()

    def debug(self,msg):
        """Print message with level 'DEBUG'
        
        :param str msg: message to be printed with level 'DEBUG'
        """
        self.log(self.LOG_LEVEL_DEBUG,msg)

    def info(self,msg):
        """Print message with level 'INFO'
        
        :param str msg: message to be printed with level 'INFO'
        """
        self.log(self.LOG_LEVEL_INFO,msg)

    def warn(self,msg):
        """Print message with level 'WARNING'
        
        :param str msg: message to be printed with level 'WARNING'
        """
        self.log(self.LOG_LEVEL_WARNING,msg)

    def warning(self,msg):
        """Print message with level 'WARNING'
        
        :param str msg: message to be printed with level 'WARNING'
        """
        self.log(self.LOG_LEVEL_WARNING,msg)

    def error(self,msg):
        """Print message with level 'ERROR'
        
        :param str msg: message to be printed with level 'ERROR'
        """
        self.log(self.LOG_LEVEL_ERROR,msg)

    def critical(self,msg):
        """Print message with level 'CRITICAL'
        
        :param str msg: message to be printed with level 'CRITICAL'
        """
        self.log(self.LOG_LEVEL_CRITICAL,msg)

    def fatal(self,msg):
        """Print message with level 'FATAL'
        
        :param str msg: message to be printed with level 'FATAL'
        """
        self.log(self.LOG_LEVEL_FATAL,msg)







##################################################################
#
# other
#
##################################################################
def isResultFlag():
    #"""TODO"""
    return globalFlags.deformationDisplayFlag or globalFlags.intForcesDisplayFlag[0] or globalFlags.intForcesDisplayFlag[1] or globalFlags.intForcesDisplayFlag[2] or globalFlags.intForcesDisplayFlag[3]

def isBeamResultFlag():
    #"""TODO"""
    return globalFlags.deformationDisplayFlag or globalFlags.intForcesDisplayFlag[0] or globalFlags.intForcesDisplayFlag[1] or globalFlags.intForcesDisplayFlag[2]


#natural sorting, e.g. 1,2,11, One ...
def natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html
    
    :param str string_: string to be naturalized
    :rtype: str
    """
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]




##################################################################
#
# ACTUAL RUN - GLOBAL VARIABLES
#
##################################################################

##################################################################
# command line arguments
##################################################################
if '-h' in sys.argv or '--help' in sys.argv:
    print (helpMessage())
    sys.exit()

fileName = ''
redirectTerm = True #False=parent terminal, True=bottom window
doNotUseExtensions = False
outputFileName = ''
logLevel = 'INFO'
pythonScriptFileName =''
for i,arg in enumerate(sys.argv):
    a = arg.lower()
    if   a == '-l' or a == '--lang':       eblang = sys.argv[i+1]
    elif a == '-f' or a == '--file':       fileName = sys.argv[i+1]
    elif a == '-t' or a == '--term':       redirectTerm = False
    elif a == '-b' or a == '--basic':      doNotUseExtensions = True
    elif a == '-o' or a == '--output':     outputFileName = sys.argv[i+1]
    elif a == '-d' or a == '--debug':      logLevel = 'DEBUG'
    elif a == '--loglevel':                logLevel = sys.argv[i+1]
    elif a == '-e' or a == '--execute':    pythonScriptFileName = sys.argv[i+1]
    
if not eblang in supportedLangs:
    eblang = defaultLang
##################################################################



# logger
f = open(outputFileName,'w') if outputFileName else None
logger = Logger(logLevel,f)
"""Instance of :py:class:`Logger`"""

if 0: # for testing logger only
    logger.debug('debug')
    logger.info('info')
    logger.warn('warn')
    logger.warning('warning')
    logger.error('error')
    logger.fatal('fatal')
    logger.critical('critical')
    sys.exit()

logger.debug( langStr('Logger created', 'Logger vytvořen') )





##################################################################
# extensions
##################################################################

# extract directories from ebdir/extensions directory
extensions = []
if os.path.exists(os.path.join(ebdir,'extensions')):
    extensions = [extension for extension in os.listdir(os.path.join(ebdir,'extensions')) if os.path.isdir(os.path.join(ebdir,'extensions',extension))]

# default values
sheetExportFormats = ['csv']
import csv

if not doNotUseExtensions:
    # iterate over all found extensions and handle supported ones
    for extension in extensions:
        if 'xlwt' in extension:
            # xlwt module for writing to .xls (MS Excel) format
            # http://pypi.python.org/pypi/xlwt
            sys.path.append(os.path.join(ebdir,'extensions',extension))
            try:
                import xlwt
                sheetExportFormats.append('xls')
            except ImportError:
                pass
logger.debug(langStr( 'Extensions are%sused'%(' not ' if doNotUseExtensions else ''), 'Rozšíření %sjsou použita'%('ne' if doNotUseExtensions else '')))
##################################################################


class EduBeamSettings:
    """Auxiliary class for easier setting access. Implemented methods should behave like dictionary, but attributes may be accesed only by dot syntax: e.g. globalSettings['nodeColor'] -> globalSettings.nodeColor
    
    :param kw: 
    """
    def __init__(self,**kw):
        self.__dict__.update(kw)
    def copy(self):
        return copy.deepcopy(self)
    def update(self,d):
        self.__dict__.update(copy.deepcopy(d.__dict__))
    def updateFromDict(self,d):
        self.__dict__.update(d)
    def __getitem__(self,key):
        return self.__dict__[key]
    def __setitem__(self,key,val):
        self.__dict__[key] = val
    def iteritems(self):
        return self.__dict__.items()
    def iterkeys(self):
        return self.__dict__.keys()


# some global variables
# different colors used to draw individual enetities
defaultGlobalSettings = EduBeamSettings(
    nodeColor   = [0.7,0.0,0.0],
    elemColor   = [0.25,0.25,0.25],
    bcColor     = [0.3,0.3,0.3],
    nForceColor = [0.5,0.0,0.25],
    vForceColor = [0.0,0.6,0.0],
    mForceColor = [0.0,0.0,0.65],
    loadColor   = [0.0, 0.4,0.4],
    temperatureColor = [0.5,0.5,0.5],
    defgeoColor  = [0.1,0.1,0.1],
    rForceColor  = [1.0,0.4,0.8],
    defaultColor = [0,0,0], # black
    hilitColor   = [1.0,0.5,0.0],
    previewColor = [0.0,1.0,0.0],
    elemthick    = 3.0,
    defaultthick = 1.0,
)
"""Dictionary of default setup variables"""

colorsInDefaultSetup = (
    'nodeColor',
    'elemColor',
    'bcColor',
    'nForceColor',
    'vForceColor',
    'mForceColor',
    'loadColor',
    'temperatureColor',
    'defgeoColor',
    'rForceColor',
    'defaultColor',
    'hilitColor',
    'previewColor',
)

gridOrigin = [-5.0,-5.0]
gridDelta  = [1.0,1.0]
gridCount  = 30
gridSnap   = [0.1,0.1]
defaultGlobalGridSettings = EduBeamSettings(
    gridOrigin = gridOrigin,
    gridDelta  = gridDelta,
    gridCount  = gridCount,
    gridSnap   = gridSnap,
)
"""Dictionary of default global grid settings variables"""

# scales controlling the size
bcSize           = 0.4
loadSize         = 1.0
deformationScale = 1.0
intForceScale    = 1.0
lineWidthCoeff   = 1.0
momentForceRatio = 1.0
pDsplSize        = 1.0
fontSize         = '12' # 10,12,18
useUniLoadSize   = 1 # int for easier better str -> bool conversion
defaultGlobalSizesScales = EduBeamSettings(
    bcSize           = bcSize,
    loadSize         = loadSize,
    deformationScale = deformationScale,
    intForceScale    = intForceScale,
    lineWidthCoeff   = lineWidthCoeff,
    momentForceRatio = momentForceRatio,
    pDsplSize        = pDsplSize,
    fontSize         = fontSize,
    useUniLoadSize   = useUniLoadSize,
)
"""Dictionary of default global sizes and scales settings"""

# Display flags, controlling display of individual entity groups
bcDisplayFlag          = True
loadDisplayFlag        = True
nodeDisplayFlag        = True
labelDisplayFlag       = True
gridDisplayFlag        = True
snapGridFlag           = True
deformationDisplayFlag = False
intForcesDisplayFlag   = [False, False, False, False] #N,V,M, Reactions
valuesDisplayFlag      = True
axesDisplayFlag        = True
defaultGlobalFlags = EduBeamSettings(
    bcDisplayFlag          = bcDisplayFlag,
    loadDisplayFlag        = loadDisplayFlag,
    nodeDisplayFlag        = nodeDisplayFlag,
    labelDisplayFlag       = labelDisplayFlag,
    gridDisplayFlag        = gridDisplayFlag,
    snapGridFlag           = snapGridFlag,
    deformationDisplayFlag = deformationDisplayFlag,
    intForcesDisplayFlag   = intForcesDisplayFlag,
    valuesDisplayFlag      = valuesDisplayFlag,
    axesDisplayFlag        = axesDisplayFlag,
)
"""Dictionary of default global flags"""



globalSettings = defaultGlobalSettings.copy()
"""Dictionary of global settings variables"""
globalGridSettings = defaultGlobalGridSettings.copy()
"""Dictionary of global grid settings variables"""
globalSizesScales = defaultGlobalSizesScales.copy()
"""Dictionary of global sizes and scales settings"""
globalFlags = defaultGlobalFlags.copy()
"""Dictionary of global flags"""

from ebio import loadConfiguration
newDicts = loadConfiguration()
globalSettings.updateFromDict(newDicts.get('globalSettings',{}))
globalGridSettings.updateFromDict(newDicts.get('globalGridSettings',{}))
globalSizesScales.updateFromDict(newDicts.get('globalSizesScales',{}))
globalFlags.updateFromDict(newDicts.get('globalFlags',{}))

globalFlags.intForcesDisplayFlag = [False,False,False,False]
globalFlags.deformationDisplayFlag = False
