#python acquisition.py --numEvents 1000 --numPoints 8000 --trigCh 2 --trig -0.05
#python acquisition.py --numEvents 1000 --trigCh 1 --trig +0.5 --trigSlope "POSitive" --timeoffset 0 
python InfiniiVision_Complex.py  --numEvents 10 --trigCh 1 --trig -0.020 --trigSlope "NEGative" --timeoffset 0 
#python InfiniiVision_SegmentedMemory_Waveform_and_Measurement_Grabber.py  --numEvents 100 --trigCh 1 --trig -0.020 --trigSlope "NEGative" --timeoffset 0 

# Proper
#python acquisition.py --numEvents 1000 --sampleRate 6 --horizontalWindow --125 --trigCh 1 --trig -0.05
 

