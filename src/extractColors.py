from sklearn.cluster import KMeans
from PIL import Image
import numpy as np
from tkinter import Tk, filedialog

def extract_kmean_colors(image_path, num_colors=9):
    """
    Extracts `num_colors` dominant colors from an image using K-means clustering.
    Sorts the colors to assign the darkest color as the top of the gradient,
    the lightest color as the bottom, and the remaining colors by saturation.
    """
    # Load the image
    image = Image.open(image_path)
    image = image.convert("RGB")  # Ensure it's in RGB mode
    image_data = np.array(image)

    # Reshape the image data to a 2D array of pixels
    pixels = image_data.reshape(-1, 3)

    # Perform K-means clustering
    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(pixels)

    # Get the cluster centers (dominant colors)
    colors = kmeans.cluster_centers_

    # Normalize the colors to 0.0 - 1.0 for use in OpenGL
    normalized_colors = colors / 255.0

    # Sort colors by luminance (darkest to lightest)
    luminance = lambda color: 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
    sorted_colors_by_luminance = sorted(normalized_colors, key=luminance)

    # Assign background colors
    background_top_color = sorted_colors_by_luminance[0]  # Darkest color
    background_bottom_color = sorted_colors_by_luminance[-1]  # Lightest color

    # Remove the top and bottom background colors from the list
    remaining_colors = sorted_colors_by_luminance[1:-1]

    # Sort the remaining colors by saturation
    def saturation(color):
        max_val = max(color)
        min_val = min(color)
        return max_val - min_val  # Saturation formula

    sorted_colors_by_saturation = sorted(remaining_colors, key=saturation, reverse=True)

    return background_top_color, background_bottom_color, sorted_colors_by_saturation

if __name__ == "__main__":
    # Open file dialog to select an image
    Tk().withdraw()  # Hide the root Tkinter window
    image_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
    )

    if not image_path:
        print("No image selected. Exiting...")
    else:
        # Extract colors
        background_top_color, background_bottom_color, wave_colors = extract_kmean_colors(image_path)

        # Print extracted colors
        print("Extracted Colors (Normalized RGB):")
        print(f"Background Top Color (Darkest): {background_top_color}")
        print(f"Background Bottom Color (Lightest): {background_bottom_color}")
        for i, color in enumerate(wave_colors):
            print(f"waveColor{i}: {color}")