import cv2
import numpy as np
from PIL import Image
import json
import os

def frame_to_braille(frame, width=60, threshold=150):
    """Convert frame to braille ASCII with black background for transparent areas."""
    # Convert to PIL Image
    img = Image.fromarray(frame)
    
    # Handle transparency with BLACK background
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        # Create BLACK background
        background = Image.new('RGB', img.size, (0, 0, 0))  # Black background
        
        if img.mode == 'P':
            img = img.convert('RGBA')
        elif img.mode == 'LA':
            img = img.convert('RGBA')
            
        background.paste(img, (0, 0), img)
        img = background.convert('L')
    else:
        img = img.convert('L')
    
    # Rest of the conversion
    aspect = img.height / img.width
    height = int(width * aspect * 0.5)
    img = img.resize((width, height * 4), Image.Resampling.LANCZOS)
    pixels = np.array(img)
    pixels = 255 - pixels  # Invert for dark text
    
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
    """Convert video to braille frames with black background for transparency."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video {video_path}")
        return []
    
    video_fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps
    
    if max_duration > 0 and duration > max_duration:
        total_frames = int(video_fps * max_duration)
    
    frame_skip = max(1, video_fps // fps)
    frames_data = []
    
    print(f"Processing video: {video_path}")
    print(f"Original: {video_fps} FPS, {duration:.1f}s, {total_frames} frames")
    print(f"Extracting at: {fps} FPS")
    
    frame_count = 0
    extracted_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret or (max_duration > 0 and frame_count / video_fps > max_duration):
            break
        
        if frame_count % frame_skip == 0:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to braille
            braille_text = frame_to_braille(frame_rgb, width=width, threshold=150)
            
            # Save frame
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
            if extracted_count % 10 == 0:
                print(f"  Extracted {extracted_count} frames...")
        
        frame_count += 1
    
    cap.release()
    
    # Create JSON for HTML player
    json_data = {
        "frames": frames_data,
        "info": {
            "video": os.path.basename(video_path),
            "original_fps": video_fps,
            "output_fps": fps,
            "width": width,
            "total_frames": extracted_count,
            "duration": extracted_count / fps
        }
    }
    
    with open("frames.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Done! Extracted {extracted_count} frames to '{output_dir}/'")
    print(f"Created 'frames.json' for the HTML player")
    
    return extracted_count

if __name__ == "__main__":
    # Look for video files
    video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.gif', '.webm')
    video_files = [f for f in os.listdir() if f.lower().endswith(video_exts)]
    
    if not video_files:
        print("❌ No video file found!")
        print("Add a video file (MP4, AVI, MOV, MKV, GIF, WEBM) to the repository root.")
        exit(1)
    
    video_file = video_files[0]
    
    # Convert video to braille frames
    frame_count = video_to_braille_frames(
        video_path=video_file,
        output_dir="frames",
        fps=15,           # Frames per second to extract
        width=60,         # Braille width in characters
        max_duration=30   # Max seconds to process (0 for full video)
    )
    
    # Create a simple HTML file if it doesn't exist
    if not os.path.exists("index.html"):
        print("\n📁 Creating index.html...")
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Braille Video Player</title>
    <style>
        body { background: #111; color: white; font-family: monospace; padding: 20px; }
        #display { background: black; padding: 20px; border-radius: 10px; font-size: 12px; 
                  line-height: 1.2; white-space: pre; min-height: 400px; }
        .controls { margin: 20px 0; }
        button { background: #333; color: white; border: none; padding: 10px 15px; 
                margin: 0 5px; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0af; }
    </style>
</head>
<body>
    <h1>🎬 Braille Video Player</h1>
    <div class="controls">
        <button onclick="play()">▶ Play</button>
        <button onclick="pause()">⏸ Pause</button>
        <button onclick="prev()">◀ Prev</button>
        <button onclick="next()">Next ▶</button>
        <span id="counter">Frame: 0/0</span>
    </div>
    <div id="display">Loading...</div>
    
    <script>
        let frames = [];
        let currentFrame = 0;
        let playing = false;
        let interval;
        
        async function loadFrames() {
            const response = await fetch('frames.json');
            const data = await response.json();
            frames = data.frames.map(f => f.content);
            document.getElementById('counter').textContent = `Frame: 1/${frames.length}`;
            document.getElementById('display').textContent = frames[0];
        }
        
        function play() {
            if (playing) return;
            playing = true;
            interval = setInterval(() => {
                currentFrame = (currentFrame + 1) % frames.length;
                updateDisplay();
            }, 1000/15);
        }
        
        function pause() {
            playing = false;
            clearInterval(interval);
        }
        
        function prev() {
            pause();
            currentFrame = (currentFrame - 1 + frames.length) % frames.length;
            updateDisplay();
        }
        
        function next() {
            pause();
            currentFrame = (currentFrame + 1) % frames.length;
            updateDisplay();
        }
        
        function updateDisplay() {
            document.getElementById('display').textContent = frames[currentFrame];
            document.getElementById('counter').textContent = `Frame: ${currentFrame + 1}/${frames.length}`;
        }
        
        loadFrames();
    </script>
</body>
</html>"""
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("✅ Created index.html")
    
    print(f"\n🎉 Conversion complete!")
    print(f"Run the GitHub workflow, then download the artifact and open 'index.html'")
