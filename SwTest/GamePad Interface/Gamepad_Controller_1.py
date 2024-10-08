import pygame
import sys

# Initialize Pygame
pygame.init()

# Initialize the joystick module
pygame.joystick.init()

# Check if any joysticks are connected
if pygame.joystick.get_count() == 0:
    print("No joystick found!")
    pygame.quit()
    sys.exit()

# Get the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Function to print joystick state
def print_joystick_state():
    print("Joystick name:", joystick.get_name())
    print("Number of buttons:", joystick.get_numbuttons())
    print("Number of axes:", joystick.get_numaxes())


# Vars
speedFactor = 0
maxSpeedFactor = 20
reverseSpeedFactor = -20
defaultSpeed = 100
M1 = 0
M2 = 0
M3 = 0
M4 = 0


# Main loop
try:
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Print button state
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"Button {event.button} pressed")
                if event.button == 1:
                    print(f"Shutting Down: Button {event.button} Pressed!")
                    pygame.quit()
                    sys.exit()
                if event.button == 7:
                    speedFactor = maxSpeedFactor
                    print(f"Speed Factor: {speedFactor}")
                elif event.button == 6:
                    speedFactor = reverseSpeedFactor
                    print(f"Speed Factor: {speedFactor}")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"Button {event.button} released")
                if event.button == 7 or event.button == 6:
                    speedFactor = 0
                    print(f"Speed Factor: {speedFactor}")

        # Read analog axes values
        axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
        print("Axes values:", axes)

        # Limit output frequency

        M1 = defaultSpeed + round(axes[0], 3) * speedFactor
        M2 = defaultSpeed - round(axes[0], 3) * speedFactor
        M3 = defaultSpeed + round(axes[0], 3) * speedFactor
        M4 = defaultSpeed - round(axes[0], 3) * speedFactor

        #print(axes[0] * speedFactor)

        if speedFactor == 0:
            M1 = 0
            M2 = 0
            M3 = 0
            M4 = 0
        elif speedFactor < 0:
            M1 = -M1
            M2 = -M2
            M3 = -M3
            M4 = -M4

        print("----------")
        print(f"M1: {M1}, M2: {M2}")
        print(f"M3: {M3}, M4: {M4}")

        pygame.time.delay(10)

except KeyboardInterrupt:
    pygame.quit()
    sys.exit()
