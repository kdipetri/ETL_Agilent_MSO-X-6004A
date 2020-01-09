# adapted for MSO-X 92004A

"""
VISA Control: FastFrame Acquisition
Tektronix DPO7254 Control
FNAL November 2018
CMS MTD ETL Test beam
"""

import numpy as np
# import matplotlib.pyplot as plt
import sys
import optparse
import argparse
import signal
import os
import time
import shutil
import datetime
from shutil import copy

stop_asap = False

import pyvisa as visa

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        shutil.copytree(item, d, symlinks, ignore)
def copynew(source,destination):
    for files in source:
        shutil.copy(files,destination)

"""#################SEARCH/CONNECT#################"""
# establish communication with dpo
rm = visa.ResourceManager()
dpo = rm.open_resource('TCPIP::192.168.133.2::INSTR')
dpo.timeout = 3000000
dpo.encoding = 'latin_1'
print(dpo.query('*idn?'))

parser = argparse.ArgumentParser(description='Run info.')

parser.add_argument('--numEvents',metavar='Events', type=str,default = 500, help='numEvents (default 500)',required=True)
parser.add_argument('--runNumber',metavar='runNumber', type=str,default = -1, help='runNumber (default -1)',required=False)
parser.add_argument('--sampleRate',metavar='sampleRate', type=str,default = 6, help='Sampling rate (default 6)',required=False)
parser.add_argument('--horizontalWindow',metavar='horizontalWindow', type=str,default = 125, help='horizontal Window (default 125)',required=False)
# parser.add_argument('--numPoints',metavar='Points', type=str,default = 500, help='numPoints (default 500)',required=True)
parser.add_argument('--trigCh',metavar='trigCh', type=str, default='AUX',help='trigger Channel (default Aux (-0.1V))',required=False)
parser.add_argument('--trig',metavar='trig', type=float, default= -0.05, help='trigger value in V (default Aux (-0.05V))',required=False)
parser.add_argument('--trigSlope',metavar='trigSlope', type=str, default= 'NEGative', help='trigger slope; positive(rise) or negative(fall)',required=False)

parser.add_argument('--vScale1',metavar='vScale1', type=float, default= 0.5, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale2',metavar='vScale2', type=float, default= 0.2, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale3',metavar='vScale3', type=float, default= 0.2, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale4',metavar='vScale4', type=float, default= 0.2, help='Vertical scale, volts/div',required=False)

parser.add_argument('--timeoffset',metavar='timeoffset', type=float, default=-130, help='Offset to compensate for trigger delay. This is the delta T between the center of the acquisition window and the trigger. (default for NimPlusX: -160 ns)',required=False)



args = parser.parse_args()
trigCh = str(args.trigCh) 
runNumberParam = int(args.runNumber) 
if trigCh != "AUX": trigCh = 'CHANnel'+trigCh
trigLevel = float(args.trig)
triggerSlope = args.trigSlope
timeoffset = float(args.timeoffset)*1e-9
print "timeoffset is ",timeoffset
date = datetime.datetime.now()

"""#################CONFIGURE INSTRUMENT#################"""
# variables for individual settings
hScale = float(args.horizontalWindow)*1e-9
samplingrate = float(args.sampleRate)*1e+9
# hScale = 100e-9 # horizontal scale in seconds
numEvents = int(args.numEvents) # number of events for each file
# numPoints = int(args.numPoints) # number of points to be acquired per event
numPoints = samplingrate*hScale
# samplerate =  numPoints/hScale ## sampling rate
# print "samplerate is = ", samplerate

#vertical scale
vScale_ch1 =float(args.vScale1) # in Volts for division
vScale_ch2 =float(args.vScale2) # in Volts for division
vScale_ch3 =float(args.vScale3) # in Volts for division
vScale_ch4 =float(args.vScale4) # in Volts for division

#vertical position
vPos_ch1 = -2  # in Divisions
vPos_ch2 = 3  # in Divisions
vPos_ch3 = 3  # in Divisions
vPos_ch4 = 3  # in Divisions

date = datetime.datetime.now()

# helpful directory info
this_package="/home/daq/ETL_Agilent_MSO-X-6004A/Acquisition"

"""#################CONFIGURE RUN NUMBER#################"""
# increment the last runNumber by 1

if runNumberParam == -1:
    #RunNumberFile = '/home/daq/JARVIS/AutoPilot/otsdaq_runNumber.txt'
	RunNumberFile = "{}/runNumber.txt".format(this_package)
	with open(RunNumberFile) as file:
	    runNumber = int(file.read())
	print('######## Starting RUN {} ########\n'.format(runNumber))
	print('---------------------\n')
	print(date)
	print('---------------------\n')

else: runNumber = runNumberParam
#with open('runNumber.txt','w') as file:
#    file.write(str(runNumber+1))


"""#################SET THE OUTPUT FOLDER#################"""
# The scope save runs localy on a shared folder with
# path = r"C:\Users\Public\Documents\Infiniium\Test_Feb18"
path = r"C:\Users\Public\Documents\Infiniium\Test_March21"
dpo.write(':DISK:MDIRectory "{}"'.format(path)) ## what is this for?
#log_path = "/home/daq/2019_04_April_CMSTiming/KeySightScope/ETL_Agilent_MSO-X-92004A/Acquisition/Logbook.txt"
#run_log_path = "/home/daq/2019_04_April_CMSTiming/KeySightScope/ETL_Agilent_MSO-X-92004A/Acquisition/RunLog.txt"
log_path     = "{}/Logbook.txt".format(this_package)
run_log_path = "{}/RunLog.txt".format(this_package)

#Write in the log file
logf = open(log_path,"a+")
logf.write("\n\n#### SCOPE LOGBOOK -- RUN NUMBER {} ####\n\n".format(runNumber))
logf.write("Date:\t{}\n".format(date))
logf.write("---------------------------------------------------------\n")
logf.write("Number of events per file: {} \n".format(numEvents))
logf.write("---------------------------------------------------------\n\n")


"""#################SCOPE HORIZONTAL SETUP#################"""
# dpo setup

dpo.write(':STOP;*OPC?')

dpo.write(':TIMebase:RANGe {}'.format(hScale)) ## Sets the full-scale horizontal time in s. Range value is ten times the time-per division value.
dpo.write(':TIMebase:REFerence:PERCent 50') ## percent of screen location
dpo.write(':ACQuire:SRATe:ANALog {}'.format(samplingrate))
#dpo.write(':TIMebase:POSition 25E-9') ## offset
print ':TIMebase:POSition {}'.format(timeoffset)
dpo.write(':TIMebase:POSition {}'.format(timeoffset)) ## offset
dpo.write(':ACQuire:MODE SEGMented') ## fast frame/segmented acquisition mode
dpo.write(':ACQuire:SEGMented:COUNt {}'.format(numEvents)) ##number of segments to acquire
dpo.write(':ACQuire:POINts:ANALog {}'.format(numPoints))
dpo.write(':ACQuire:INTerpolate 0') ## interpolation is set off (otherwise its set to auto, which cause errors downstream)

print("# SCOPE HORIZONTAL SETUP #")
print('Horizontal scale set to {} for division\n'.format(hScale))

logf.write("HORIZONTAL SETUP\n")
logf.write('- Horizontal scale set to {} s for division\n\n'.format(hScale))

"""#################SCOPE CHANNELS BANDWIDTH#################"""
# dpo.write(':ACQuire:BANDwidth MAX') ## set the bandwidth to maximum
# dpo.write('CHANnel1:ISIM:BANDwidth 2.0E+09')
# dpo.write('CHANnel2:ISIM:BANDwidth 2.0E+09')
# dpo.write('CHANnel3:ISIM:BANDwidth 2.0E+09')
# dpo.write('CHANnel4:ISIM:BANDwidth 2.0E+09')

# dpo.write('CHANnel1:ISIM:BWLimit 1')
# dpo.write('CHANnel2:ISIM:BWLimit 1')
# dpo.write('CHANnel3:ISIM:BWLimit 1')
# dpo.write('CHANnel4:ISIM:BWLimit 1')

dpo.write(':ACQuire:BANDwidth 3.5E9')
"""#################SCOPE VERTICAL SETUP#################"""
#vScale expressed in Volts
dpo.write('CHANnel1:SCALe {}'.format(vScale_ch1))
dpo.write('CHANnel2:SCALe {}'.format(vScale_ch2))
dpo.write('CHANnel3:SCALe {}'.format(vScale_ch3))
dpo.write('CHANnel4:SCALe {}'.format(vScale_ch4))

dpo.write('CHANnel1:OFFSet {}'.format(-vScale_ch1 * vPos_ch1))
dpo.write('CHANnel2:OFFSet {}'.format(-vScale_ch2 * vPos_ch2))
dpo.write('CHANnel3:OFFSet {}'.format(-vScale_ch3 * vPos_ch3))
dpo.write('CHANnel4:OFFSet {}'.format(-vScale_ch4 * vPos_ch4))


logf.write("VERTICAL SETUP\n")
logf.write('- CH1: vertical scale set to {} V for division\n'.format(vScale_ch1))
logf.write('- CH2: vertical scale set to {} V for division\n'.format(vScale_ch2))
logf.write('- CH3: vertical scale set to {} V for division\n'.format(vScale_ch3))
logf.write('- CH4: vertical scale set to {} V for division\n\n'.format(vScale_ch4))


"""#################TRIGGER SETUP#################"""
dpo.write('TRIGger:MODE EDGE; :TRIGger:EDGE:SOURce %s; :TRIGger:LEVel %s, %f'%(trigCh, trigCh, trigLevel))
dpo.write(':TRIGger:EDGE:SLOPe %s;' %(triggerSlope))

trigprint='%.3f'%(trigLevel)
print("# TRIGGER SETUP #")
print('Trigger scale set to %s V\n'%(trigprint))

logf.write("TRIGGER SETUP\n")
logf.write('- Trigger Channel set to %s\n'%(trigCh))
logf.write('- Trigger scale set to %s V\n\n\n\n'%(trigprint))
logf.close()
print('Horizontal, vertical, and trigger settings configured.\n')
#print("Trigger!")

status = ""
status = "busy"

run_logf = open(run_log_path,"w")
run_logf.write(status)
#run_logf.write("\n")
run_logf.close()
#raise exception("suck it")

"""#################DATA TRANSFERRING#################"""
# configure data transfer settings
#dpo.timeout = 600000
time.sleep(2)
#dpo.write(':DIGitize')
#print ("digitize")

print(dpo.write(':CDISplay'))


# karri debugging
ACQ_DONE=1
ACQ_NOT_DONE=0

print("Acquiring signal(s) \n")

# Setup start time
StartTime = time.time()
MAX_TIME_TO_WAIT = 30 # 30 seconds for now -1 when done debugging

# Clear all status registers (set them to 0)
print ("Clear status registers \n")
dpo.write("*CLS")

# Begin acquistion with non-blocking :SINGle command
print("Begin acquistion with SINGle command \n")
dpo.write(":SINGle")

# Could concatinate two commands for performance 
#dpo.write('*CLS;:SINGle')

# Ask oscilliscope if its done
print ("Getting status \n")
#Status = int(dpo.query(":ADER?")) # gets stuck
#Status = int(dpo.query(":PDER?")) # gets stuck
#Status = int(dpo.query("*OPC?")) # gets set to 1 when acq is done
Status = 0

# Poll oscilloscope until Status is one
while Status == ACQ_NOT_DONE and ( time.time() - StartTime <= MAX_TIME_TO_WAIT) :
    #print Status, StartTime - time.time()
    time.sleep(0.1) 
    Status = int(dpo.query("*OPC?"))
    #Status = int(dpo.query(":ADER?"))
    #Status = int(dpo.query(":PDER?"))

if Status == ACQ_DONE : 
    print "Signal acquired \n"

    tmp_file = open(run_log_path,"w")
    status = "writing"
    tmp_file.write(status)
    tmp_file.write("\n")
    tmp_file.close()
    

    # save files
    # note: this scope is weird and can only save new waveforms to a usb 
    scope_usb_path = "U:\\usb\\Waveforms"
    print(dpo.query('*OPC?'))
    print("Ready to save all segments")

    channels = [1,2,3,4]
    for channel in channels: 
        dpo.write(':DISK:SEGMented ALL') ##save all segments (as opposed to just the current segment)
        time.sleep(0.5)
        dpo.write(':DISK:SAVE:WAVeform CHANnel{} ,"{}\\Waveform_CH{}_{}", BIN,ON'.format(channel,scope_usb_path,channel,runNumber))
    
        print(dpo.query('*OPC?'))
        print("Saved Channel {} waveform".format(channel))
        time.sleep(1)

    
    tmp_file2 = open(run_log_path,"w")
    status = "ready"
    tmp_file2.write(status)
    tmp_file2.write("\n")
    tmp_file2.close()
    
    dpo.close()

else : # Acquistion failed for some reason
    print ("Max wait time exceeded")    
    print ("Visually check scope for trigger, adjust if needed")
    print ("Properly closing the scope connection and exiting script")
    
    # stop scop 
    dpo.query(":STOP;*OPC?")
    dpo.clear()
    dpo.close()
        

