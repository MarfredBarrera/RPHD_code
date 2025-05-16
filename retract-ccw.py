# (4)  RETRACTION PHASE OF REPLICATION
# COMPONENT: LINEAR RAIL (X)
import RPi.GPIO as GPIO
from time import sleep

# Direction pin from controller
DIR = 10
# Step pin from controller
STEP = 8

# Setup pin layout on PI
GPIO.setmode(GPIO.BOARD)


# Establish Pins in software
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Set the direction you want it to spin
GPIO.output(DIR, CCW) 

try:
	# Run for n steps. This will change based on how you set you controller
	for x in range(500):
		# Set one coil winding to high
		GPIO.output(STEP,GPIO.HIGH)
		# Allow it to get there.
		sleep(.0015) # Dictates how fast stepper motor will run
		# Set coil winding to low
		GPIO.output(STEP,GPIO.LOW)
		sleep(.0015) # Dictates how fast stepper motor will run

# Once finished clean everything up
except KeyboardInterrupt:
	print("cleanup")
	GPIO.cleanup()
