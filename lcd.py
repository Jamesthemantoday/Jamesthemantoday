from PIL import Image, ImageDraw, ImageFont
import digitalio
import board
import adafruit_rgb_display.st7789 as st7789  # This is an example library

# Configuration for CS, DC, and RESET pins:
cs_pin = digitalio.DigitalInOut(board.CE0)  # Chip select
dc_pin = digitalio.DigitalInOut(board.D25)  # Data/command
reset_pin = digitalio.DigitalInOut(board.D24)  # Reset

# SPI setup
spi = board.SPI()

# ST7789 display initialization
display = st7789.ST7789(
    spi,
    height=280,
    width=240,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=40000000  # SPI communication frequency
)

# Clear display
display.fill(0)

# Create an image with text to display
image = Image.new('RGB', (240, 280))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
draw.text((10, 10), 'Hello Raspberry Pi', font=font, fill=(255, 255, 255))

# Display the image
display.image(image)
