import cv2
import numpy as np
from PIL import Image
import json
import os

def frame_to_braille(frame, width=60, threshold=150):
    """Convert frame to braille ASCII with black background for transparent areas."""
    img = Image.fromarray(frame)
    
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (0, 0, 0))
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

def video_to_braille_frames(video_path, output_dir="frames", fps=10, width=60, max_duration=30):
    """Convert video to braille frames."""
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video {video_path}")
        return []
    
    video_fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_skip = max(1, video_fps // fps)
    frames_data = []
    
    print(f"Processing: {video_path}")
    print(f"Original: {video_fps} FPS, {total_frames} frames")
    print(f"Extracting at: {fps} FPS")
    
    frame_count = 0
    extracted_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if max_duration > 0 and frame_count / video_fps > max_duration:
            break
        
        if frame_count % frame_skip == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            braille_text = frame_to_braille(frame_rgb, width=width, threshold=150)
            
            frame_filename = f"frame_{extracted_count:04d}.txt"
            frame_path = os.path.join(output_dir, frame_filename)
            
            with open(frame_path, 'w', encoding='utf-8') as f:
                f.write(braille_text)
            
            frames_data.append({
                "name": frame_filename,
                "content": braille_text,
                "index": extracted_count
            })
            
            extracted_count += 1
        
        frame_count += 1
    
    cap.release()
    
    # Save JSON
    json_data = {
        "frames": frames_data,
        "info": {
            "video": os.path.basename(video_path),
            "original_fps": video_fps,
            "output_fps": fps,
            "width": width,
            "total_frames": extracted_count
        }
    }
    
    with open("frames.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Done! Extracted {extracted_count} frames to '{output_dir}/'")
    return extracted_count

if __name__ == "__main__":
    video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.gif', '.webm')
    video_files = [f for f in os.listdir() if f.lower().endswith(video_exts)]
    
    if not video_files:
        print("❌ No video file found!")
        print("Add a video file to the repo root.")
        exit(1)
    
    video_file = video_files[0]
    
    frame_count = video_to_braille_frames(
        video_path=video_file,
        output_dir="frames",
        fps=15,
        width=60,
        max_duration=30
    )
    
    print(f"🎉 Created {frame_count} frames")
