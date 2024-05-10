import digitalio
import board
import adafruit_st7789 as st7789
from PIL import Image, ImageDraw, ImageFont

# Configuration for CS, DC, and Reset pins
cs_pin = digitalio.DigitalInOut(board.CE0)  # Chip select
dc_pin = digitalio.DigitalInOut(board.D25)  # Data/command
rst_pin = digitalio.DigitalInOut(board.D27)  # Reset

# SPI setup
spi = board.SPI()

# ST7789 display initialization
display = st7789.ST7789(
    spi, rotation=0,  # Change rotation if needed
    width=240, height=280,  # Adjust to your screen's dimensions
    cs=cs_pin, dc=dc_pin, rst=rst_pin,
    baudrate=24000000  # May need adjustment for your particular display
)

# Clear the display to black
display.fill(0)

# Create a blank image for drawing
# Make sure to create an image with mode 'RGB' for full color
if display.rotation % 180 == 90:
    height = display.width  # we swap height/width to rotate it to landscape!
    width = display.height
else:
    width = display.width  # we swap height/width to rotate it to landscape!
    height = display.height
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

# Load a TTF font
font = ImageFont.load_default()

# Define the position of the text
text = "Hello, World!"
(font_width, font_height) = draw.textsize(text, font=font)
draw.text(
    (width // 2 - font_width // 2, height // 2 - font_height // 2),
    text, font=font, fill=(255, 255, 255)
)

# Display the image
display.image(image)
