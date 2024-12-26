import numpy as np
import matplotlib.pyplot as plt

# Step 1: Simple SDF for a single circle
def sdf_circle(x, y, center, radius):
    return np.sqrt((x - center[0])**2 + (y - center[1])**2) - radius

# Step 2: Compute normals (gradients of the SDF)
def compute_normals(sdf, dx=1e-3):
    grad_x = (np.roll(sdf, -1, axis=1) - np.roll(sdf, 1, axis=1)) / (2 * dx)
    grad_y = (np.roll(sdf, -1, axis=0) - np.roll(sdf, 1, axis=0)) / (2 * dx)
    magnitude = np.sqrt(grad_x**2 + grad_y**2 + 1e-5)
    return grad_x / magnitude, grad_y / magnitude  # Normalize the gradients

# Step 3: Lambertian lighting with mask
def apply_lighting(sdf, light_dir, threshold=0.01):
    normals = compute_normals(sdf)
    brightness = normals[0] * light_dir[0] + normals[1] * light_dir[1]
    brightness = np.clip(brightness, 0, 1)
    
    # Mask: Only keep values close to the surface
    mask = np.abs(sdf) < threshold
    return brightness * mask  # Apply mask to lighting

# Step 4: Generate the SDF and apply lighting
def generate_simple_3d_circle(width, height, center, radius, light_dir):
    # Coordinate grid
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    X, Y = np.meshgrid(x, y)
    
    # Generate SDF for one circle
    sdf = sdf_circle(X, Y, center, radius)
    
    # Apply lighting
    lighting = apply_lighting(sdf, light_dir)
    return lighting

# Define light direction and circle parameters
light_direction = np.array([1, -1]) / np.sqrt(2)  # Top-right light
circle_center = (0.0, 0.0)  # Center of the circle
circle_radius = 0.5  # Radius of the circle

# Generate image
width, height = 512, 512
lighting_result = generate_simple_3d_circle(width, height, circle_center, circle_radius, light_direction)

# Plot the result
plt.imshow(lighting_result, cmap='gray', extent=(-1, 1, -1, 1))
plt.axis('off')
plt.title("Fixed Pseudo-3D Circle with Masked Lighting")
plt.show()