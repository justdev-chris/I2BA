from PIL import Image
import numpy as np

def image_to_braille(image_path, width=100, threshold=128, invert=False):
    """
    Convert an image to braille ASCII art.
    Uses black background for transparent areas.
    """
    try:
        # Open image
        img = Image.open(image_path)
        
        # Handle transparency with BLACK background
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Create BLACK background
            background = Image.new('RGB', img.size, (0, 0, 0))  # Black
            
            if img.mode == 'P':
                img = img.convert('RGBA')
            elif img.mode == 'LA':
                img = img.convert('RGBA')
                
            background.paste(img, (0, 0), img)
            img = background.convert('L')
        else:
            img = img.convert('L')
        
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio * 0.5)
        
        img = img.resize((width, height * 4), Image.Resampling.LANCZOS)
        pixels = np.array(img)
        
        if invert:
            pixels = 255 - pixels
        
        braille_chars = []
        
        for y in range(0, height * 4, 4):
            row_chars = []
            for x in range(0, width, 2):
                block = pixels[y:min(y+4, pixels.shape[0]), 
                              x:min(x+2, pixels.shape[1])]
                
                bits = 0
                
                if block.shape[0] > 0 and block.shape[1] > 0:
                    if block[0, 0] < threshold: bits |= 0b00000001
                    if block.shape[0] > 1 and block[1, 0] < threshold: bits |= 0b00000010
                    if block.shape[0] > 2 and block[2, 0] < threshold: bits |= 0b00000100
                    if block.shape[1] > 1 and block[0, 1] < threshold: bits |= 0b00001000
                    if block.shape[0] > 1 and block.shape[1] > 1 and block[1, 1] < threshold: bits |= 0b00010000
                    if block.shape[0] > 2 and block.shape[1] > 1 and block[2, 1] < threshold: bits |= 0b00100000
                    if block.shape[0] > 3 and block[3, 0] < threshold: bits |= 0b01000000
                    if block.shape[0] > 3 and block.shape[1] > 1 and block[3, 1] < threshold: bits |= 0b10000000
                
                braille_chars.append(chr(0x2800 + bits))
            braille_chars.append('\n')
        
        return ''.join(braille_chars)
        
    except Exception as e:
        return f"Error: {str(e)}"

def save_braille_to_file(braille_text, filename="braille_output.txt"):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(braille_text)
    return filename

if __name__ == "__main__":
    braille_art = image_to_braille(
        image_path='bk.webp',  # Change this to your image
        width=80,
        threshold=150,
        invert=True  # Keep invert=True for dark text on black BG
    )
    
    print(braille_art)
    save_braille_to_file(braille_art, "braille_output.txt")
    print("\nSaved to braille_output.txt")
