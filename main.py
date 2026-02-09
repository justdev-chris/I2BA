from PIL import Image
import numpy as np

def image_to_braille(image_path, width=100, threshold=128, invert=False):
    """
    Convert an image to braille ASCII art.
    
    Args:
        image_path: Path to the image file
        width: Output width in characters (height is auto-calculated)
        threshold: Brightness threshold (0-255)
        invert: True for dark text on light background
    
    Returns:
        String containing braille ASCII art
    """
    try:
        # Open and convert to grayscale
        img = Image.open(image_path).convert('L')
        
        # Calculate height to maintain aspect ratio
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.5)  # *0.5 because braille is 2:1 aspect
        
        # Resize image
        img = img.resize((width, height * 4), Image.Resampling.LANCZOS)
        pixels = np.array(img)
        
        if invert:
            pixels = 255 - pixels
        
        # Braille Unicode starts at 0x2800
        # Each braille character represents 2x4 dots
        braille_chars = []
        
        for y in range(0, height * 4, 4):
            row_chars = []
            for x in range(0, width, 2):
                # Get 2x4 block of pixels
                block = pixels[y:min(y+4, pixels.shape[0]), 
                              x:min(x+2, pixels.shape[1])]
                
                # Create braille bits
                # Braille dot numbering:
                # 1 4
                # 2 5
                # 3 6
                # 7 8
                bits = 0
                
                if block.shape[0] > 0 and block.shape[1] > 0:
                    # Dot 1 (top-left)
                    if block[0, 0] < threshold:
                        bits |= 0b00000001
                    # Dot 2 (middle-left)
                    if block.shape[0] > 1 and block[0, 1] < threshold:
                        bits |= 0b00000010
                    # Dot 3 (bottom-left)
                    if block.shape[0] > 2 and block[0, 2] < threshold:
                        bits |= 0b00000100
                    # Dot 4 (top-right)
                    if block.shape[1] > 1 and block[1, 0] < threshold:
                        bits |= 0b00001000
                    # Dot 5 (middle-right)
                    if block.shape[0] > 1 and block.shape[1] > 1 and block[1, 1] < threshold:
                        bits |= 0b00010000
                    # Dot 6 (bottom-right)
                    if block.shape[0] > 2 and block.shape[1] > 1 and block[1, 2] < threshold:
                        bits |= 0b00100000
                    # Dot 7 (very bottom-left)
                    if block.shape[0] > 3 and block[2, 0] < threshold:
                        bits |= 0b01000000
                    # Dot 8 (very bottom-right)
                    if block.shape[0] > 3 and block.shape[1] > 1 and block[2, 1] < threshold:
                        bits |= 0b10000000
                
                # Convert to braille character
                braille_chars.append(chr(0x2800 + bits))
            braille_chars.append('\n')
        
        return ''.join(braille_chars)
        
    except Exception as e:
        return f"Error: {str(e)}"

def save_braille_to_file(braille_text, filename="braille_art.txt"):
    """Save braille art to a text file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(braille_text)
    return filename

# Example usage
if __name__ == "__main__":
    # Convert an image (replace 'your_image.jpg' with your image path)
    braille_art = image_to_braille(
        image_path='bk.png',
        width=80,
        threshold=150,
        invert=True
    )
    
    print(braille_art)
    
    # Save to file
    save_braille_to_file(braille_art, "braille_output.txt")
    print("\nSaved to braille_output.txt")
