import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
import os
import json

def frame_to_braille(frame, width=60, threshold=150):
    """Convert frame to braille ASCII text."""
    img = Image.fromarray(frame)
    
    # Handle transparency with WHITE background
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        background = Image.new('RGB', img.size, (255, 255, 255))  # WHITE background
        if img.mode == 'P':
            img = img.convert('RGBA')
        elif img.mode == 'LA':
            img = img.convert('RGBA')
        background.paste(img, (0, 0), img)
        img = background.convert('L')
    else:
        img = img.convert('L')
    
    # Create braille text
    aspect = img.height / img.width
    height = int(width * aspect * 0.5)
    img = img.resize((width, height * 4), Image.Resampling.LANCZOS)
    pixels = np.array(img)
    pixels = 255 - pixels  # Invert: white bg becomes black in output
    
    braille_text = ""
    for y in range(0, height * 4, 4):
        row = ""
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
            row += chr(0x2800 + bits)
        braille_text += row + "\n"
    
    return braille_text.strip()

def create_all_outputs(video_path, output_dir="frames", fps=10, width=60, max_duration=15):
    """Create GIF, frames, and JSON."""
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Cannot open video: {video_path}")
        return
    
    video_fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_skip = max(1, video_fps // fps)
    
    gif_frames = []
    text_frames = []
    frame_count = 0
    extracted_count = 0
    
    print(f"🎥 Processing: {video_path}")
    print(f"📊 Original: {video_fps} FPS")
    print(f"🎯 Target: {fps} FPS, Width: {width} chars")
    
    # Try to load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    except:
        print("⚠️  Using default font")
        font = ImageFont.load_default()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if max_duration > 0 and frame_count / video_fps > max_duration:
            break
        
        if frame_count % frame_skip == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Get braille text
            braille_text = frame_to_braille(frame_rgb, width=width, threshold=150)
            
            # Save individual .txt frame
            frame_filename = f"frame_{extracted_count:04d}.txt"
            frame_path = os.path.join(output_dir, frame_filename)
            with open(frame_path, 'w', encoding='utf-8') as f:
                f.write(braille_text)
            
            text_frames.append({
                "name": frame_filename,
                "content": braille_text,
                "index": extracted_count
            })
            
            # Create image for GIF from braille text
            lines = braille_text.split('\n')
            char_width = 12
            char_height = 18
            img_width = width * char_width
            img_height = len(lines) * char_height
            
            # Create image
            img = Image.new('RGB', (img_width, img_height), color='black')
            draw = ImageDraw.Draw(img)
            
            # Draw braille text
            for i, line in enumerate(lines):
                draw.text((0, i * char_height), line, font=font, fill='white')
            
            gif_frames.append(np.array(img))
            
            extracted_count += 1
            
            if extracted_count % 10 == 0:
                print(f"  📸 Extracted frame {extracted_count}")
        
        frame_count += 1
    
    cap.release()
    
    if not extracted_count:
        print("❌ No frames extracted!")
        return
    
    # 1. Save GIF
    print(f"💾 Saving GIF: braille_video.gif ({len(gif_frames)} frames)")
    imageio.mimsave("braille_video.gif", gif_frames, fps=fps)
    
    # 2. Save JSON
    json_data = {
        "frames": text_frames,
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
    
    # 3. Save first frame as sample
    if gif_frames:
        Image.fromarray(gif_frames[0]).save("first_frame.png")
    
    print(f"\n✅ Created all outputs:")
    print(f"   - braille_video.gif ({len(gif_frames)} frames)")
    print(f"   - frames/ ({extracted_count} .txt files)")
    print(f"   - frames.json")
    print(f"   - first_frame.png")
    
    return extracted_count

if __name__ == "__main__":
    video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.gif', '.webm')
    video_files = [f for f in os.listdir() if f.lower().endswith(video_exts)]
    
    if not video_files:
        print("❌ No video file found in repo!")
        print("   Add a video file to the repository root.")
        exit(1)
    
    video_file = video_files[0]
    
    frame_count = create_all_outputs(
        video_path=video_file,
        output_dir="frames",
        fps=10,
        width=60,
        max_duration=15
    )
    
    if frame_count:
        print(f"\n🎉 Success! Created {frame_count} frames total")
