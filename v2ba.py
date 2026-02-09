import cv2
import numpy as np
from PIL import Image
import imageio
import os

def frame_to_braille(frame, width=60, threshold=150):
    """Convert frame to braille ASCII."""
    img = Image.fromarray(frame).convert('L')
    aspect = img.height / img.width
    height = int(width * aspect * 0.5)
    img = img.resize((width, height * 4), Image.Resampling.LANCZOS)
    pixels = np.array(img)
    pixels = 255 - pixels
    
    braille = []
    for y in range(0, height * 4, 4):
        row = []
        for x in range(0, width, 2):
            block = pixels[y:min(y+4, pixels.shape[0]), x:min(x+2, pixels.shape[1])]
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
            row.append(chr(0x2800 + bits))
        braille.append(''.join(row))
    return '\n'.join(braille)

def create_braille_gif(video_path, output_gif="braille_video.gif", fps=5, width=60):
    """Create GIF from video frames converted to braille."""
    cap = cv2.VideoCapture(video_path)
    video_fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_skip = max(1, video_fps // fps)
    
    frames = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            braille_text = frame_to_braille(frame, width=width)
            
            # Create image from text
            lines = braille_text.split('\n')
            char_width = 12
            char_height = 20
            img = Image.new('RGB', (width * char_width, len(lines) * char_height), color='black')
            
            # Draw text (you'd need a font file or use basic drawing)
            # For now, save as text frames
            frames.append(braille_text)
        
        frame_count += 1
        if frame_count > 30 * 10:  # Limit to 10 seconds
            break
    
    cap.release()
    
    # Save frames as individual files or create a text file
    os.makedirs("output", exist_ok=True)
    for i, frame_text in enumerate(frames):
        with open(f"output/frame_{i:04d}.txt", "w", encoding="utf-8") as f:
            f.write(frame_text)
    
    # Create a simple summary
    with open("braille_video_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Braille video frames: {len(frames)}\n")
        f.write(f"Original FPS: {video_fps}\n")
        f.write(f"Output FPS: {fps}\n")
        f.write(f"Width: {width} chars\n")
    
    return len(frames)

if __name__ == "__main__":
    # Look for video files
    video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.gif')
    video_files = [f for f in os.listdir() if f.lower().endswith(video_exts)]
    
    if not video_files:
        print("No video file found! Add a video to the repo root.")
        exit(1)
    
    video_file = video_files[0]
    print(f"Converting: {video_file}")
    
    frame_count = create_braille_gif(
        video_path=video_file,
        output_gif="braille_video.gif",
        fps=5,
        width=60
    )
    
    print(f"Created {frame_count} braille frames in output/ folder")
