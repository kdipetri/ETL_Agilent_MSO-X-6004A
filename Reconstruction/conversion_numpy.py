import struct  #struct unpack result - tuple
import numpy as np
import ROOT
from ROOT import *
import time
import optparse
import argparse
import os

parser = argparse.ArgumentParser(description='Creating a root file from Binary format')

parser.add_argument('--Run',metavar='Run', type=str, help='Run Number to process',required=True)
#parser.add_argument('--FileNum',metavar='FileNum', type=int, help='File Number to process',required=True)
args = parser.parse_args()
run = args.Run
#run = 26
#fileNum= args.FileNum
fileNum=0
RawDataPath    = '/home/daq/ScopeData/Raw'
OutputFilePath = '/home/daq/ScopeData/Converted'

debug=False

def time_array(data):
    time_array = [x[0] for x in data ]
    return time_array

def voltage_array(data,event):
    voltage_array = [y[event+1] for y in data] 
    return voltage_array 

print("Starting conversion.")
## read the input files
inputFile1 = "{}/run_{}_Channel1_file{}.npy".format(RawDataPath,run,fileNum)  
inputFile2 = "{}/run_{}_Channel2_file{}.npy".format(RawDataPath,run,fileNum) 
inputFile3 = "{}/run_{}_Channel3_file{}.npy".format(RawDataPath,run,fileNum) 
inputFile4 = "{}/run_{}_Channel4_file{}.npy".format(RawDataPath,run,fileNum) 

arrayChannel1 = np.load(inputFile1) 
arrayChannel2 = np.load(inputFile2)
arrayChannel3 = np.load(inputFile3)
arrayChannel4 = np.load(inputFile4)

n_events = len(arrayChannel1[0]) - 1
n_points = len(arrayChannel1) 
print( "Number of events : {} ".format(n_events) )
print( "Number of points : {} ".format(n_points) )

time_array(arrayChannel1)

## prepare the output files
outputFile = '{}/run_scope{}_file{}.root'.format(OutputFilePath, run, fileNum)
outRoot    = TFile(outputFile, "RECREATE")
outTree    = TTree("pulse","pulse")

i_evt   = np.zeros(1,dtype=np.dtype("u4"))
channel = np.zeros([4,n_points],dtype=np.float32)
time    = np.zeros([1,n_points],dtype=np.float32)

outTree.Branch('i_evt'  ,i_evt    ,'i_evt/i')
outTree.Branch('channel', channel , 'channel[4]['+str(n_points)+']/F' )
outTree.Branch('time'   , time    , 'time[1]['+str(n_points)+']/F' )

## get voltage values for each event/segment (return array gives voltage and time values for each segment. number of entries in the time and voltage arrays are equal to nimber of points)
# times - in seconds
# voltages - in volts
times = time_array(arrayChannel1)
for evt in range(n_events):
    if debug and evt%10==0 : 
        print "Processing event %i" % evt 
    elif evt%1000==0:
        print "Processing event %i" % evt
    channel[0] = voltage_array(arrayChannel1,evt) # fast_Keysight_bin(inputFile1, i+1, n_points)[0][1]
    channel[1] = voltage_array(arrayChannel2,evt) # fast_Keysight_bin(inputFile2, i+1, n_points)[0][1]
    channel[2] = voltage_array(arrayChannel3,evt) # fast_Keysight_bin(inputFile3, i+1, n_points)[0][1]
    channel[3] = voltage_array(arrayChannel4,evt) # fast_Keysight_bin(inputFile4, i+1, n_points)[0][1]
    time[0] = times 
    i_evt[0] = evt

    outTree.Fill()

print("Done filling the tree!")
outRoot.cd()
outTree.Write()
outRoot.Close()
