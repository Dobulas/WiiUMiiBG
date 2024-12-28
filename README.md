WiiUMiiBG

A shader inspired by the Wii U Mii transfer screen where users scanned QR codes to transfer Miis. This version adds the ability to select a color palette from the top 7 colors in an image and transitions between palettes over time. Originally created for a YouTube mix.

Features

- Dynamic Wave Animation: Smooth, customizable wave animations inspired by the Wii U Mii transfer screen.
- Color Palette Extraction: Uses K-means clustering to extract dominant colors from album cover images.
- Gradient Transitions: Gradual transitions between extracted color palettes for visual fluidity.
- Video Rendering: Outputs a high-quality MP4 file of the shader animation.

Folder Structure

SDF Project/
├── src/                  # Source code
│   ├── preview.py        # Real-time shader preview script
│   ├── record.py         # Shader animation video renderer
│   ├── extractColors.py  # Color extraction using K-means clustering
├── shaders/              # Shader files
│   ├── wiiU.frag         # Fragment shader
│   ├── wiiU.vert         # Vertex shader
├── assets/               # Input data
│   ├── Album Covers/     # Album cover images (input for color extraction)
│   ├── durations.txt     # Timing for animation segments
├── venv/                 # Virtual environment (excluded in .gitignore)
├── requirements.txt      # Python dependencies
├── .gitignore            # Excluded files/folders
├── README.md             # Project documentation

Requirements

Ensure you have Python 3.7+ installed. Install the required libraries by running:
pip install -r requirements.txt

Dependencies

The project relies on the following Python libraries:
- moderngl: For GPU-accelerated rendering.
- pygame: For real-time preview window.
- numpy: For numerical operations.
- scikit-learn: For K-means clustering.
- Pillow: For image processing.
- imageio: For video encoding.

Usage

1. Live Shader Preview
Run the shader animation in real-time using:
python src/preview.py

Inputs:
- A folder containing album covers.
- A durations.txt file specifying animation segment timings.

Steps:
- Select a folder containing the required input files.
- Watch the real-time shader animation.

2. Render Video
Generate a high-quality MP4 video of the shader animation:
python src/record.py

Inputs:
- Same as the preview script: album covers and durations.txt.

Output:
- The rendered video is saved as output.mp4 in the same folder.

File Details

1. src/preview.py
- Previews the shader animation in real-time.
- Dynamically extracts color palettes from images and applies them to the animation.

2. src/record.py
- Renders the shader animation to a video file.
- Outputs a high-quality MP4 file using the extracted color palettes.

3. src/extractColors.py
- Extracts dominant colors from input images using K-means clustering.
- Determines the darkest and lightest colors for gradient backgrounds and sorts remaining colors by saturation for wave colors.

4. shaders/wiiU.frag and shaders/wiiU.vert
- GLSL shaders responsible for rendering the wave animation and gradient backgrounds.

Inputs

1. Album Covers
Place album cover images in the assets/Album Covers/ directory. Supported formats:
- .png, .jpg, .jpeg, .bmp, .tiff.

2. durations.txt
This file specifies the duration and type of each animation segment. Example format:
0:00-0:15
0:15-0:30 transition
0:30-0:45

- Non-transition segments specify static color palettes.
- Transition segments smoothly blend between two palettes.

Outputs

1. Live Preview
Displays the shader animation in a window.

2. Rendered Video
A high-quality MP4 video file (output.mp4) is saved to the same folder as the input files.

Inspiration

This project is inspired by the Wii U Mii transfer screen's smooth wave animations and customizable visuals. It's a tribute to the design aesthetics of the Wii U.

License

This project is licensed under the MIT License. See the LICENSE file for details.

Contributions

Contributions are welcome! If you'd like to improve the project, submit a pull request or open an issue.