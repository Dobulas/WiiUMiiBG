import os
import sys

# Add the root directory to the module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tkinter import Tk, filedialog
import moderngl
import pygame
import numpy as np
from pygame.locals import DOUBLEBUF, OPENGL
from extractColors import extract_kmean_colors  # Import your K-means function
from time import time
from config import FRAGMENT_SHADER_PATH, VERTEX_SHADER_PATH

########################
# Parsing Durations
########################

def parse_durations(file_path):
    """
    Parse song segments and transitions from a text file where lines are either:
      'MM:SS-MM:SS' for a static segment
      'MM:SS-MM:SS transition' for a transition
    No 'speed' or BPM concept is used.
    
    Example lines:
      0:00-0:20
      0:20-0:32 transition
      0:32-0:52
      0:52-1:04 transition
      1:04-1:24
    """
    segments = []

    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]  # Remove empty lines

    for line in lines:
        parts = line.split()
        # Example line: "0:00-1:15" or "0:00-1:15 transition"
        time_range = parts[0]
        start_str, end_str = time_range.split('-')
        start_minutes, start_seconds = map(int, start_str.split(':'))
        end_minutes, end_seconds = map(int, end_str.split(':'))
        start_time = start_minutes * 60 + start_seconds
        end_time = end_minutes * 60 + end_seconds

        if len(parts) > 1 and parts[1].lower() == "transition":
            # It's a transition segment
            segments.append({
                "start": start_time,
                "end": end_time,
                "transition": True
            })
        else:
            # Static segment (no speed)
            segments.append({
                "start": start_time,
                "end": end_time
            })

    return segments

########################
# Load Images
########################

def load_images_from_folder(folder_path):
    """Return all image paths from a folder in sorted order."""
    supported_formats = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
    image_paths = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if os.path.splitext(f)[-1].lower() in supported_formats
    ]
    return sorted(image_paths)

########################
# Open Mix Folder
########################

Tk().withdraw()  # Hide Tkinter root window
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

if not image_paths:
    print("No valid images found in the Album Covers folder. Exiting...")
    exit(1)

########################
# Assign Palettes
########################

# We assign a 'palette_id' to each non-transition (static) segment
palette_index = 0
for seg in segments:
    # If it doesn't have "transition", it's a static segment
    if not seg.get("transition", False):
        seg["palette_id"] = palette_index
        palette_index += 1

# Validate the number of static segments matches the covers
static_segments = [s for s in segments if not s.get("transition", False)]
if len(static_segments) != len(image_paths):
    print(f"Error: Number of static segments ({len(static_segments)}) does not match "
          f"the number of album covers ({len(image_paths)}). Exiting...")
    exit(1)

# For transitions, find the palettes they blend between
for i, seg in enumerate(segments):
    if seg.get("transition", False):
        # Find previous static
        prev_static = None
        for j in range(i - 1, -1, -1):
            if "palette_id" in segments[j]:
                prev_static = segments[j]
                break

        # Find next static
        next_static = None
        for j in range(i + 1, len(segments)):
            if "palette_id" in segments[j]:
                next_static = segments[j]
                break

        if not prev_static or not next_static:
            print("Error: Transition segment without proper static segments before/after.")
            exit(1)

        seg["start_palette"] = prev_static["palette_id"]
        seg["end_palette"]   = next_static["palette_id"]

########################
# Preload Palettes
########################

print("Preloading palettes...")
palettes = [extract_kmean_colors(img_path) for img_path in image_paths]
print("Palettes preloaded.")

########################
# Initialize Pygame & OpenGL
########################

pygame.init()

# Request OpenGL 3.3 Core Profile
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

screen = pygame.display.set_mode((1600, 900), DOUBLEBUF | OPENGL)
ctx = moderngl.create_context()

########################
# Shader Load Helper
########################

def load_shader(file_path):
    with open(file_path, 'r') as file:
        return file.read()

vertex_shader = load_shader(VERTEX_SHADER_PATH)
fragment_shader = load_shader(FRAGMENT_SHADER_PATH)

########################
# Compile/Link Shader
########################

try:
    program = ctx.program(
        vertex_shader=vertex_shader,
        fragment_shader=fragment_shader,
    )
except Exception as e:
    print(f"Shader compilation/linking error: {e}")
    pygame.quit()
    exit(1)

########################
# Setup Geometry
########################

vertices = np.array([
    [-1.0, -1.0],
    [ 1.0, -1.0],
    [-1.0,  1.0],
    [ 1.0,  1.0],
], dtype="f4")

vbo = ctx.buffer(vertices)
vao = ctx.simple_vertex_array(program, vbo, "in_position")

# Initialize some uniform defaults
program["u_resolution"].value         = (1600, 900)
program["u_lineAlpha"].value          = 1.0
program["transitionProgress"].value   = 0.0

########################
# Palette Functions
########################

def set_static_palette(palette):
    """Set uniform colors for a static (non-transition) segment."""
    bg_top, bg_bottom, waves = palette
    program["backgroundTopColor"].value         = tuple(bg_top)
    program["backgroundBottomColor"].value      = tuple(bg_bottom)
    program["nextBackgroundTopColor"].value     = tuple(bg_top)
    program["nextBackgroundBottomColor"].value  = tuple(bg_bottom)

    for i, c in enumerate(waves):
        program[f"waveColor{i}"].value     = tuple(c)
        program[f"nextWaveColor{i}"].value = tuple(c)

def update_transition_palettes(start_palette, end_palette):
    """Blend between two palettes during transition."""
    bg_top_s,    bg_bottom_s,    waves_s = start_palette
    bg_top_e,    bg_bottom_e,    waves_e = end_palette

    program["backgroundTopColor"].value         = tuple(bg_top_s)
    program["backgroundBottomColor"].value      = tuple(bg_bottom_s)
    program["nextBackgroundTopColor"].value     = tuple(bg_top_e)
    program["nextBackgroundBottomColor"].value  = tuple(bg_bottom_e)

    for i in range(7):
        program[f"waveColor{i}"].value     = tuple(waves_s[i])
        program[f"nextWaveColor{i}"].value = tuple(waves_e[i])

########################
# Main Loop
########################

start_time = time()
current_segment_index = 0
last_log_time = time()

# Initialize the very first segment
current_segment = segments[current_segment_index]
if not current_segment.get("transition", False):
    # It's a static segment
    program["transitionProgress"].value = 0.0
    set_static_palette(palettes[current_segment["palette_id"]])
else:
    # It's a transition (should be rare as the first segment)
    sp = palettes[current_segment["start_palette"]]
    ep = palettes[current_segment["end_palette"]]
    update_transition_palettes(sp, ep)
    program["transitionProgress"].value = 0.0

running = True

try:
    while running:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Current time in seconds since start
        elapsed_time = time() - start_time
        program["u_time"].value = elapsed_time

        # Figure out where we are in the segment timeline
        current_segment = segments[current_segment_index]
        seg_start = current_segment["start"]
        seg_end   = current_segment["end"]
        seg_duration = seg_end - seg_start
        seg_progress = (elapsed_time - seg_start) / seg_duration if seg_duration > 0 else 1.0
        seg_progress = max(0.0, min(seg_progress, 1.0))

        # Decide if this is a static or transition segment
        if not current_segment.get("transition", False):
            # Static segment
            program["transitionProgress"].value = 0.0
            # We already set the palette in the code below,
            # but let's re-set for safety each frame:
            set_static_palette(palettes[current_segment["palette_id"]])

            # Log once a second
            if time() - last_log_time >= 1.0:
                print(f"[STATIC] Segment index: {current_segment_index}, progress: 0.0")
                last_log_time = time()

        else:
            # It's a transition
            program["transitionProgress"].value = seg_progress

            sp = palettes[current_segment["start_palette"]]
            ep = palettes[current_segment["end_palette"]]
            update_transition_palettes(sp, ep)

            # Log once a second
            if time() - last_log_time >= 1.0:
                print(f"[TRANSITION] Segment index: {current_segment_index}, progress: {seg_progress:.2f}")
                last_log_time = time()

        # If we've passed the end of the current segment, move on
        if elapsed_time > seg_end:
            current_segment_index += 1
            if current_segment_index >= len(segments):
                # Start over or exit
                current_segment_index = 0
            continue

        # Clear, render, flip
        ctx.clear(0.0, 0.0, 0.0)
        vao.render(moderngl.TRIANGLE_STRIP)
        pygame.display.flip()

except KeyboardInterrupt:
    print("\nRender loop interrupted by user.")
finally:
    pygame.quit()
    print("Program terminated.")