import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from itertools import cycle

# Parameters for the canvas and circles
width, height = 1000, 1000
margin = 150
min_distance = 150
radii = [100, 80, 60]  # Circle radii for layers
noise_scale = 0.02  # Noise granularity
noise_intensity = 5  # Noise intensity
sprite_count = 8  # Number of sprites

# Function to generate a random center within a defined margin
def get_random_center(width, height, margin):
    center_x = np.random.randint(margin, width - margin)
    center_y = np.random.randint(margin, height - margin)
    return center_x, center_y

# Function to generate sine-cosine-based noise
def generate_simple_noise(width, height, scale=0.05, intensity=10):
    y, x = np.meshgrid(np.arange(height), np.arange(width))
    noise = np.sin(x * scale) + np.cos(y * scale)
    return noise * intensity

# Function to create a sprite (layered SDF) with noise
def create_sprite(center_x, center_y, radii, noise_scale=0.05, noise_intensity=10):
    y, x = np.meshgrid(np.arange(height), np.arange(width))
    combined_sdf = np.zeros((height, width))
    for radius in radii:
        sdf = np.sqrt((x - center_x)**2 + (y - center_y)**2) - radius
        noise = generate_simple_noise(width, height, scale=noise_scale, intensity=noise_intensity)
        sdf_with_noise = sdf + noise
        combined_sdf = np.minimum(combined_sdf, sdf_with_noise)
    return combined_sdf

# Updated list of sequential Matplotlib colormaps
sequential_colormaps = [
    plt.cm.Greys, plt.cm.Purples, plt.cm.Blues, plt.cm.Greens, plt.cm.Oranges, plt.cm.Reds,
    plt.cm.YlOrBr, plt.cm.YlOrRd, plt.cm.OrRd, plt.cm.PuRd, plt.cm.RdPu, plt.cm.BuPu,
    plt.cm.GnBu, plt.cm.PuBu, plt.cm.YlGnBu, plt.cm.PuBuGn, plt.cm.BuGn, plt.cm.YlGn
]

# Cycle through the colormaps
colormap_cycle = cycle(sequential_colormaps)

# Generate sprite data
sprites = []
sprite_colors = []
for _ in range(sprite_count):
    center_x, center_y = get_random_center(width, height, margin)
    layered_sdf = create_sprite(center_x, center_y, radii, noise_scale, noise_intensity)
    normalized_sdf = (layered_sdf - layered_sdf.min()) / (layered_sdf.max() - layered_sdf.min())
    colormap = next(colormap_cycle)
    colors_layered = colormap(normalized_sdf)
    alpha_layered = np.clip(1 - normalized_sdf**2, 0, 1)
    colors_layered[..., -1] = alpha_layered  # Set alpha channel
    sprites.append(colors_layered)
    sprite_colors.append((center_x, center_y))

# Animation parameters
sprite_positions = np.random.rand(sprite_count, 2) * np.array([width, height])
sprite_velocities = (np.random.rand(sprite_count, 2) - 0.5) * 10

# Animation function
def update(frame):
    global sprite_positions, sprite_velocities
    ax.clear()
    ax.axis('off')
    for i, sprite in enumerate(sprites):
        sprite_positions[i] += sprite_velocities[i]
        # Bounce sprites off edges
        if sprite_positions[i, 0] < 0 or sprite_positions[i, 0] > width:
            sprite_velocities[i, 0] *= -1
        if sprite_positions[i, 1] < 0 or sprite_positions[i, 1] > height:
            sprite_velocities[i, 1] *= -1
        # Overlay sprite on canvas
        x_pos, y_pos = sprite_positions[i]
        extent = [x_pos - width // 2, x_pos + width // 2, y_pos - height // 2, y_pos + height // 2]
        ax.imshow(sprite, extent=extent)

# Set up the figure
fig, ax = plt.subplots(figsize=(10, 10))
ax.axis('off')

# Run the animation
ani = FuncAnimation(fig, update, frames=200, interval=50, repeat=True)
plt.show()