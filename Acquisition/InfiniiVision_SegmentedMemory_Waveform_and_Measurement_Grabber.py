# -*- coding: utf-8 -*-

## DO NOT CHANGE ABOVE LINE

# Python for Test and Measurement
#
# Requires VISA installed on Control PC
# 'keysight.com/find/iosuite'
# Requires PyVISA to use VISA in Python
# 'https://urldefense.proofpoint.com/v2/url?u=http-3A__pyvisa.sourceforge.net_pyvisa_&d=DwIGaQ&c=gRgGjJ3BkIsb5y6s49QqsA&r=WaY4b_RNg9kVxqHEJOskN4uGpB532--0MQsZGLeDquI&m=nbwL3wrWa9-M582buiRe_jYlTK6MHTy0ndiB1r0bUBM&s=fI6YxZ9VTlm486rn-3pHfMbvAGdnLEn0PLw-xKkpIaQ&e= '

## Keysight IO Libraries 17.1.19xxx
## Anaconda Python 2.7.7 64 bit
## pyvisa 1.8
## Windows 7 Enterprise, 64 bit

##"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
## Copyright © 2015 Keysight Technologies Inc. All rights reserved.
##
## You have a royalty-free right to use, modify, reproduce and distribute this
## example files (and/or any modified version) in any way you find useful, provided
## that you agree that Keysight has no warranty, obligations or liability for any
## Sample Application Files.
##
##"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

##############################################################################################################################################################################
##############################################################################################################################################################################
## Import Python modules
##############################################################################################################################################################################
##############################################################################################################################################################################

## Import python modules - Not all of these are used in this program; provided for reference
import sys
import argparse
import pyvisa as visa
import time
import struct
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import datetime


## INSTRUCTIONS
## 1. Setup oscilloscope and acquire segments manually, wait until acquisition is done
## The following applies to this script under ## Initialization constants, just below these instructions
## 2. Modify VISA address; Get VISA address of oscilloscope from Keysight IO Libraries Connection Expert
## 3. Enable analog waveform saving or not.
## 3.1 Enable averaged waveform or not.
## 4.0 Enable measurements or not.
## 4.1 Enter number of measurements to take per segment under N_MEASUREMENTS
    ## At least 1 measurement MUST be enabled if measurements are enabled
## 4.2 Edit measurement header info below (MeasHeader)
## 5. Enable saving of time tags to separate file or not
## 6. Edit BASE_FILE_NAME and BASE_DIRECTORY under ## Save Locations
    ## IMPORTANT NOTE:  This script WILL overwrite previously saved files!
## 7. Edit/add/remove measurements to retrieve at ## FLAG_DEFINE_MEASUREMENTS – refer to oscilloscope programmer's guide as needed
    ## Note that desired measurements can potentially be configured to turn on channels that were otherwise off.
    ## This could potentially cause a timeout error in a few places when trying to get the waveform data, but
    ## this is taken care of.  What IS NOT taken care of is bad measurements commands.  Try them out in Keysight Connection Expert or Command Expert first
## 8. ALWAYS DO SOME TEST RUNS!!!!! and ensure you are getting what you want and it is later usable!!!!!

## Initialization constants
SCOPE_VISA_ADDRESS = "TCPIP::192.168.133.2::INSTR"  # MSOX6004A

GLOBAL_TOUT =  50000 # IO time out in milliseconds

## Pull waveform data?
GET_WFM_DATA = "YES" # "YES" or "NO" ; Automatically determines which analog channels are on, and grabs the waveform data for each segment.
    ## If you do not want to pull that channel data, turn it off, though it must be on for a measurement.
    ## One time axis is created for ALL segments, so each segment is referenced to its own trigger.
    ## One file per analog channel is created, with every segment, time tags, and segment indices.
#DO_AVERAGE = "NO" # "YES" or "NO" ; create an averaged waveform for each analog channel.  It is placed in the final column of the resulting data file..
    ## This is not done on-board the scope.  It is done in this script.


"""#################ARGUMENT PARSING#################"""

parser = argparse.ArgumentParser(description='Run info.')

parser.add_argument('--numEvents',metavar='Events', type=str,default = 500, help='numEvents (default 500)',required=True)
parser.add_argument('--runNumber',metavar='runNumber', type=str,default = -1, help='runNumber (default -1)',required=False)
parser.add_argument('--sampleRate',metavar='sampleRate', type=str,default = 6, help='Sampling rate (default 6)',required=False)
parser.add_argument('--horizontalWindow',metavar='horizontalWindow', type=str,default = 125, help='horizontal Window (default 125)',required=False)
# parser.add_argument('--numPoints',metavar='Points', type=str,default = 500, help='numPoints (default 500)',required=True)
parser.add_argument('--trigCh',metavar='trigCh', type=str, default='AUX',help='trigger Channel (default Aux (-0.1V))',required=False)
parser.add_argument('--trig',metavar='trig', type=float, default= -0.05, help='trigger value in V (default Aux (-0.05V))',required=False)
parser.add_argument('--trigSlope',metavar='trigSlope', type=str, default= 'NEGative', help='trigger slope; positive(rise) or negative(fall)',required=False)

parser.add_argument('--vScale1',metavar='vScale1', type=float, default= 1.0, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale2',metavar='vScale2', type=float, default= 0.2, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale3',metavar='vScale3', type=float, default= 1.0, help='Vertical scale, volts/div',required=False)
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

# helpful directory info
this_package="/home/daq/ETL_Agilent_MSO-X-6004A/Acquisition"

"""#################TO CONFIGURE INSTRUMENT#################"""
# variables for individual settings
hScale = float(args.horizontalWindow)*1e-9
samplingrate = float(args.sampleRate)*1e+9
numEvents = int(args.numEvents) # number of events for each file
numPoints = samplingrate*hScale
print("Sampling Rate : {}".format(samplingrate))
print("NumEvents : {}".format(numEvents))
print("NumPoints : {}".format(numPoints))

#vertical scale
vScale_ch1 =float(args.vScale1) # in Volts for division
vScale_ch2 =float(args.vScale2) # in Volts for division
vScale_ch3 =float(args.vScale3) # in Volts for division
vScale_ch4 =float(args.vScale4) # in Volts for division

#vertical position
vPos_ch1 = 1  # in Divisions
vPos_ch2 = 0  # in Divisions
vPos_ch3 = -2  # in Divisions
vPos_ch4 = -3  # in Divisions

date = datetime.datetime.now()

## File Saving Information 

## Increment the last runNumber by 1
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

BASE_DIRECTORY = "/home/daq/ETL_Agilent_MSO-X-6004A/Acquisition/tmp_output/"
BASE_FILE_NAME = "run_{}".format(runNumber)

## Output file format 
OUTPUT_FILE = "BOTH" #  CSV, BINARY, BOTH, or NONE 

##############################################################################################################################################################################
##############################################################################################################################################################################
## Main code
##############################################################################################################################################################################
##############################################################################################################################################################################

print "Script is running.  This may take a while..."

##############################################################################################################################################################################
##############################################################################################################################################################################
## Connect and initialize scope
##############################################################################################################################################################################
##############################################################################################################################################################################

## Define VISA Resource Manager & Install directory
rm = visa.ResourceManager() # this uses pyvisa

## Open Connection
## Define & open the scope by the VISA address ; # This uses PyVisa
try:
    KsInfiniiVisionX = rm.open_resource(SCOPE_VISA_ADDRESS)
except Exception:
    print "Unable to connect to oscilloscope at " + str(SCOPE_VISA_ADDRESS) + ". Aborting script.\n"
    sys.exit()

## Set Global Timeout
## This can be used wherever, but local timeouts are used for Arming, Triggering, and Finishing the acquisition... Thus it mostly handles IO timeouts
KsInfiniiVisionX.timeout = GLOBAL_TOUT

## Clear the instrument bus
KsInfiniiVisionX.clear()


# Configuring things....
KsInfiniiVisionX.write('ch1:bandwidth full')
KsInfiniiVisionX.write('ch2:bandwidth full')
KsInfiniiVisionX.write('ch3:bandwidth full')
KsInfiniiVisionX.write('ch4:bandwidth full')

## Program assumes the scope is already set up to capture the desired
## number of segments.


opc = KsInfiniiVisionX.query(":DIGITIZE;*OPC?")
#opc = KsInfiniiVisionX.query(":DIGITIZE CHANNEL1;*OPC?")

##############################################################################################################################################################################
##############################################################################################################################################################################
## Flip through segments, get time tags and make measurements
##############################################################################################################################################################################
##############################################################################################################################################################################



## Find number of segments actually acquired
NSEG = int(KsInfiniiVisionX.query(":WAVeform:SEGMented:COUNt?"))
## compare with :ACQuire:SEGMented:COUNt?
## :ACQuire:SEGMented:COUNt? is how many segments the scope was set to acquire
## :WAVeform:SEGMented:COUNt? is how many were actually acquired
## KEY POINT:
    ## Using fewer segments can result in a higher sample rate.
    ## If the user sets the scope to acquire the maximum number for segments, and STOPS it before it is done,
    ## it is likely that a higher sample rate could have been achieved.
print str(NSEG) + " segments were acquired."
if NSEG == 0:
    ## Close Connection to scope properly
    KsInfiniiVisionX.clear()
    KsInfiniiVisionX.close()
    sys.exit("No segments acquired, aborting script.")

## pre-allocate TimeTag data array
Tags =  np.zeros(NSEG)


## Flip through segments...
for n in range(1,NSEG+1,1): ## Python indices start at 0, segments start at 1

    print("Acquiring segment {}".format(n))
    KsInfiniiVisionX.write(":ACQuire:SEGMented:INDex " + str(n)) # Go to segment n

    Tags[n-1] = KsInfiniiVisionX.query(":WAVeform:SEGMented:TTAG?") # Get time tag of segment n ; always get time tags


    if GET_WFM_DATA == "YES":
        if n == 1: # Only need to do some things once

            ## Determine which channels are on, and which have acquired data, and get the vertical pre-amble info accordingly
                ## Use brute force method for readability

            CHS_ON = [0,0,0,0] # Create empty array to store channel states
            NUMBER_CHANNELS_ON = 0

            ## Channel 1
            on_off = int(KsInfiniiVisionX.query(":CHANnel1:DISPlay?"))
            Channel_acquired = int(KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel1;:WAVeform:POIN?")) # If there are no points available
            print("Channel 1, on off {}, acquired {}".format(on_off,Channel_acquired))
                ## this channel did not capture data and thus there are no points (but was turned on)
            if Channel_acquired == 0 or on_off == 0:
                KsInfiniiVisionX.write(":CHANnel1:DISPlay OFF") # Setting a channel to be a waveform source turns it on...
                CHS_ON[0] = 0
                Y_INCrement_Ch1 = "BLANK"
                Y_ORIGin_Ch1    = "BLANK"
                Y_REFerence_Ch1 = "BLANK"
            else:
                CHS_ON[0] = 1
                NUMBER_CHANNELS_ON += 1
                Pre = KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel1;:WAVeform:PREamble?").split(',')
                Y_INCrement_Ch1 = float(Pre[7]) # Voltage difference between data points
                Y_ORIGin_Ch1    = float(Pre[8]) # Voltage at center screen
                Y_REFerence_Ch1 = float(Pre[9]) # Specifies the data point where y-origin occurs, alwasy zero
                    ## The programmer's guide has a very good description of this, under the info on :WAVeform:PREamble.

            ## Channel 2
            on_off = int(KsInfiniiVisionX.query(":CHANnel2:DISPlay?"))
            Channel_acquired = int(KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel2;:WAVeform:POIN?"))
            print("Channel 2, on off {}, acquired {}".format(on_off,Channel_acquired))
            if Channel_acquired == 0 or on_off == 0:
                KsInfiniiVisionX.write(":CHANnel2:DISPlay OFF")
                CHS_ON[1] = 0
                Y_INCrement_Ch2 = "BLANK"
                Y_ORIGin_Ch2    = "BLANK"
                Y_REFerence_Ch2 = "BLANK"
            else:
                CHS_ON[1] = 1
                NUMBER_CHANNELS_ON += 1
                Pre = KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel2;:WAVeform:PREamble?").split(',')
                Y_INCrement_Ch2 = float(Pre[7])
                Y_ORIGin_Ch2    = float(Pre[8])
                Y_REFerence_Ch2 = float(Pre[9])

            ## Channel 3
            on_off = int(KsInfiniiVisionX.query(":CHANnel3:DISPlay?"))
            Channel_acquired = int(KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel3;:WAVeform:POIN?"))
            print("Channel 3, on off {}, acquired {}".format(on_off,Channel_acquired))
            if Channel_acquired == 0 or on_off == 0:
                KsInfiniiVisionX.write(":CHANnel3:DISPlay OFF")
                CHS_ON[2] = 0
                Y_INCrement_Ch3 = "BLANK"
                Y_ORIGin_Ch3    = "BLANK"
                Y_REFerence_Ch3 = "BLANK"
            else:
                CHS_ON[2] = 1
                NUMBER_CHANNELS_ON += 1
                Pre = KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel3;:WAVeform:PREamble?").split(',')
                Y_INCrement_Ch3 = float(Pre[7])
                Y_ORIGin_Ch3    = float(Pre[8])
                Y_REFerence_Ch3 = float(Pre[9])

            ## Channel 4
            on_off = int(KsInfiniiVisionX.query(":CHANnel4:DISPlay?"))
            Channel_acquired = int(KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel4;:WAVeform:POIN?"))
            print("Channel 4, on off {}, acquired {}".format(on_off,Channel_acquired))
            if Channel_acquired == 0 or on_off == 0:
                KsInfiniiVisionX.write(":CHANnel4:DISPlay OFF")
                CHS_ON[3] = 0
                Y_INCrement_Ch4 = "BLANK"
                Y_ORIGin_Ch4    = "BLANK"
                Y_REFerence_Ch4 = "BLANK"
            else:
                CHS_ON[3] = 1
                NUMBER_CHANNELS_ON += 1
                Pre = KsInfiniiVisionX.query(":WAVeform:SOURce CHANnel4;:WAVeform:PREamble?").split(',')
                Y_INCrement_Ch4 = float(Pre[7])
                Y_ORIGin_Ch4    = float(Pre[8])
                Y_REFerence_Ch4 = float(Pre[9])

            print("NUMBER_CHANNELS_ON {}".format(NUMBER_CHANNELS_ON))
            ANALOGVERTPRES = (Y_INCrement_Ch1, Y_INCrement_Ch2, Y_INCrement_Ch3, Y_INCrement_Ch4, Y_ORIGin_Ch1, Y_ORIGin_Ch2, Y_ORIGin_Ch3, Y_ORIGin_Ch4, Y_REFerence_Ch1, Y_REFerence_Ch2, Y_REFerence_Ch3, Y_REFerence_Ch4)
            del Pre, on_off, Channel_acquired

            ## Find first channel on
            ch = 1
            for each_value in CHS_ON:
                if each_value ==1:
                    FIRST_CHANNEL_ON = ch
                    break
                ch +=1
            del ch, each_value

            ## Setup data export
            #KsInfiniiVisionX.write(":WAVeform:FORMat BYTE")  # needs finesing 
            KsInfiniiVisionX.write(":WAVeform:FORMAT WORD") # 16 bit word format...
            KsInfiniiVisionX.write(":WAVeform:BYTeorder LSBFirst") # Explicitly set this to avoid confusion
            KsInfiniiVisionX.write(":WAVeform:UNSigned 0") # Explicitly set this to avoid confusion
            KsInfiniiVisionX.write(":WAVeform:SOURce CHANnel" + str(FIRST_CHANNEL_ON))  # Set waveform source to any enabled channel, here the FIRST_CHANNEL_ON
            KsInfiniiVisionX.write(":WAVeform:POINts MAX") # Set number of points to max possible for any InfiniiVision; ensures all are available
                ## If using :WAVeform:POINts MAX, be sure to do this BEFORE setting the :WAVeform:POINts:MODE as it will switch it to MAX
            KsInfiniiVisionX.write(":WAVeform:POINts:MODE RAW")  # Set this now so when the preamble is queried it knows what how many points it can retrieve from
                ## If measurements are also being made, they are made on a different record, the "measurement record."  This record can be accessed by using:
                ## :WAVeform:POINts:MODE NORMal isntead of :WAVeform:POINts:MODE RAW
            POINTS = int(KsInfiniiVisionX.query(":WAVeform:POINts?")) # Get number of points.  This is the number of points in each segment.
            print str(POINTS) + " points were acquired for each channel for each segment."

            ## Get timing pre-amble data - this can be done at any segment - it does not change segment to segment
            Pre = KsInfiniiVisionX.query(":WAVeform:PREamble?").split(',')
            AMODE        = float(Pre[1]) # Gives the scope acquisition mode
            X_INCrement = float(Pre[4]) # Time difference between data points
            X_ORIGin    = float(Pre[5]) # Always the first data point in memory
            X_REFerence = float(Pre[6]) # Specifies the data point associated with x-origin; The x-reference point is the first point displayed and XREFerence is always 0.
                ## The programmer's guide has a very good description of this, under the info on :WAVeform:PREamble.
            del Pre

            ## Pre-allocate data array
            if AMODE == 1: # This means peak detect mode
                Wav_Data = np.zeros([NUMBER_CHANNELS_ON,2*POINTS,NSEG])
                ## Peak detect mode returns twice as many points as the points query, one point each for LOW and HIGH values
            else: # For all other acquistion modes
                Wav_Data = np.zeros([NUMBER_CHANNELS_ON,POINTS,NSEG])

            ## Create time axis:
            DataTime = ((np.linspace(0,POINTS-1,POINTS)-X_REFerence)*X_INCrement)+X_ORIGin
            if AMODE == 1: # This means peak detect mode
                DataTime = np.repeat(DataTime,2)
                ##  The points come out as Low(time1),High(time1),Low(time2),High(time2)....

        ## Pull waveform data, scale it - for every segment
        ch = 1 # channel number
        i  = 0 # index of Wav_data
        for each_value in  CHS_ON:
            #if each_value == 1:
            # save all channels
            print("Channel Number {} : Index of Wav data {} : Segment {}".format(ch,i,n))
            ## Gets the waveform in 16 bit WORD format
            Wav_Data[i,:,n-1] = np.array(KsInfiniiVisionX.query_binary_values(':WAVeform:SOURce CHANnel' + str(ch) + ';DATA?', "h", False))
            ## Scales the waveform
            Wav_Data[i,:,n-1] = ((Wav_Data[i,:,n-1]-ANALOGVERTPRES[ch+7])*ANALOGVERTPRES[ch-1])+ANALOGVERTPRES[ch+3]
                ## For clarity: Scaled_waveform_Data[*] = [(Unscaled_Waveform_Data[*] - Y_reference) * Y_increment] + Y_origin
            i +=1
            ch +=1
        del ch, i,

## End of flipping through segments
## Some cleanup
if GET_WFM_DATA == "YES":
    del  ANALOGVERTPRES,Y_INCrement_Ch1, Y_ORIGin_Ch1, Y_REFerence_Ch1, Y_INCrement_Ch2, Y_ORIGin_Ch2, Y_REFerence_Ch2,Y_INCrement_Ch3, Y_ORIGin_Ch3, Y_REFerence_Ch3, Y_INCrement_Ch4, Y_ORIGin_Ch4, Y_REFerence_Ch4, X_INCrement, X_ORIGin, X_REFerence

## Close Connection to scope properly
KsInfiniiVisionX.clear()
KsInfiniiVisionX.close()

## Data save operations

## Save waveform data
if GET_WFM_DATA == "YES":

    #if DO_AVERAGE == "YES":
    #    Ave_Data = np.mean(Wav_Data,axis = 2)
    #    Wav_Data = np.dstack((Wav_Data,Ave_Data))
    #    del Ave_Data

    if OUTPUT_FILE == "CSV" or OUTPUT_FILE == "BOTH": 

        print('Saving waveform(s) in csv format...' )

        segment_indices = np.linspace(1,NSEG,NSEG)
        segment_indices = [ int(index) for index in segment_indices ] 
        #segment_indices = np.linspace(1,NSEG,NSEG, dtype = int)

        start_time = time.clock()  # Time saving waveform data to a numpy file
        i = 0
        ch = 1
        for each_value in CHS_ON:
            if each_value == 1:
                filename = BASE_DIRECTORY + BASE_FILE_NAME + "_Channel" + str(ch) + ".csv"
                with open(filename, 'w') as filehandle:
                    filehandle.write("Timestamp (s):,")
                    np.savetxt(filehandle, np.atleast_2d(Tags), delimiter=',')
                    filehandle.write("Segment Index:,")
                    np.savetxt(filehandle, np.atleast_2d(segment_indices), delimiter=',')
                    #if DO_AVERAGE == "YES":
                    #    filehandle.write("Time (s), Waveforms... Final column is averaged.\n")
                    #else:
                    filehandle.write("Time (s), Waveforms...\n")
                    np.savetxt(filehandle, np.insert(Wav_Data[i,:,:],0,DataTime,axis=1), delimiter=',')
                    csv_saving_time = time.clock() - start_time

                    print('Done saving' + '    ' + filename)
                    print('This took {:.3f} seconds '.format(csv_saving_time)
                i +=1
            ch +=1
        del each_value, ch, filehandle, filename, segment_indices



    if OUTPUT_FILE == "BINARY" or OUTPUT_FILE == "BOTH": # save NPY file

        print('Saving waveform(s) in binary (NumPy) format...' )

        start_time = time.clock()  # Time saving waveform data to a numpy file
        i = 0
        ch = 1
        for each_value in CHS_ON:
            #if each_value == 1:
            # actually save all waveforms

            header = "Time (s),Channel 1 (V)\n"
            filename = BASE_DIRECTORY + BASE_FILE_NAME + "_Channel" + str(ch) + ".npy"

            with open(filename, 'wb') as filehandle:
                np.save(filehandle, np.insert(Wav_Data[i,:,:],0,DataTime,axis=1)) 
                #np.save(filehandle, np.insert(waveforms, 0, time_axis, axis=1))
                npy_saving_time = time.clock() - start_time

            print('Done saving' + '    ' + filename)
            print('This took {:.3f} seconds '.format(npy_saving_time)
                      )
            i +=1
            ch +=1
        del each_value, ch, filehandle, filename 

del n, BASE_DIRECTORY, BASE_FILE_NAME 

print "Done."
