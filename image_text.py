from PIL import Image, ImageDraw, ImageFont
import sys

try:
    logo = Image.open("./Image_templates/RLPC_Logo.png")

except IOError:
    print("Unable to load image")
    sys.exit(1)
    
idraw = ImageDraw.Draw(logo)
text = "text"

font = ImageFont.truetype("arial.ttf", size=100)

idraw.text((10, 10), text, font=font)
 
logo.show()