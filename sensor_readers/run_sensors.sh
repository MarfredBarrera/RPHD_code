# Run sample.py in the background
python c:/Users/remba/UCSD/MAE_Capstone_Project/RPHD_code/sensor_readers/sampleNDI.py -t 100 COM6 &
SAMPLE_NDI=$!

# Run serial_reader.py in the background
python c:/Users/remba/UCSD/MAE_Capstone_Project/RPHD_code/sensor_readers/sampleATI.py "$@" &
SAMPLE_ATI=$!

# Wait for both processes to finish
wait $SAMPLE_NDI $SAMPLE_ATI