import RPi.GPIO as GPIO
import time

# GPIO pins
DIR_PIN = 8     # Pin 8
STEP_PIN = 10   # Pin 10
LIMIT_SWITCH_PIN = 17  # Pin 17

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Set direction: True for one way, False for the other
direction = True
GPIO.output(DIR_PIN, direction)

# Step function
def step_motor(steps, delay=0.001):
    for _ in range(steps):
        if GPIO.input(LIMIT_SWITCH_PIN) == GPIO.HIGH:
            print("Limit switch activated. Stopping motor.")
            break
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)

# Run the motor
try:
    print("Motor running...")
    while True:
        step_motor(1)  # Continuous movement, step by step

except KeyboardInterrupt:
    print("Stopping program.")

finally:
    GPIO.cleanup()
