import os
import moderngl
import numpy as np
from PIL import Image
import imageio
from time import time
from tkinter import Tk, filedialog  # For folder selection
from extractColors import extract_kmean_colors
# Add the root directory to the module search path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FRAGMENT_SHADER_PATH, VERTEX_SHADER_PATH


########################
# Parsing Durations
########################

def parse_durations(file_path):
    segments = []
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    for line in lines:
        parts = line.split()
        time_range = parts[0]
        start_str, end_str = time_range.split('-')
        start_minutes, start_seconds = map(int, start_str.split(':'))
        end_minutes, end_seconds = map(int, end_str.split(':'))
        start_time = start_minutes * 60 + start_seconds
        end_time = end_minutes * 60 + end_seconds
        if len(parts) > 1 and parts[1].lower() == "transition":
            segments.append({"start": start_time, "end": end_time, "transition": True})
        else:
            segments.append({"start": start_time, "end": end_time})
    return segments

########################
# Load Images
########################

def load_images_from_folder(folder_path):
    supported_formats = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
    return sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.splitext(f)[-1].lower() in supported_formats])

########################
# Setup Moderngl Context
########################

WIDTH, HEIGHT = 1920, 1080
FPS = 60

ctx = moderngl.create_standalone_context()

# Load vertex and fragment shaders
def load_shader(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Shader file not found: {file_path}")
    with open(file_path, 'r') as f:
        return f.read()
    
vertex_shader = load_shader(VERTEX_SHADER_PATH)
fragment_shader = load_shader(FRAGMENT_SHADER_PATH)

program = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

vertices = np.array([[-1.0, -1.0], [1.0, -1.0], [-1.0, 1.0], [1.0, 1.0]], dtype="f4")
vbo = ctx.buffer(vertices)
vao = ctx.simple_vertex_array(program, vbo, "in_position")

fbo = ctx.framebuffer(color_attachments=[ctx.texture((WIDTH, HEIGHT), 4)])
fbo.use()

########################
# Initialize Uniforms
########################

program["u_resolution"].value = (WIDTH, HEIGHT)
program["u_lineAlpha"].value = 1.0
program["transitionProgress"].value = 0.0

########################
# Select Folder for Mix
########################

Tk().withdraw()  # Hide the Tkinter root window
mix_folder = filedialog.askdirectory(title="Select the Mix Folder")

if not mix_folder:
    print("No folder selected. Exiting...")
    exit(1)

album_covers_folder = os.path.join(mix_folder, "Album Covers")
durations_file = os.path.join(mix_folder, "durations.txt")

# Validate the folder structure
if not os.path.exists(album_covers_folder):
    print(f"Error: {album_covers_folder} not found. Exiting...")
    exit(1)
if not os.path.exists(durations_file):
    print(f"Error: {durations_file} not found. Exiting...")
    exit(1)

# Load data
image_paths = load_images_from_folder(album_covers_folder)
segments = parse_durations(durations_file)

palettes = [extract_kmean_colors(img) for img in image_paths]
palette_index = 0
for seg in segments:
    if not seg.get("transition", False):
        seg["palette_id"] = palette_index
        palette_index += 1
for i, seg in enumerate(segments):
    if seg.get("transition", False):
        prev_static = next_static = None
        for j in range(i - 1, -1, -1):
            if "palette_id" in segments[j]:
                prev_static = segments[j]
                break
        for j in range(i + 1, len(segments)):
            if "palette_id" in segments[j]:
                next_static = segments[j]
                break
        seg["start_palette"] = prev_static["palette_id"]
        seg["end_palette"] = next_static["palette_id"]

########################
# Palette Handling Functions
########################

def set_static_palette(palette):
    """Set uniform colors for a static (non-transition) segment."""
    bg_top, bg_bottom, waves = palette
    program["backgroundTopColor"].value = tuple(bg_top)
    program["backgroundBottomColor"].value = tuple(bg_bottom)
    for i, color in enumerate(waves):
        program[f"waveColor{i}"].value = tuple(color)

def update_transition_palettes(start_palette, end_palette):
    """Blend between two palettes during a transition."""
    bg_top_s, bg_bottom_s, waves_s = start_palette
    bg_top_e, bg_bottom_e, waves_e = end_palette

    # Assign the transition palettes
    program["backgroundTopColor"].value = tuple(bg_top_s)
    program["backgroundBottomColor"].value = tuple(bg_bottom_s)
    program["nextBackgroundTopColor"].value = tuple(bg_top_e)
    program["nextBackgroundBottomColor"].value = tuple(bg_bottom_e)
    for i in range(len(waves_s)):
        program[f"waveColor{i}"].value = tuple(waves_s[i])
        program[f"nextWaveColor{i}"].value = tuple(waves_e[i])

########################
# Main Rendering Loop
########################

frame_index = 0  # Track the number of frames rendered
output_path = os.path.join(mix_folder, "output.mp4")
writer = imageio.get_writer(
    output_path,
    fps=FPS,
    codec="libx264",
    quality=10,
    ffmpeg_params=[
        "-pix_fmt", "yuv420p",        # YUV 4:2:0 format
        "-crf", "18",                 # High-quality compression
        "-preset", "slow",            # Balances speed and quality
        "-profile:v", "high",         # High profile for H.264
        "-level", "4.2",              # Compatible level
        "-b:v", "12M",                # Target bitrate for 1080p60
        "-maxrate", "15M",            # Max bitrate for buffering
        "-bufsize", "24M",            # Larger buffer size for smoother encoding
        "-movflags", "faststart"      # Ensures playback starts immediately
    ]
)

start_time = time()
current_segment_index = 0
running = True

# Initialize the first segment (static or transition)
current_segment = segments[current_segment_index]
if not current_segment.get("transition", False):
    program["transitionProgress"].value = 0.0
    set_static_palette(palettes[current_segment["palette_id"]])
else:
    start_palette = palettes[current_segment["start_palette"]]
    end_palette = palettes[current_segment["end_palette"]]
    update_transition_palettes(start_palette, end_palette)
    program["transitionProgress"].value = 0.0

try:
    while running:
        # Determine elapsed time based on frame count
        elapsed_time = frame_index / FPS
        program["u_time"].value = elapsed_time

        # Determine current segment
        current_segment = segments[current_segment_index]
        seg_start = current_segment["start"]
        seg_end = current_segment["end"]

        # Update segment progress
        seg_progress = (elapsed_time - seg_start) / (seg_end - seg_start)
        seg_progress = max(0.0, min(seg_progress, 1.0))

        if not current_segment.get("transition", False):
            # Static palette
            program["transitionProgress"].value = 0.0
            set_static_palette(palettes[current_segment["palette_id"]])
        else:
            # Transition palette
            program["transitionProgress"].value = seg_progress
            start_palette = palettes[current_segment["start_palette"]]
            end_palette = palettes[current_segment["end_palette"]]
            update_transition_palettes(start_palette, end_palette)

        # Move to the next segment if necessary
        if elapsed_time > seg_end:
            current_segment_index += 1
            if current_segment_index >= len(segments):
                break

        # Render to framebuffer
        ctx.clear(0.0, 0.0, 0.0)
        vao.render(moderngl.TRIANGLE_STRIP)

        # Capture frame
        image_data = fbo.read(components=3)
        frame = np.frombuffer(image_data, dtype=np.uint8).reshape(HEIGHT, WIDTH, 3)
        frame = np.flipud(frame)  # Correct upside-down issue
        writer.append_data(frame)

        # Increment frame index
        frame_index += 1

except KeyboardInterrupt:
    print("Rendering interrupted by user.")
finally:
    writer.close()
    print(f"Rendering completed. Video saved to {output_path}")