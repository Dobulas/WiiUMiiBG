#version 330 core

precision highp float;

uniform vec2 u_resolution;           // Canvas resolution
uniform float u_time;                // Time for animation
uniform float u_lineAlpha;           // (0.5 to 1.0) line transparency scale

// Transition uniform (0.0 to 1.0) for color blending only
uniform float transitionProgress;    

// Wave colors
uniform vec3 waveColor0;
uniform vec3 waveColor1;
uniform vec3 waveColor2;
uniform vec3 waveColor3;
uniform vec3 waveColor4;
uniform vec3 waveColor5;
uniform vec3 waveColor6;

// Next wave colors (for transition blending)
uniform vec3 nextWaveColor0;
uniform vec3 nextWaveColor1;
uniform vec3 nextWaveColor2;
uniform vec3 nextWaveColor3;
uniform vec3 nextWaveColor4;
uniform vec3 nextWaveColor5;
uniform vec3 nextWaveColor6;

// Background gradient colors (current)
uniform vec3 backgroundTopColor;
uniform vec3 backgroundBottomColor;

// Next background gradient colors (for transition)
uniform vec3 nextBackgroundTopColor;
uniform vec3 nextBackgroundBottomColor;

out vec4 FragColor;

// A simple pseudo-random function
float random(float x) {
    return fract(sin(x) * 43758.5453123);
}

// (Optional) function to create circular dots
float drawDot(vec2 st, vec2 center, float radius) {
    float dist = length(st - center);
    return 1.0 - smoothstep(radius - 0.0067, radius + 0.00067, dist);
}

void main() {
    vec2 st = gl_FragCoord.xy / u_resolution;
    st.x *= u_resolution.x / u_resolution.y; // Adjust for aspect ratio 

    // Interpolate background colors based on transitionProgress
    vec3 interpolatedTopColor = mix(backgroundTopColor,    nextBackgroundTopColor,    transitionProgress);
    vec3 interpolatedBottomColor = mix(backgroundBottomColor, nextBackgroundBottomColor, transitionProgress);

    // Compute vertical gradient with smoother interpolation
    vec3 color = mix(interpolatedBottomColor, interpolatedTopColor, pow(st.y, 1.2));

    // Base wave parameters (constant speed, no dynamic BPM)
    float baseAmplitude = 0.025;
    float baseFrequency = 3.0;
    float baseFlow      = -0.2;   // A fixed negative flow for horizontal wave motion
    float thickness     = 0.005;

    // Draw multiple waves
    for (int i = 0; i < 7; i++) {
        // Random vertical offset
        float verticalOffset  = mix(-0.2, 0.6, random(float(i)));
        // Random amplitude/frequency
        float amplitude       = baseAmplitude * mix(1.0, 5.3, random(float(i) + 2.0));
        float frequency       = baseFrequency * mix(0.2, 2.5, random(float(i) + 1.0));

        // Random factor for wave flow
        float waveRandomFactor = mix(0.4, 1.5, random(float(i)));
        // Combine baseFlow with waveRandomFactor
        float waveFlow = baseFlow * waveRandomFactor;

        // Reverse direction for certain waves
        if (i == 3 || i == 5) {
            waveFlow = -waveFlow;
        }

        // Interpolate wave colors based on transitionProgress
        vec3 waveColor = mix(
            (i == 0) ? waveColor0 :
            (i == 1) ? waveColor1 :
            (i == 2) ? waveColor2 :
            (i == 3) ? waveColor3 :
            (i == 4) ? waveColor4 :
            (i == 5) ? waveColor5 : waveColor6,
            (i == 0) ? nextWaveColor0 :
            (i == 1) ? nextWaveColor1 :
            (i == 2) ? nextWaveColor2 :
            (i == 3) ? nextWaveColor3 :
            (i == 4) ? nextWaveColor4 :
            (i == 5) ? nextWaveColor5 : nextWaveColor6,
            transitionProgress
        );

        // Compute wave Y using sine
        float waveY = 0.5 + verticalOffset 
                      + amplitude * sin(frequency * st.x + u_time * waveFlow);

        // Wave alpha (smooth lines)
        float waveAlpha = smoothstep(waveY + thickness, waveY, st.y)
                        - smoothstep(waveY, waveY - thickness * 20.0, st.y);

        // Scale alpha by u_lineAlpha uniform
        float scaledAlpha = mix(0.5, 1.0, u_lineAlpha);
        waveAlpha *= scaledAlpha;

        // Blend wave into the background color
        color = mix(color, waveColor, waveAlpha);
    }

    // OPTIONAL: Dot grid overlay
    vec2 gridSize      = vec2(0.0045);
    vec2 gridIndex     = floor(st / gridSize);
    vec2 gridPosition  = gridIndex * gridSize + gridSize * 0.5;
    float dotRadius    = 0.00275;
    float dot          = drawDot(st, gridPosition, dotRadius);

    float dotAlpha     = mod(gridIndex.x + gridIndex.y, 2.0) == 0.0 ? 0.1 : 0.0;
    vec3 dotColor      = vec3(1.3);

    // Blend dots into color
    color = mix(color, dotColor, dot * dotAlpha * 1.2);

    // Final output
    FragColor = vec4(color, 1.0);
}