import os

# Base directory for the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Subdirectories
SHADERS_DIR = os.path.join(BASE_DIR, "shaders")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SRC_DIR = os.path.join(BASE_DIR, "src")

# File paths
FRAGMENT_SHADER_PATH = os.path.join(SHADERS_DIR, "wiiU.frag")
VERTEX_SHADER_PATH = os.path.join(SHADERS_DIR, "wiiU.vert")
ALBUM_COVERS_DIR = os.path.join(ASSETS_DIR, "Album Covers")
DURATIONS_FILE_PATH = os.path.join(ASSETS_DIR, "durations.txt")