from displayio import release_displays
release_displays()

import displayio
import busio
import board
import dotclockframebuffer
from framebufferio import FramebufferDisplay
import time
import math

tft_pins = dict(board.TFT_PINS)

tft_timings = {
    "frequency": 10000000,  # ~9MHz gives ~24-30Hz, within sync range
    "width": 720,
    "height": 720,
    "hsync_pulse_width": 4,
    "hsync_front_porch": 60,
    "hsync_back_porch": 60,
    "vsync_pulse_width": 4,
    "vsync_front_porch": 20,
    "vsync_back_porch": 20,
    "hsync_idle_low": True,
    "vsync_idle_low": True,
    "de_idle_high": False,
    "pclk_active_high": False,
    "pclk_idle_high": False,
}

init_sequence_tl040hds20 = bytes()

board.I2C().deinit()
i2c = busio.I2C(board.SCL, board.SDA)
tft_io_expander = dict(board.TFT_IO_EXPANDER)
dotclockframebuffer.ioexpander_send_init_sequence(i2c, init_sequence_tl040hds20, **tft_io_expander)
i2c.deinit()

bitmap = displayio.OnDiskBitmap("/Undercity_720.bmp")

fb = dotclockframebuffer.DotClockFramebuffer(**tft_pins, **tft_timings)
display = FramebufferDisplay(fb, auto_refresh=False)

tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

group = displayio.Group()
group.append(tile_grid)

# Create a 2-color palette: index 0 = transparent/black, index 1 = white
palette = displayio.Palette(2)
palette.make_transparent(0)  # index 0 is transparent now
palette[1] = 0xFFFFFF        # index 1 is white

dot_size = 5

# Create overlay bitmap for the dot (same size as screen, 2 colors)
dot_bitmap = displayio.Bitmap(tft_timings["width"], tft_timings["height"], 2)
dot_tilegrid = displayio.TileGrid(dot_bitmap, pixel_shader=palette)

group.append(dot_tilegrid)

display.root_group = group
display.auto_refresh = True

def generate_coords(t, width, height):
    x = int((width - dot_size) / 2 * (1 + math.sin(t * 0.5)))
    y = int((height - dot_size) / 2 * (1 + math.cos(t * 0.5)))
    return x, y

t = 0

prev_x, prev_y = None, None
dot_size = 5
start_time = time.monotonic()

while True:
    now = time.monotonic()
    t = now - start_time  # real elapsed time

    # Smooth circular path
    x = int((tft_timings['width'] - dot_size) / 2 * (1 + math.sin(t * 0.8)))
    y = int((tft_timings['height'] - dot_size) / 2 * (1 + math.cos(t * 0.8)))

    if (x != prev_x) or (y != prev_y):
        # Clear previous dot
        if prev_x is not None:
            for py in range(prev_y, prev_y + dot_size):
                for px in range(prev_x, prev_x + dot_size):
                    if 0 <= px < tft_timings['width'] and 0 <= py < tft_timings['height']:
                        dot_bitmap[px, py] = 0  # transparent

        # Draw new dot
        for py in range(y, y + dot_size):
            for px in range(x, x + dot_size):
                if 0 <= px < tft_timings['width'] and 0 <= py < tft_timings['height']:
                    dot_bitmap[px, py] = 1  # white

        display.refresh()

        prev_x, prev_y = x, y

    time.sleep(0.005)  # Small delay for smoother animation
