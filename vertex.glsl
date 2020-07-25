#version 330

uniform mat4 ortho_matrix;
in vec3 position;

void main()
{
    gl_Position = ortho_matrix * vec4(position.x, position.y, 0.0, 1.0);
}