from time import sleep
import pygame
import serial
import re
import sys

# === CONFIG ===
SERIAL_PORT = 'COM7'
BAUD_RATE    = 9600
WINDOW_SIZE  = 600
DOT_RADIUS   = 5
MAX_RANGE    = 10

# Button properties
BUTTON_WIDTH, BUTTON_HEIGHT = 180, 40
button_rect = pygame.Rect(WINDOW_SIZE - BUTTON_WIDTH - 10, 10, BUTTON_WIDTH, BUTTON_HEIGHT)
button_color_idle = (70, 70, 70)
button_color_hover = (100, 100, 100)
button_text_color = (255, 255, 255)


# dynamically compute zoom
ZOOM = (WINDOW_SIZE/2 - DOT_RADIUS) / MAX_RANGE

# === Initialize serial ===
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT}")
except serial.SerialException:
    print(f"Failed to connect to {SERIAL_PORT}")
    sys.exit(1)

# === Initialize pygame ===
pygame.init()
font = pygame.font.SysFont("monospace", 16)
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Position Tracker")
clock = pygame.time.Clock()

# === Main Loop ===
center    = (WINDOW_SIZE // 2, WINDOW_SIZE // 2)
position  = [0, 0]
last_line = ""

running = True
while running:
    screen.fill((30, 30, 30))

    # Read serial line

    try:
        line = ser.readline().decode('utf-8').strip()
        last_line = line
        parts = line.split(",")
        if len(parts) >= 2:
            x, y = map(float, parts[:2])
            position = [x, y]
    except Exception as e:
        print(f"Serial error: {e}")

    # Convert to pixel coordinates
    px = int(center[0] + position[0] * ZOOM)
    py = int(center[1] - position[1] * ZOOM)
    print(f"Position: {position[0]:.2f}, {position[1]:.2f}")

    # Clamp to window
    px = max(DOT_RADIUS, min(WINDOW_SIZE - DOT_RADIUS, px))
    py = max(DOT_RADIUS, min(WINDOW_SIZE - DOT_RADIUS, py))

    # Draw
    pygame.draw.circle(screen, (0, 255, 0), (px, py), DOT_RADIUS)
    pygame.draw.line(screen, (100, 100, 100), (center[0], 0), (center[0], WINDOW_SIZE))
    pygame.draw.line(screen, (100, 100, 100), (0, center[1]), (WINDOW_SIZE, center[1]))
    text_surface = font.render(last_line, True, (200, 200, 200))
    screen.blit(text_surface, (10, WINDOW_SIZE - 25))

    # Detect mouse position
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]

    # Change button color on hover
    if button_rect.collidepoint(mouse_pos):
        color = button_color_hover
        if mouse_clicked:
            try:
                # ser.write(b'\x04')  # Send Ctrl+D to reset
                ser.write(b'\x03')  # Ctrl-C to interrupt running code
                sleep(0.1)    # short delay
                ser.write(b'\x04')  # Ctrl-D to soft reset
                # ser.write(b'\x04\n')
                # ser.flush()
                # ser.setDTR(False)
                # sleep(0.1)  # Wait for reset
                # ser.setDTR(True)
                print("Sent Ctrl+D to CircuitPython (soft reload).")
            except Exception as e:
                print(f"Failed to send reset: {e}")
    else:
        color = button_color_idle

    # Draw the button rectangle
    pygame.draw.rect(screen, color, button_rect)

    # Draw the button text
    button_font = pygame.font.SysFont("monospace", 20, bold=True)
    button_label = button_font.render("Reset Board", True, button_text_color)
    label_rect = button_label.get_rect(center=button_rect.center)
    screen.blit(button_label, label_rect)


    pygame.display.flip()
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
ser.close()
