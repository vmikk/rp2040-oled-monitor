import time
import board
import busio
import displayio
import terminalio
import random
import math # Needed for polygon demo
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect # Using Rect for stars for performance
from adafruit_display_shapes.line import Line # Using Lines to draw polygon outline
import adafruit_displayio_ssd1306
from i2cdisplaybus import I2CDisplayBus

# --- Display Setup ---
displayio.release_displays()

# I2C is on GP1/GP0
i2c = busio.I2C(board.GP1, board.GP0) 

# Display parameters
WIDTH = 128
HEIGHT = 64
I2C_ADDRESS = 0x3C 

# Initialize display using the correct class
display_bus = I2CDisplayBus(i2c, device_address=I2C_ADDRESS)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

# --- Demo Switching Logic ---
DEMO_DURATION = 10 # seconds
current_demo = "starfield" # Start with starfield
last_switch_time = time.monotonic()

# --- Starfield Setup ---
NUM_STARS = 150 # Increased star count
MAX_DEPTH = 32.0
STAR_SPEED = 0.5 # Increased speed
stars = []
star_group = displayio.Group()

def init_starfield():
    global stars
    stars = []
    for _ in range(NUM_STARS):
        stars.append({
            'x': random.uniform(-0.5, 0.5) * WIDTH,
            'y': random.uniform(-0.5, 0.5) * HEIGHT,
            'z': random.uniform(1, MAX_DEPTH)
        })
    # Clear previous drawing elements except potentially a title
    while len(main_group) > 1: 
        main_group.pop()
    # Ensure star_group is added (might have been popped)
    if star_group not in main_group:
         main_group.append(star_group)
    # Clear old stars
    while len(star_group) > 0:
        star_group.pop()
    title.text = "Starfield" # Update title

def update_draw_starfield():
    while len(star_group) > 0:
        star_group.pop()

    for star in stars:
        star['z'] -= STAR_SPEED
        if star['z'] <= 0:
            star['x'] = random.uniform(-0.5, 0.5) * WIDTH
            star['y'] = random.uniform(-0.5, 0.5) * HEIGHT
            star['z'] = MAX_DEPTH

        if star['z'] > 0:
            k = 128.0 / star['z']
            x = int(star['x'] * k + WIDTH / 2)
            y = int(star['y'] * k + HEIGHT / 2)
            size = max(1, int((1.0 - (star['z'] / MAX_DEPTH)) * 3))
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                star_rect = Rect(x - size // 2, y - size // 2, size, size, fill=0xFFFFFF)
                star_group.append(star_rect)

# --- Polygon Demo Setup ---
NUM_SIDES = 5
BASE_RADIUS = 20
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2
AMPLITUDE = 8 # How much vertices move
FREQ = 2.0 # Speed of mutation
polygon_group = displayio.Group()

def init_polygon():
    global polygon_group
    print("-- Initializing Polygon Demo --")
    # Explicitly remove star_group if present
    if star_group in main_group:
        # print("Removing star_group from main_group")
        main_group.remove(star_group)
    # Clear any other potential stale groups (except title)
    while len(main_group) > 1: 
        main_group.pop()
    # Ensure polygon_group is added
    if polygon_group not in main_group:
        # print("Adding polygon_group to main_group")
        main_group.append(polygon_group)
    
    # Clear any previous lines/shapes from the group
    while len(polygon_group) > 0:
        polygon_group.pop()
    title.text = "Poly Morph" # Update title
    # print("Polygon Init complete.")

def update_draw_polygon():
    # print("-- Updating Polygon (using Lines) --") # Optional: uncomment for debugging
    
    # Clear previous lines
    while len(polygon_group) > 0:
        polygon_group.pop()

    # Calculate dynamic vertices
    vertices = []
    current_time = time.monotonic()
    angle_step = 2 * math.pi / NUM_SIDES

    for i in range(NUM_SIDES):
        base_angle = i * angle_step
        # Offset radius with sine wave, phase shifted per vertex
        offset = AMPLITUDE * math.sin(current_time * FREQ + i * (math.pi / NUM_SIDES * 1.5))
        mutated_radius = BASE_RADIUS + offset

        x = int(CENTER_X + mutated_radius * math.cos(base_angle))
        y = int(CENTER_Y + mutated_radius * math.sin(base_angle))
        vertices.append((x, y))
        
    # Draw the polygon outline using Line objects
    if len(vertices) >= 2:
        # print(f"Drawing polygon with lines using vertices: {vertices}") # Optional debug print
        try:
            for i in range(len(vertices)):
                p1 = vertices[i]
                p2 = vertices[(i + 1) % len(vertices)] # Wrap around to connect last to first
                polygon_group.append(Line(p1[0], p1[1], p2[0], p2[1], color=0xFFFFFF))
            # print("Lines added successfully.") # Optional debug print
        except Exception as e:
             print(f"ERROR drawing lines: {e}")

# --- Main Display Group ---
main_group = displayio.Group()
display.root_group = main_group

# Optional: Add a title label
title = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=5, y=5)
main_group.append(title)

# Initialize the first demo
init_starfield()

# --- Main Loop ---
while True:
    now = time.monotonic()

    # Check if it's time to switch demos
    if now - last_switch_time > DEMO_DURATION:
        if current_demo == "starfield":
            current_demo = "polygon"
            init_polygon()
        else:
            current_demo = "starfield"
            init_starfield()
        last_switch_time = now

    # Update and draw the current demo
    if current_demo == "starfield":
        update_draw_starfield()
    else:
        update_draw_polygon()

    # Display updates automatically
    time.sleep(0.01)

