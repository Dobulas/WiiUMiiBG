#version 330 core

layout(location = 0) in vec2 in_position;  // Vertex input
out vec2 v_position;                      // Output to fragment shader

void main() {
    v_position = in_position;             // Pass position to fragment shader
    gl_Position = vec4(in_position, 0.0, 1.0);  // Position in clip space
}