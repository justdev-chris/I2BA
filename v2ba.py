import cv2
import numpy as np
from PIL import Image
import os

def frame_to_braille(frame, width=60):
    """Convert frame to braille ASCII text."""
    img = Image.fromarray(frame)
    
    # Handle transparency - treat as WHITE
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        elif img.mode == 'LA':
            img = img.convert('RGBA')
        background.paste(img, (0, 0), img)
        img = background.convert('L')
    else:
        img = img.convert('L')
    
    aspect = img.height / img.width
    height = int(width * aspect * 0.5)
    img = img.resize((width, height * 4), Image.Resampling.LANCZOS)
    pixels = np.array(img)
    
    braille_text = ""
    for y in range(0, height * 4, 4):
        row = ""
        for x in range(0, width, 2):
            block = pixels[y:min(y+4, pixels.shape[0]), x:min(x+2, pixels.shape[1])]
            bits = 0
            if block.shape[0] > 0 and block.shape[1] > 0:
                # WHITE (255) = NO DOT, anything else = DOT
                if block[0, 0] < 254: bits |= 0b00000001
                if block.shape[0] > 1 and block[1, 0] < 254: bits |= 0b00000010
                if block.shape[0] > 2 and block[2, 0] < 254: bits |= 0b00000100
                if block.shape[1] > 1 and block[0, 1] < 254: bits |= 0b00001000
                if block.shape[0] > 1 and block.shape[1] > 1 and block[1, 1] < 254: bits |= 0b00010000
                if block.shape[0] > 2 and block.shape[1] > 1 and block[2, 1] < 254: bits |= 0b00100000
                if block.shape[0] > 3 and block[3, 0] < 254: bits |= 0b01000000
                if block.shape[0] > 3 and block.shape[1] > 1 and block[3, 1] < 254: bits |= 0b10000000
            row += chr(0x2800 + bits)
        braille_text += row + "\n"
    
    return braille_text.strip()

def video_to_frames(video_path, output_dir="frames", fps=10, width=60, max_duration=15):
    """Convert video to braille frames."""
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Cannot open video: {video_path}")
        return
    
    video_fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_skip = max(1, video_fps // fps)
    
    frame_count = 0
    extracted_count = 0
    
    print(f"Processing: {video_path}")
    print(f"Original FPS: {video_fps}")
    print(f"Extracting at: {fps} FPS, Width: {width} chars")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if max_duration > 0 and frame_count / video_fps > max_duration:
            break
        
        if frame_count % frame_skip == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            braille_text = frame_to_braille(frame_rgb, width=width)
            
            frame_filename = f"frame_{extracted_count:04d}.txt"
            frame_path = os.path.join(output_dir, frame_filename)
            with open(frame_path, 'w', encoding='utf-8') as f:
                f.write(braille_text)
            
            extracted_count += 1
        
        frame_count += 1
    
    cap.release()
    print(f"✅ Created {extracted_count} frames in '{output_dir}/'")
    return extracted_count

if __name__ == "__main__":
    video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.gif', '.webm')
    video_files = [f for f in os.listdir() if f.lower().endswith(video_exts)]
    
    if not video_files:
        print("❌ No video file found!")
        exit(1)
    
    video_file = video_files[0]
    
    frame_count = video_to_frames(
        video_path=video_file,
        output_dir="frames",
        fps=10,
        width=60,
        max_duration=15
    )