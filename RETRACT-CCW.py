# COMPONENT: LINEAR RAIL (X) - RETRACTION
import RPi.GPIO as GPIO
from time import sleep
import sys

# --- GPIO Pins ---
DIR = 10
STEP = 8
lim1 = 37  # Limit switch 1 (forward)
lim2 = 31  # Limit switch 2 (rear)

CW = 0
CCW = 1

# --- GPIO Setup ---
GPIO.setmode(GPIO.BOARD)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(lim1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(lim2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# --- Set direction to retract ---
GPIO.output(DIR, CCW)

# --- Read distance from system argument ---
if len(sys.argv) != 2:
    print("Usage: python retract.py <distance_mm>")
    GPIO.cleanup()
    sys.exit(1)

try:
    distance = int(sys.argv[1])
except ValueError:
    print("Distance must be an integer.")
    GPIO.cleanup()
    sys.exit(1)

# --- Step calculation ---
steps_per_mm = 200 / 5
n = round(distance * steps_per_mm)

print("Retraction in progress...")

try:
    for x in range(n):
        if GPIO.input(lim1) == GPIO.HIGH or GPIO.input(lim2) == GPIO.HIGH:
            print("Limit switch activated. Stopping...")
            break
        GPIO.output(STEP, GPIO.HIGH)
        sleep(0.001325)
        GPIO.output(STEP, GPIO.LOW)
        sleep(0.001325)

except KeyboardInterrupt:
    print("Interrupted. Cleaning up...")
finally:
    GPIO.cleanup()
