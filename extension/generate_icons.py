import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    import subprocess
    print("Pillow not found. Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw

def generate():
    # Create icons directory if it doesn't exist
    os.makedirs("icons", exist_ok=True)

    # Generate a beautiful 128x128 retro pixel icon
    size = 128
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Neo-brutalist style icon:
    # Solid black border box
    draw.rectangle([4, 4, 124, 124], fill=(0, 0, 0, 255))
    # Inner solid box
    draw.rectangle([12, 12, 116, 116], fill=(255, 255, 255, 255))

    # Draw an inner retro shadow / accent block
    draw.rectangle([20, 20, 108, 108], fill=(240, 240, 240, 255))

    # Draw standard bold ">_" symbol manually in pixels
    # '>' symbol
    draw.rectangle([32, 40, 48, 48], fill=(0, 0, 0, 255))
    draw.rectangle([48, 48, 64, 56], fill=(0, 0, 0, 255))
    draw.rectangle([64, 56, 80, 64], fill=(0, 0, 0, 255))
    draw.rectangle([48, 64, 64, 72], fill=(0, 0, 0, 255))
    draw.rectangle([32, 72, 48, 80], fill=(0, 0, 0, 255))
    
    # '_' symbol
    draw.rectangle([48, 88, 88, 96], fill=(0, 0, 0, 255))

    # Save 128x128
    img.save("icons/icon128.png")

    # Resize for 48x48
    img48 = img.resize((48, 48), Image.Resampling.LANCZOS)
    img48.save("icons/icon48.png")

    # Resize for 16x16
    img16 = img.resize((16, 16), Image.Resampling.LANCZOS)
    img16.save("icons/icon16.png")

    print("Status Tracker: Retro pixel-art icons generated in extension/icons/ successfully!")

if __name__ == "__main__":
    generate()
