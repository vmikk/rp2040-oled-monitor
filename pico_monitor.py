import time
import board
import busio
import displayio
from adafruit_display_text import label
import terminalio
import adafruit_displayio_ssd1306
from i2cdisplaybus import I2CDisplayBus
import digitalio  # For GPIO control
import neopixel   # For the onboard WS2812 LED
import usb_cdc    # For receiving data from host

# Global variables for status
IP = "192.168.252.252"
UPTIME = "008.1d"
JOBCOUNT = "3280"
DOCKER_RUNNING = False
EUTAX_HEALTHY = False

# Initialize the WS2812 LED on GP16
try:
    pixel = neopixel.NeoPixel(board.GP16, 1, brightness=0.1)
    pixel[0] = (0, 0, 0)  # Initially off
except Exception as e:
    # If LED control fails, don't let it prevent the main code from running
    print(f"LED control failed: {e}")

# --- Display Setup ---
displayio.release_displays()

# I2C is on GP1/GP0
i2c = busio.I2C(board.GP1, board.GP0)

# Display parameters
WIDTH = 128
HEIGHT = 64
I2C_ADDRESS = 0x3C

# Initialize display using the custom display bus
display_bus = I2CDisplayBus(i2c, device_address=I2C_ADDRESS)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

# Create a main display group
main_group = displayio.Group()
display.root_group = main_group

# Clear display
display.fill(0)
display.show()

# Function to update LED based on health status
def update_health_status():
    # Turn on red LED if both Docker is not running and Eutax is not healthy
    if not DOCKER_RUNNING and not EUTAX_HEALTHY:
        pixel[0] = (255, 0, 0)  # Red
    else:
        pixel[0] = (0, 0, 0)  # Off

## Docker icon 40x40
icon_docker = bytearray((
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0x00,
    0x1E, 0x00, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x7B, 0xDE, 0x00, 0x00, 0x00, 0x7B, 0xDE, 0x00, 0x00, 0x00, 0x7B, 0xDE, 0x00,
    0x00, 0x00, 0x7B, 0xDE, 0x03, 0x00, 0x00, 0x00, 0x00, 0x03, 0x80, 0x0F, 0x7B, 0xDE, 0xF7, 0xC0,
    0x0F, 0x7B, 0xDE, 0xF7, 0xC0, 0x0F, 0x7B, 0xDE, 0xF7, 0xFE, 0x0F, 0x7B, 0xDE, 0xF3, 0xFE, 0x00,
    0x00, 0x00, 0x03, 0xFC, 0x7F, 0xFF, 0xFF, 0xFF, 0xF8, 0x7F, 0xFF, 0xFF, 0xFF, 0xC0, 0x7F, 0xFF,
    0xFF, 0xFF, 0x80, 0x7F, 0xFF, 0xFF, 0xFF, 0x00, 0x3F, 0xFF, 0xFF, 0xFF, 0x00, 0x3F, 0xFF, 0xFF,
    0xFE, 0x00, 0x3F, 0xFF, 0xFF, 0xFC, 0x00, 0x1F, 0xFF, 0xFF, 0xF8, 0x00, 0x1F, 0xFF, 0xFF, 0xF0,
    0x00, 0x0F, 0xFF, 0xFF, 0xE0, 0x00, 0x07, 0xFF, 0xFF, 0xC0, 0x00, 0x03, 0xFF, 0xFF, 0x00, 0x00,
    0x00, 0xFF, 0xF8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
))

# Create bitmap for the Docker icon
def create_icon_bitmap(icon_data, width, height):
    bitmap = displayio.Bitmap(width, height, 1)
    for y in range(height):
        for x in range(width):
            byte_offset = (y * ((width + 7) // 8)) + (x // 8)
            bit_position = x % 8  # LSB first (little-endian)
            if byte_offset < len(icon_data):
                if (icon_data[byte_offset] & (1 << bit_position)) > 0:
                    bitmap[x, y] = 1
    return bitmap

# Create palettes for monochrome display
palette = displayio.Palette(2)
palette[0] = 0x000000  # Black
palette[1] = 0xFFFFFF  # White

# Create the Docker icon TileGrid
ICON_WIDTH = 40
ICON_HEIGHT = 40
docker_bitmap = displayio.Bitmap(ICON_WIDTH, ICON_HEIGHT, 1)

# Load the bitmap data
for y in range(ICON_HEIGHT):
    for x in range(ICON_WIDTH):
        byte_index = y * (ICON_WIDTH // 8) + (x // 8)
        bit_position = 7 - (x % 8)  # Horizontal byte orientation, MSB first
        
        if byte_index < len(icon_docker):
            docker_bitmap[x, y] = 1 if (icon_docker[byte_index] & (1 << bit_position)) else 0

docker_tile = displayio.TileGrid(docker_bitmap, pixel_shader=palette)

# Common font
font = terminalio.FONT

def clear_display():
    while len(main_group) > 0:
        main_group.pop()

def setup_layout():
    # Clear the display first
    clear_display()
    
    # Only show Docker icon if Docker is running AND Eutax is healthy
    if DOCKER_RUNNING and EUTAX_HEALTHY:
        docker_tile_copy = displayio.TileGrid(docker_bitmap, pixel_shader=palette)
        docker_tile_copy.x = 5
        docker_tile_copy.y = HEIGHT - ICON_HEIGHT  # Align with bottom of display
        main_group.append(docker_tile_copy)
    
    # IP address aligned to left side
    ip_label = label.Label(font, text=IP, color=0xFFFFFF, x=5, y=15)
    
    # Job count aligned to right side
    job_label = label.Label(font, text=JOBCOUNT, color=0xFFFFFF, x=60, y=36, scale=3)
    
    # Uptime aligned to right side
    uptime_label = label.Label(font, text=UPTIME, color=0xFFFFFF, x=90, y=58)
    
    # Add all elements to main group
    main_group.append(ip_label)
    main_group.append(job_label)
    main_group.append(uptime_label)

def update_display():
    setup_layout()
    display.refresh()
    update_health_status()  # Update LED status

# Initialize the display
update_display()

# Function to update display data
def update_data(ip=None, uptime=None, jobcount=None, docker_running=None, eutax_healthy=None):
    global IP, UPTIME, JOBCOUNT, DOCKER_RUNNING, EUTAX_HEALTHY
    
    if ip is not None:
        IP = ip
    if uptime is not None:
        UPTIME = uptime
    if jobcount is not None:
        JOBCOUNT = str(jobcount)
    if docker_running is not None:
        DOCKER_RUNNING = docker_running
    if eutax_healthy is not None:
        EUTAX_HEALTHY = eutax_healthy
        
    update_display()

## Function to parse pipe-delimited messages from host
def parse_message(data):
    """
    Parse a pipe-delimited message in format "key1:value1|key2:value2|key3:value3"
    """
    result = {}
    pairs = data.strip().split("|")
    for pair in pairs:
        if ":" in pair:
            key, value = pair.split(":", 1)
            # Handle boolean values as strings
            if value == "true":
                value = True
            elif value == "false":
                value = False
            # Convert numeric strings to appropriate types
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '', 1).isdigit():
                value = float(value)
            result[key] = value
    return result

# --- Prepare serial ----------------------
# usb_cdc.console is REPL; usb_cdc.data is the data channel
data_port = usb_cdc.data
buffer = b""

# Main loop to receive and process data
def main():
    global buffer
    
    while True:
        # read any available bytes
        chunk = data_port.read(32)
        if chunk:
            buffer += chunk
            if b"\n" in buffer:
                line, _, buffer = buffer.partition(b"\n")
                try:
                    # Parse the pipe-delimited message
                    m = parse_message(line.decode("ascii"))
                    
                    # Format uptime, add suffix "d"
                    uptime_str = f"{m.get('uptime', 0.0):.1f}d"
                    
                    # Update display with received metrics
                    update_data(
                        ip=m.get('ip', IP),
                        uptime=uptime_str,
                        jobcount=m.get('eutax_jobs', 0),
                        docker_running=m.get('docker', False),
                        eutax_healthy=m.get('eutax', False)
                    )
                    
                except Exception as e:
                    print(f"Error parsing metrics: {e}")
        
        time.sleep(25)

# Initialize display and start the main loop
if __name__ == "__main__":
    main()

