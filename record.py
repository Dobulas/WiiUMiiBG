import os
from tkinter import Tk, filedialog
import moderngl
import pygame
import numpy as np
from pygame.locals import DOUBLEBUF, OPENGL
from extractColors import extract_kmean_colors  # Import your K-means function
from time import time
import imageio
from PIL import Image
import subprocess

########################
# Parsing Durations
########################

def parse_durations(file_path):
    """
    Parse song segments and transitions from a text file where lines are either:
      'MM:SS-MM:SS' for a static segment
      'MM:SS-MM:SS transition' for a transition
    """
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

Tk().withdraw()
mix_folder = filedialog.askdirectory(title="Select the Mix Folder")

if not mix_folder:
    print("No folder selected. Exiting...")
    exit(1)

album_covers_folder = os.path.join(mix_folder, "Album Covers")
durations_file = os.path.join(mix_folder, "durations.txt")
folder_name = os.path.basename(mix_folder)
output_video_path = os.path.join(mix_folder, f"{folder_name}.mp4")

if not os.path.exists(album_covers_folder) or not os.path.exists(durations_file):
    print("Error: Folder structure is invalid. Exiting...")
    exit(1)

image_paths = load_images_from_folder(album_covers_folder)
segments = parse_durations(durations_file)

if not image_paths:
    print("No valid images found in the Album Covers folder. Exiting...")
    exit(1)

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
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

WIDTH, HEIGHT = 3840, 2160
screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
ctx = moderngl.create_context()

########################
# Shader Load Helpery
########################

def load_shader(file_path):
    with open(file_path, 'r') as file:
        return file.read()

vertex_shader = """
#version 330 core
layout(location = 0) in vec2 in_position;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
}
""".strip()

fragment_shader = load_shader("wiiU.frag")  # Update this to the correct path of your shader

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
program["u_resolution"].value = (WIDTH, HEIGHT)
program["u_lineAlpha"].value = 1.0
program["transitionProgress"].value = 0.0

########################
# Palette Functions
########################

def set_static_palette(palette):
    """Set uniform colors for a static (non-transition) segment."""
    bg_top, bg_bottom, waves = palette
    program["backgroundTopColor"].value = tuple(bg_top)
    program["backgroundBottomColor"].value = tuple(bg_bottom)
    program["nextBackgroundTopColor"].value = tuple(bg_top)
    program["nextBackgroundBottomColor"].value = tuple(bg_bottom)

    for i, c in enumerate(waves):
        program[f"waveColor{i}"].value = tuple(c)
        program[f"nextWaveColor{i}"].value = tuple(c)

def update_transition_palettes(start_palette, end_palette):
    """Blend between two palettes during transition."""
    bg_top_s, bg_bottom_s, waves_s = start_palette
    bg_top_e, bg_bottom_e, waves_e = end_palette

    program["backgroundTopColor"].value = tuple(bg_top_s)
    program["backgroundBottomColor"].value = tuple(bg_bottom_s)
    program["nextBackgroundTopColor"].value = tuple(bg_top_e)
    program["nextBackgroundBottomColor"].value = tuple(bg_bottom_e)

    for i in range(7):
        program[f"waveColor{i}"].value = tuple(waves_s[i])
        program[f"nextWaveColor{i}"].value = tuple(waves_e[i])

########################
# Assign Palettes
########################

# Assign a 'palette_id' to each non-transition (static) segment
palette_index = 0
for seg in segments:
    if not seg.get("transition", False):  # Only static segments get a palette_id
        seg["palette_id"] = palette_index
        palette_index += 1

# Validate the number of static segments matches the number of album covers
static_segments = [s for s in segments if not s.get("transition", False)]
if len(static_segments) != len(image_paths):
    print(f"Error: Number of static segments ({len(static_segments)}) does not match "
          f"the number of album covers ({len(image_paths)}). Exiting...")
    exit(1)

# For transition segments, assign start_palette and end_palette
for i, seg in enumerate(segments):
    if seg.get("transition", False):
        # Find previous and next static segments
        prev_static = None
        next_static = None

        for j in range(i - 1, -1, -1):
            if "palette_id" in segments[j]:
                prev_static = segments[j]
                break

        for j in range(i + 1, len(segments)):
            if "palette_id" in segments[j]:
                next_static = segments[j]
                break

        if not prev_static or not next_static:
            print("Error: Transition segment without valid static segments before/after. Exiting...")
            exit(1)

        seg["start_palette"] = prev_static["palette_id"]
        seg["end_palette"] = next_static["palette_id"]

########################
# Video Recording Setup
########################

writer = None
frame_count = 0
render_start_time = time()  # Start timing the render
start_time = time()
current_segment_index = 0
fps_list = []
target_frame_time = 1 / 60  # Target 60 FPS

########################
# Main Loop
########################

try:
    running = True
    while running:
        frame_start_time = time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Increment frame count
        frame_count += 1

        elapsed_time = time() - start_time
        program["u_time"].value = elapsed_time

        current_segment = segments[current_segment_index]
        seg_start = current_segment["start"]
        seg_end = current_segment["end"]
        seg_duration = seg_end - seg_start
        seg_progress = (elapsed_time - seg_start) / seg_duration if seg_duration > 0 else 1.0
        seg_progress = max(0.0, min(seg_progress, 1.0))

        if not current_segment.get("transition", False):
            program["transitionProgress"].value = 0.0
            set_static_palette(palettes[current_segment["palette_id"]])
        else:
            program["transitionProgress"].value = seg_progress
            sp = palettes[current_segment["start_palette"]]
            ep = palettes[current_segment["end_palette"]]
            update_transition_palettes(sp, ep)

        if elapsed_time > seg_end:
            current_segment_index += 1
            if current_segment_index >= len(segments):
                running = False
            continue

        # Render and capture frame
        ctx.clear(0.0, 0.0, 0.0)
        vao.render(moderngl.TRIANGLE_STRIP)
        pygame.display.flip()

        # Initialize the writer on the first frame
        if writer is None:
            standard_fps = 60
            writer = imageio.get_writer(
                output_video_path,
                quality=10,
                fps=standard_fps,
                macro_block_size=None,
                codec="libx264",
                bitrate="5000k"
            )

        # Capture and process the frame
        frame_data = ctx.screen.read(components=3, alignment=1)
        frame_image = Image.frombytes("RGB", (WIDTH, HEIGHT), frame_data)
        frame_image = frame_image.transpose(Image.FLIP_TOP_BOTTOM)
        writer.append_data(np.array(frame_image))

        elapsed_frame_time = time() - frame_start_time
        fps_list.append(1 / elapsed_frame_time if elapsed_frame_time > 0 else 60)

        if elapsed_frame_time < target_frame_time:
            pygame.time.wait(int((target_frame_time - elapsed_frame_time) * 1000))

except KeyboardInterrupt:
    print("\nRendering interrupted by user.")
finally:
    if writer:
        writer.close()
    pygame.quit()

    # Total render time
    render_elapsed_time = time() - render_start_time
    print(f"Render elapsed time: {render_elapsed_time:.2f} seconds")

    # Recalculate total timeline duyration
    total_timeline_duration = sum(seg["end"] - seg["start"] for seg in segments)
    print(f"Total intended timeline duration: {total_timeline_duration:.2f} seconds")

    # Ensure proper playback speed adjustment
    effective_fps = frame_count / render_elapsed_time
    playback_speed = render_elapsed_time / total_timeline_duration
    print(f"Playback speed adjustment factor: {playback_speed:.2f}")

    # Adjust the video playback speed
    adjusted_video_path = output_video_path.replace(".mp4", "_adjusted.mp4")
    subprocess.run([
        "ffmpeg", "-i", output_video_path,
        "-filter:v", f"setpts={1 / playback_speed}*PTS",
        "-r", str(standard_fps),  # Match the intended FPS
        adjusted_video_path
    ])
    print(f"Adjusted video saved to: {adjusted_video_path}")