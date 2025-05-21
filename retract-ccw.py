# (4)  RETRACTION PHASE OF REPLICATION
# COMPONENT: LINEAR RAIL (X)
import RPi.GPIO as GPIO
from time import sleep

# Direction pin from controller
DIR = 10
# Step pin from controller
STEP = 8
# Limit switch GPIO Pin
LIMIT_SWITCH_PIN = 37  # Pin 37
# lim2 = 31 # Pin 31 - GPIO 6

# 0/1 used to signify clockwise or counterclockwise.
CW = 0
CCW = 1

# Setup pin layout on PI
GPIO.setmode(GPIO.BOARD)


# Establish Pins in software
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
# GPIO.setup(lim2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# Set the direction you want it to spin
GPIO.output(DIR, CCW) 

# Ask for user input for distance to travel
distance = int(input("Please enter the distance to travel in mm (retraction): "))
# Convert distance value x into # steps (full step, no microstepping)
# Step Angle = 1.8deg --> 200 steps/rev | lead srew mitch = 5mm --> 5mm/rev
n = distance * (200/5) # distance_mm * steps/mm
n = round(n) # range function only accepts integers
print("Insertion in progress...")

try:
	# Run for n steps.
	for x in range(n):
		# Limit switch activated = stops linear rail.
		if GPIO.input(LIMIT_SWITCH_PIN) == GPIO.HIGH:
			print("Limit switch activated. Stopping...")
			break
		#if GPIO.input(lim2 == GPIO.HIGH:
			#print("Limit switch activated. Stopping...")
			#break
		# Set one coil winding to high
		GPIO.output(STEP,GPIO.HIGH)
		# Allow it to get there.
		sleep(.001325) # Dictates how fast stepper motor will run
		# Set coil winding to low
		GPIO.output(STEP,GPIO.LOW)
		sleep(.001325) # Dictates how fast stepper motor will run

# Once finished clean everything up
except KeyboardInterrupt:
	print("cleanup")
	GPIO.cleanup()
