# Run sample.py in the background
python c:/Users/remba/UCSD/MAE_Capstone_Project/RPHD_code/sensor_readers/sample.py -t 100 COM6 &
SAMPLE_NDI=$!

# Run serial_reader.py in the background
python c:/Users/remba/UCSD/MAE_Capstone_Project/RPHD_code/sensor_readers/serial_reader.py "$@" &
SAMPLE_ATI=$!

# Wait for both processes to finish
wait $SAMPLE_NDI $SAMPLE_ATI