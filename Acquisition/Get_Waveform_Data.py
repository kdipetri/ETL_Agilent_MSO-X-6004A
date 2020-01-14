# -*- coding: utf-8 -*-
## DO NOT CHANGE ABOVE LINE

'''
Python for Test and Measurement

Requires VISA installed on Control PC
'keysight.com/find/iosuite'
Requires PyVISA to use VISA in Python
'https://urldefense.proofpoint.com/v2/url?u=http-3A__PyVisa.sourceforge.net_PyVisa_&d=DwIGaQ&c=gRgGjJ3BkIsb5y6s49QqsA&r=WaY4b_RNg9kVxqHEJOskN4uGpB532--0MQsZGLeDquI&m=DShS7Q73R_pW_NS1p6GeFCn8KkFCpZISblb9A7s49mM&s=rrzBcNr-iey96_Vw5usvxjAlrnb7qpygcCUQ6pDPwG8&e= '

Keysight IO Libraries 18.1.22713.0
Anaconda Python 2.7.14 64 bit
PyVISA 1.9.0
Windows 7 Enterprise, 64 bit

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
 Copyright © 2017 Keysight Technologies Inc. All rights reserved.

You have a royalty-free right to use, modify, reproduce and distribute this
example file (and/or any modified version) in any way you find useful, provided
that you agree that Keysight has no warranty, obligations or liability for any
Sample Application Files.

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
'''

# =============================================================================
# Import Python modules
# =============================================================================

# Import python modules - Not all of these are used in this program; provided
# for reference
import sys
import visa # PyVisa info @ https://urldefense.proofpoint.com/v2/url?u=http-3A__PyVisa.readthedocs.io_en_stable_&d=DwIGaQ&c=gRgGjJ3BkIsb5y6s49QqsA&r=WaY4b_RNg9kVxqHEJOskN4uGpB532--0MQsZGLeDquI&m=DShS7Q73R_pW_NS1p6GeFCn8KkFCpZISblb9A7s49mM&s=DHfDXheixAJJeGVe9R3VaAd3Tgp1Ofj7THiQsMzde5s&e= 
import time
import struct
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

# =============================================================================
# DEFINE CONSTANTS
# =============================================================================

# Number of Points to request
USER_REQUESTED_POINTS = 2000

# Number of waveforms to acquire and transfer:
NUMBER_WAVEFORMS = 1

# Set format for output file to save waveform data:
OUTPUT_FILE = 'NONE'  # CSV, BINARY, BOTH, or NONE

# Load data from output file(s) back into Python:
LOAD_SAVED_FILES = 'YES'  # 'YES' or 'NO'

# Report status details and throughput measurements:
VERBOSE_MODE = 'ON'  # 'ON' or 'OFF'

# Initialization constants
#SCOPE_VISA_ADDRESS = "USB0::0x2A8D::0x1770::MY56311141::0::INSTR"  # MSOX3104T
#SCOPE_VISA_ADDRESS = "TCPIP0::192.168.1.110::inst0::INSTR"  # MSOX3104T
#SCOPE_VISA_ADDRESS = 'TCPIP0::10.80.7.194::inst0::INSTR'  # 3kT COS
SCOPE_VISA_ADDRESS = 'TCPIP0::192.168.1.111::hislip0::INSTR'  # MSOX3054A
#SCOPE_VISA_ADDRESS = "USB0::0x2A8D::0x1797::CN57046145::0::INSTR"  # DSOX1102G
#SCOPE_VISA_ADDRESS = "TCPIP0::192.168.0.113::inst0::INSTR"  # MSOX6004A
#SCOPE_VISA_ADDRESS = "USB0::0x0957::0x1790::MY56050705::0::INSTR"  # MSOX6004A
#SCOPE_VISA_ADDRESS = "msox3104t"  # This is a VISA alias in Connection Expert
#SCOPE_VISA_ADDRESS = 'TCPIP0::192.168.0.114::inst0::INSTR'  # DSO5054A

GLOBAL_TIMEOUT = 15000  # IO timeout in milliseconds

# Define save Locations
BASE_FILE_NAME = ""
BASE_DIRECTORY = "C:\\Users\\Public\\"

# =============================================================================
# Misc tasks
# =============================================================================

# Initialize variables to clear any old data:
waveforms = False

# =============================================================================
# Connect and initialize scope
# =============================================================================

rm = visa.ResourceManager('C:\\Windows\\System32\\visa32.dll')

# Open Connection

try:
    KsInfiniiVisionX = rm.open_resource(SCOPE_VISA_ADDRESS)
except Exception:
    print "Unable to connect to oscilloscope at " + str(SCOPE_VISA_ADDRESS) \
        + ". Aborting script.\n"
    sys.exit()

# Set Global Timeout
KsInfiniiVisionX.timeout = GLOBAL_TIMEOUT

# Clear the instrument bus
KsInfiniiVisionX.clear()

# =============================================================================
# Brute Force method
# =============================================================================

# Get Number of analog channels on scope
IDN = str(KsInfiniiVisionX.query("*IDN?"))
print('\nConnected to: ' + IDN)
if VERBOSE_MODE == 'ON':
    print('VISA address: ' + SCOPE_VISA_ADDRESS)

timescale = str(KsInfiniiVisionX.query(':TIMebase:SCALe?')).replace('\n', '')
if VERBOSE_MODE == 'ON':
    print('Timescale: {:}'.format(timescale) + ' s/div\n')

# Parse *IDN? identification string
IDN = IDN.split(',')
MODEL = IDN[1]
if list(MODEL[1]) == "9":  # This is the test for the PXIe scope, M942xA)
    NUMBER_ANALOG_CHS = 2
else:
    NUMBER_ANALOG_CHS = int(MODEL[len(MODEL)-2])
NUMBER_CHANNELS_ON = 0

KsInfiniiVisionX.write(":WAVeform:POINts:MODE MAX")

# Channel 1
On_Off = int(KsInfiniiVisionX.query(":CHANnel1:DISPlay?"))
if On_Off == 1:
    Channel_Acquired = int(KsInfiniiVisionX.query(
            ":WAVeform:SOURce CHANnel1;:WAVeform:POINts?"))
else:
    Channel_Acquired = 0
if Channel_Acquired == 0:
    CHAN1_STATE = 0
    KsInfiniiVisionX.write(":CHANnel1:DISPlay OFF")
    NUMBER_CHANNELS_ON += 0
else:
    CHAN1_STATE = 1
    NUMBER_CHANNELS_ON += 1
    if NUMBER_CHANNELS_ON == 1:
        FIRST_CHANNEL_ON = 1
    LAST_CHANNEL_ON = 1
    Pre = KsInfiniiVisionX.query(
            ":WAVeform:SOURce CHANnel1;:WAVeform:PREamble?").split(',')
    Y_INCrement_Ch1 = float(Pre[7])
    Y_ORIGin_Ch1 = float(Pre[8])
    Y_REFerence_Ch1 = float(Pre[9])

if NUMBER_CHANNELS_ON == 0:
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.close()
    sys.exit("No data has been acquired.  Properly closing scope and aborting\
             script.")

# =============================================================================
# Setup data export - For repetitive acquisitions, this only needs to be done
# once unless settings are changed
# =============================================================================

KsInfiniiVisionX.write(":WAVeform:FORMat WORD")
KsInfiniiVisionX.write(":WAVeform:BYTeorder LSBFirst")
KsInfiniiVisionX.write(":WAVeform:UNSigned 0")

# Determine Acquisition Type to set points mode properly

ACQ_TYPE = str(KsInfiniiVisionX.query(":ACQuire:TYPE?")).strip("\n")
if ACQ_TYPE == "AVER" or ACQ_TYPE == "HRES":
    POINTS_MODE = "NORMal"
else:
    POINTS_MODE = "RAW"

KsInfiniiVisionX.write(":WAVeform:SOURce CHANnel" + str(FIRST_CHANNEL_ON))
KsInfiniiVisionX.write(":WAVeform:POINts MAX")
KsInfiniiVisionX.write(":WAVeform:POINts:MODE " + str(POINTS_MODE))

max_points_available = int(KsInfiniiVisionX.query(":WAVeform:POINts?"))

if USER_REQUESTED_POINTS < 100:
    USER_REQUESTED_POINTS = 100

if max_points_available < 100:
    max_points_available = 100

if USER_REQUESTED_POINTS > max_points_available or ACQ_TYPE == "PEAK":
    USER_REQUESTED_POINTS = max_points_available

KsInfiniiVisionX.write(":WAVeform:POINts " + str(USER_REQUESTED_POINTS))

number_points_to_retrieve = int(KsInfiniiVisionX.query(":WAVeform:POINts?"))

if VERBOSE_MODE == 'ON':
    print('Number of points requested: %d' % USER_REQUESTED_POINTS)
    print('Number of points available: %d' % max_points_available)
    print('Number of points to retrieve: %d\n' % number_points_to_retrieve)

Pre = KsInfiniiVisionX.query(":WAVeform:PREamble?").split(',')
X_INCrement = float(Pre[4])
X_ORIGin = float(Pre[5])
X_REFerence = float(Pre[6])
del Pre

time_axis = ((np.linspace(0, number_points_to_retrieve - 1,
             number_points_to_retrieve)-X_REFerence) * X_INCrement) + X_ORIGin
if ACQ_TYPE == "PEAK":  # This means Peak Detect Acq. Type
    time_axis = np.repeat(time_axis, 2)

## Determine number of bytes that will actually be transferred and set the "chunk size" accordingly.

## Get the waveform format
WFORM = str(KsInfiniiVisionX.query(":WAVeform:FORMat?"))
if WFORM == "BYTE":
    FORMAT_MULTIPLIER = 1
else: #WFORM == "WORD"
    FORMAT_MULTIPLIER = 2

if ACQ_TYPE == "PEAK":
    POINTS_MULTIPLIER = 2
else:
    POINTS_MULTIPLIER = 1

TOTAL_BYTES_TO_XFER = POINTS_MULTIPLIER * number_points_to_retrieve * FORMAT_MULTIPLIER + 11

## Set chunk size:
if TOTAL_BYTES_TO_XFER >= 400000:
    KsInfiniiVisionX.chunk_size = TOTAL_BYTES_TO_XFER

# =============================================================================
# Test throughput for multiple waveforms without scaling - JM
# =============================================================================

i = 0
waveforms = np.zeros((number_points_to_retrieve, NUMBER_WAVEFORMS))

if VERBOSE_MODE == 'ON':
    print('Acquiring {:,} waveform(s)...'.format(NUMBER_WAVEFORMS))

start_time = time.clock()  # Time acquiring waveforms and importing the data

while i < NUMBER_WAVEFORMS:
    KsInfiniiVisionX.query(':DIG;*OPC?')
    waveforms[:, i] = np.array(KsInfiniiVisionX.query_binary_values(
            ':WAVeform:SOURce CHANnel1;DATA?', "h", False))
    i += 1

acquisition_time = time.clock() - start_time
acquisition_rate = NUMBER_WAVEFORMS/acquisition_time

if VERBOSE_MODE == 'ON':
    print('Done acquiring and importing {:,} '.format(NUMBER_WAVEFORMS)
          + '{:,}-point waveform(s).\n'.format(number_points_to_retrieve)
          + 'This took {:.3f} seconds '.format(acquisition_time)
          + '({:.1f} waveforms/s).'.format(acquisition_rate) + '\n')

## Scales the waveform
## One could just save off the preamble factors and post process this later.

if VERBOSE_MODE == 'ON':
    print('Scaling {:,} waveform(s)...'.format(NUMBER_WAVEFORMS))

start_time = time.clock() # Time how long it takes to scale the data

time_axis = ((np.linspace(0, number_points_to_retrieve-1,
            number_points_to_retrieve)-X_REFerence)*X_INCrement)+X_ORIGin
waveforms = ((waveforms-Y_REFerence_Ch1)*Y_INCrement_Ch1)+Y_ORIGin_Ch1

scaling_time = time.clock() - start_time
scaling_rate = NUMBER_WAVEFORMS/scaling_time

if VERBOSE_MODE == 'ON':
    print('Done scaling {:,} '.format(NUMBER_WAVEFORMS)
          + '{:,}-point waveform(s).\n'.format(number_points_to_retrieve)
          + 'This took {:.3f} seconds '.format(scaling_time)
          + '({:.1f} waveforms/s).'.format(scaling_rate) + '\n')

## Reset the chunk size back to default if needed.
if TOTAL_BYTES_TO_XFER >= 400000:
    KsInfiniiVisionX.chunk_size = 20480

# =============================================================================
# Create file name with date/time tag
# =============================================================================

# File name will be a date/time value with any BASE_FILE_NAME appended
time_stamp = time.localtime()
year = time_stamp[0]
month = time_stamp[1]
day = time_stamp[2]
hour = time_stamp[3]
minute = time_stamp[4]
second = time_stamp[5]
date_stamp = '{:d}'.format(year) + '-' + '{:0>2d}'.format(month) + '-' + \
            '{:0>2d}'.format(day) + '_' + '{:0>2d}'.format(hour) + '-' + \
            '{:0>2d}'.format(minute) + '-' + '{:0>2d}'.format(second)

if len(BASE_FILE_NAME) > 0:
    BASE_FILE_NAME = '_' + BASE_FILE_NAME
filename = BASE_DIRECTORY + date_stamp + BASE_FILE_NAME

# =============================================================================
# Save waveform data to CSV file and load it back into Python
# =============================================================================

if OUTPUT_FILE == 'CSV' or OUTPUT_FILE == 'BOTH':  # Save CSV file
    if VERBOSE_MODE == 'ON':
        print('Saving {:,} waveform(s) in CSV format...'.format(
                NUMBER_WAVEFORMS))
    start_time = time.clock()  # Time saving waveform data to a CSV file
    header = "Time (s),Channel 1 (V)\n"
    csv_file = filename + '.csv'
    with open(csv_file, 'w') as filehandle:
        filehandle.write(header)
        np.savetxt(filehandle, np.insert(waveforms, 0, time_axis, axis=1), delimiter=',')
    csv_saving_time = time.clock() - start_time
    csv_saving_rate = NUMBER_WAVEFORMS/csv_saving_time
    print('Done saving {:,} '.format(NUMBER_WAVEFORMS)
          + '{:,}-point waveform(s) to file:%5Cn'.format(
                  number_points_to_retrieve) + '    ' + csv_file)
    if VERBOSE_MODE == 'ON':
        print('This took {:.3f} seconds '.format(csv_saving_time)
              + '({:.1f} waveforms/s).'.format(csv_saving_rate) + '\n')
    del start_time

    if LOAD_SAVED_FILES == 'YES':
        if VERBOSE_MODE == 'ON':
            print('Loading waveform data from {:} back into Python...'
                  .format(csv_file))
        start_time = time.clock()
        with open(csv_file, 'r') as filehandle:  # r means open for reading
            recalled_CSV = np.loadtxt(filehandle, delimiter=',', skiprows=1)
        csv_loading_time = time.clock() - start_time
        csv_loading_rate = NUMBER_WAVEFORMS/csv_loading_time
        del filehandle, header
        if VERBOSE_MODE == 'ON':
            print('Done loading waveform data into NumPy array: recalled_CSV\n'
                  + 'This took {:.3f} seconds '.format(csv_loading_time)
                  + '({:.1f} waveforms/s).'.format(csv_loading_rate))
        del start_time

# =============================================================================
# Save waveform data to numpy file and load it back into Python
# =============================================================================

if OUTPUT_FILE == 'BINARY' or OUTPUT_FILE == 'BOTH':  # Save NPY file
    if VERBOSE_MODE == 'ON':
        print('Saving {:,} waveform(s) in binary (NumPy) format...'
              .format(NUMBER_WAVEFORMS))
    start_time = time.clock()  # Time saving waveform data to a numpy file
    header = "Time (s),Channel 1 (V)\n"
    npy_file = filename + '.npy'
    with open(npy_file, 'wb') as filehandle:
        np.save(filehandle, np.insert(waveforms, 0, time_axis, axis=1))
        npy_saving_time = time.clock() - start_time
        npy_saving_rate = NUMBER_WAVEFORMS/npy_saving_time
    print('Done saving {:,} '.format(NUMBER_WAVEFORMS)
          + '{:,}-point waveform(s) to file:%5Cn'.format(
                  number_points_to_retrieve) + '    ' + npy_file)
    if VERBOSE_MODE == 'ON':
        print('This took {:.3f} seconds '.format(npy_saving_time)
              + '({:.1f} waveforms/s).'.format(npy_saving_rate) + '\n')

    if LOAD_SAVED_FILES == 'YES':
        if VERBOSE_MODE == 'ON':
            print('Loading waveform data from {:} back into Python...'
                  .format(npy_file))
        start_time = time.clock()  # Time loading waveform data from NPY file
        with open(npy_file, 'rb') as filehandle:  # rb means read binary
            recalled_NPY = np.load(filehandle)
        npy_loading_time = time.clock() - start_time
        npy_loading_rate = NUMBER_WAVEFORMS/npy_loading_time
        del filehandle, npy_file, header
        if VERBOSE_MODE == 'ON':
            print('Done loading waveform data into NumPy array: recalled_NPY\n'
                  + 'This took {:.3f} seconds '.format(npy_loading_time)
                  + '({:.1f} waveforms/s).'.format(npy_loading_rate))
        del start_time

# =============================================================================
# ## Done with scope operations - Close connection to scope
# =============================================================================

KsInfiniiVisionX.clear()
KsInfiniiVisionX.close()

print('\nDone.')
