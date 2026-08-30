from PIL import Image, ImageDraw, ImageFont
import os

# Sample manga page creation
width, height = 800, 1200
img = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(img)

# Draw some speech bubbles
bubbles = [
    (50, 50, 350, 150),
    (400, 100, 750, 200),
    (100, 300, 400, 400),
    (450, 350, 750, 450),
    (200, 600, 600, 700),
]

for i, (x1, y1, x2, y2) in enumerate(bubbles):
    # Draw bubble
    draw.ellipse([x1, y1, x2, y2], fill='white', outline='black', width=2)
    
    # Add some text simulation (lines)
    text_y = y1 + 30
    num_lines = 3 if i < 3 else 2
    for j in range(num_lines):
        line_len = 150 - (j * 20)
        draw.rectangle([x1 + 30, text_y + j*25, x1 + 30 + line_len, text_y + j*25 + 20], fill='black')

# Save test image
img.save('/workspace/test_images/sample_manga.png')
print("✓ Test görseli oluşturuldu: sample_manga.png")
