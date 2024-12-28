# Wii U Inspired Shader Project

This project recreates the background animation from the Wii U Mii transfer screen, enhanced with customizable color palettes, smooth transitions, and additional visual effects.

## Features
- Dynamic wave animations with randomized properties.
- Gradient backgrounds with smooth transitions.
- Optional dot grid overlay for added visual texture.

## Folder Structure
```plaintext
SDF Project/
├── src/                  # Source code
│   ├── preview.py        # Preview script
│   ├── record.py         # Video recording script
│   ├── extractColors.py  # Color extraction logic
├── shaders/              # Shader files
│   ├── wiiU.frag         # Fragment shader
│   ├── wiiU.vert         # Vertex shader
├── experiments/          # Experimental side projects
│   ├── sdfCircles.py     # SDF exploration
├── assets/               # Input data
│   ├── Album Covers/     # Album cover images
│   ├── durations.txt     # Timing information for rendering
├── venv/                 # Virtual environment (excluded in `.gitignore`)
├── requirements.txt      # Python dependencies
├── .gitignore            # Exclude unnecessary files
├── README.md             # Project documentation

## Utility: extractColors.py
This script provides the `extract_kmean_colors` function, which extracts dominant colors from an image using K-means clustering. It is used by:
- `src/preview.py` to dynamically assign color palettes for live shader previews.
- `src/record.py` to generate video frames with color palettes based on input images.

You can also run this script directly to test its functionality on individual images.