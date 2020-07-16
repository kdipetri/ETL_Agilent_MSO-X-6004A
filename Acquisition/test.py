# -*- coding: utf-8 -*-
## Import python modules - Not all of these are used in this program; provided for reference
import sys
import pyvisa as visa # PyVisa info @ http://PyVisa.readthedocs.io/en/stable/
import argparse
import time
import struct
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import datetime

USER_REQUESTED_POINTS = 1250#numPoints#1250
SCOPE_VISA_ADDRESS = "TCPIP::192.168.133.2::INSTR"  # MSOX6004A
GLOBAL_TOUT =  10000 # IO time out in milliseconds

rm = visa.ResourceManager() # This uses PyVisa; PyVisa info @ http://PyVisa.readthedocs.io/en/stable/
try:
    KsInfiniiVisionX = rm.open_resource(SCOPE_VISA_ADDRESS)
except Exception:
    print "Unable to connect to oscilloscope at " + str(SCOPE_VISA_ADDRESS) + ". Aborting script.\n"
    sys.exit()


KsInfiniiVisionX.timeout = GLOBAL_TOUT

KsInfiniiVisionX.clear()
KsInfiniiVisionX.write('*RST')
KsInfiniiVisionX.write(':AUTOSCALE')

# set to a time range we're interested in
hScale=125e-9
KsInfiniiVisionX.write(':TIMebase:RANGe {}'.format(hScale)) ## full-scale horizontal time in s. Range value is ten times the time-per division value.
KsInfiniiVisionX.write(':TIMebase:REFerence:PERCent 50') ## percent of screen location

# set to a horizontal range we're interested in
KsInfiniiVisionX.write('CHANnel1:SCALe {}'.format(0.02))
KsInfiniiVisionX.write('CHANnel1:OFFSet {}'.format(-0.02 * 3))

# set to a sampling rate we're interested in
samplingrate = 10e+9# 10 GHz
KsInfiniiVisionX.write(':ACQuire:SRATe:ANALog {}'.format(samplingrate))

# testing interpolation
#KsInfiniiVisionX.write(':ACQuire:INTerpolate 0') ## interpolation is set off (otherwise its set to auto, which cause errors downstream)


# set to a bandwidth we're intereseted in 
KsInfiniiVisionX.write('ch1:bandwidth full')

# now we're ready to acquire
KsInfiniiVisionX.write(':SINGLE')
KsInfiniiVisionX.write(':WAVEFORM:SOURCE CHANNEL1')
KsInfiniiVisionX.write(':WAVEFORM:FORMAT WORD')
KsInfiniiVisionX.write(":WAVeform:BYTeorder LSBFirst") # Explicitly set this to avoid confusion - only applies to WORD FORMat
KsInfiniiVisionX.write(":WAVeform:UNSigned 0") # Explicitly set this to avoid confusion

# Testing for grant...
RANGE = float(KsInfiniiVisionX.query(':CHANnel1:RANGE?'))
YINC  = float(KsInfiniiVisionX.query(':WAVEFORM:YINCREMENT?'))
print("RANGE {}".format(RANGE))
print("YINC {}".format(YINC))
print("RANGE/YINC {}".format(RANGE/YINC))


# testing aquistion type
ACQ_TYPE = str(KsInfiniiVisionX.query(":ACQuire:TYPE?")).strip("\n")
ACQ_MODE = str(KsInfiniiVisionX.query(":ACQuire:MODE?")).strip("\n")
print("Acquisition type: {}".format(ACQ_TYPE))
print("Acquisition mode: {}".format(ACQ_MODE))

# Get preamble
Pre = KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel1;:WAVeform:PREamble?").split(',')
Y_INCrement_Ch1 = float(Pre[7]) # Voltage difference between data points; Could also be found with :WAVeform:YINCrement? after setting :WAVeform:SOURce
Y_ORIGin_Ch1    = float(Pre[8]) # Voltage at center screen; Could also be found with :WAVeform:YORigin? after setting :WAVeform:SOURce
Y_REFerence_Ch1 = float(Pre[9]) # Specifies the data point where y-origin occurs, always zero; Could also be found with :WAVeform:YREFerence? after setting :WAVeform:SOURce
#KsInfiniiVisionX.write('WAVEFORM:DATA?')
print("RANGE/YINC {}".format(RANGE/Y_INCrement_Ch1))

Data_Ch1 = np.array(KsInfiniiVisionX.query_binary_values(':WAVeform:SOURce CHANnel1;DATA?', "h", False))
for x in range(0,len(Data_Ch1)):
    if x < 10: print Data_Ch1[x]
Data_Ch1 = ((Data_Ch1-Y_REFerence_Ch1)*Y_INCrement_Ch1)+Y_ORIGin_Ch1
# this data doesn't make sense

print("NPOINTS {}".format(len(Data_Ch1)))

for x in range(0,len(Data_Ch1)):
    if x < 10: print Data_Ch1[x]

