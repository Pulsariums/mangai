from PIL import Image, ImageDraw
import os

# Sample manga page creation with REAL text-like patterns
width, height = 800, 1200
img = Image.new('RGB', (width, height), color=(255, 255, 240))  # Off-white paper
draw = ImageDraw.Draw(img)

# Draw speech bubbles with text-like lines
bubbles = [
    # Bubble 1 - top left
    {"bbox": (50, 50, 350, 150), "lines": 3, "angle": 0},
    # Bubble 2 - top right  
    {"bbox": (400, 80, 750, 180), "lines": 2, "angle": -5},
    # Bubble 3 - middle left
    {"bbox": (80, 250, 380, 380), "lines": 4, "angle": 3},
    # Bubble 4 - middle right
    {"bbox": (420, 280, 720, 400), "lines": 3, "angle": -2},
    # Bubble 5 - bottom center
    {"bbox": (200, 500, 600, 620), "lines": 3, "angle": 1},
    # Bubble 6 - lower
    {"bbox": (100, 700, 400, 800), "lines": 2, "angle": 0},
    # Bubble 7 - lower right
    {"bbox": (450, 720, 750, 820), "lines": 3, "angle": -3},
]

for i, bubble in enumerate(bubbles):
    x1, y1, x2, y2 = bubble["bbox"]
    num_lines = bubble["lines"]
    angle = bubble["angle"]
    
    # Draw bubble (ellipse)
    draw.ellipse([x1, y1, x2, y2], fill='white', outline='black', width=2)
    
    # Add text-like horizontal lines (simulating text blocks)
    margin = 30
    available_height = y2 - y1 - margin * 2
    line_spacing = available_height / num_lines
    
    for j in range(num_lines):
        line_y = y1 + margin + int(j * line_spacing) + 10
        
        # Vary line lengths to look like real text
        base_width = x2 - x1 - margin * 2
        line_len = int(base_width * (0.9 - j * 0.1))
        
        # Draw multiple word-like segments
        seg_count = 3 + (j % 3)
        seg_width = line_len // seg_count
        gap = 10
        
        for seg in range(seg_count):
            seg_x = x1 + margin + seg * (seg_width + gap)
            seg_h = 18 + (j % 3) * 2
            draw.rectangle(
                [seg_x, line_y, seg_x + seg_width - gap, line_y + seg_h],
                fill='black'
            )

# Add some Japanese/Korean-like complex patterns (dense text areas)
for area in [(50, 850, 350, 1000), (400, 870, 750, 1020)]:
    ax1, ay1, ax2, ay2 = area
    draw.rectangle([ax1, ay1, ax2, ay2], fill='white', outline='black', width=1)
    
    # Dense text simulation
    for row in range(6):
        for col in range(15):
            char_w = 15
            char_h = 18
            cx = ax1 + 10 + col * (char_w + 5)
            cy = ay1 + 10 + row * (char_h + 4)
            
            # Random-looking character blocks
            if (row + col) % 3 == 0:
                draw.rectangle([cx, cy, cx + char_w - 3, cy + char_h], fill='black')
            else:
                draw.rectangle([cx + 2, cy + 3, cx + char_w - 5, cy + char_h - 4], fill='black')

# Save test image
img.save('/workspace/test_images/sample_manga_text.png')
print("✓ Geliştirilmiş test görseli oluşturuldu: sample_manga_text.png")
print(f"   Boyut: {width}x{height}, 7 yazı balonu + 2 yoğun metin alanı")
