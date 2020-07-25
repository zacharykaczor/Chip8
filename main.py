import random
import numpy
import time
import glfw
import sys
import glm
import os

from OpenGL.GL import *


def keyboard(window):
    glfw.poll_events()

    return {
        0x1: glfw.get_key(window, glfw.KEY_1),
        0x2: glfw.get_key(window, glfw.KEY_2),
        0x3: glfw.get_key(window, glfw.KEY_3),
        0xC: glfw.get_key(window, glfw.KEY_4),

        0x4: glfw.get_key(window, glfw.KEY_Q),
        0x5: glfw.get_key(window, glfw.KEY_W),
        0x6: glfw.get_key(window, glfw.KEY_E),
        0xD: glfw.get_key(window, glfw.KEY_R),

        0x7: glfw.get_key(window, glfw.KEY_A),
        0x8: glfw.get_key(window, glfw.KEY_S),
        0x9: glfw.get_key(window, glfw.KEY_D),
        0xE: glfw.get_key(window, glfw.KEY_F),

        0xA: glfw.get_key(window, glfw.KEY_Z),
        0x0: glfw.get_key(window, glfw.KEY_X),
        0xB: glfw.get_key(window, glfw.KEY_C),
        0xF: glfw.get_key(window, glfw.KEY_V)
    }


def main():
    glfw.init()
    window = glfw.create_window(640, 320, "Chip8", None, None)
    glfw.make_context_current(window)

    program = glCreateProgram()

    with open("vertex.glsl") as source:
        vertex = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex, source.read())
        glCompileShader(vertex)
        glAttachShader(program, vertex)

    with open("fragment.glsl") as source:
        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment, source.read())
        glCompileShader(fragment)
        glAttachShader(program, fragment)

    glLinkProgram(program)

    vbo = glGenBuffers(1)
    vao = glGenVertexArrays(1)

    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
    glEnableVertexAttribArray(0)

    glBindVertexArray(0)

    program_counter = 0x200
    index = 0

    display   = [[0] * 64 for _ in range(32)]
    memory    = [0] * 4096
    variables = [0] * 16
    stack     = [ ]

    delay_timer = 0
    sound_timer = 0

    memory[0: 80] = [
        0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
        0x20, 0x60, 0x20, 0x20, 0x70,  # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
        0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
        0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
        0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
        0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F
    ]

    binary = open("roms/" + input("Program? :> ") + ".ch8", "rb")

    for i, byte in enumerate(binary.read()):
        memory[0x200 + i] = byte

    binary.close()

    timer_clock = time.time()
    cycle_clock = time.time()

    while not glfw.window_should_close(window):
        if time.time() - timer_clock >= 1 / 60:
            if sound_timer > 0:
                sound_timer -= 1
            if delay_timer > 0:
                delay_timer -= 1

            timer_clock = time.time()

        if time.time() - cycle_clock >= 1 / 500:
            glfw.poll_events()

            opcode = memory[program_counter] << 8 | memory[program_counter + 1]

            x   = (opcode & 0x0F00) >> 8
            y   = (opcode & 0x00F0) >> 4
            n   = (opcode & 0x000F)
            nn  = (opcode & 0x00FF)
            nnn = (opcode & 0x0FFF)

            if (opcode & 0xF00F) == 0x0000:
                display = [[0] * 64 for _ in range(32)]

            if (opcode & 0xF00F) == 0x000E:
                program_counter = stack.pop()

            if (opcode & 0xF000) == 0x1000:
                program_counter = nnn - 2

            if (opcode & 0xF000) == 0x2000:
                stack.append(program_counter)
                program_counter = nnn - 2

            if (opcode & 0xF000) == 0x3000:
                if variables[x] == nn:
                    program_counter += 2

            if (opcode & 0xF000) == 0x4000:
                if variables[x] != nn:
                    program_counter += 2

            if (opcode & 0xF000) == 0x5000:
                if variables[x] == variables[y]:
                    program_counter += 2

            if (opcode & 0xF000) == 0x6000:
                variables[x] = nn

            if (opcode & 0xF000) == 0x7000:
                variables[x] = (variables[x] + nn) % 256

            if (opcode & 0xF00F) == 0x8000:
                variables[x] = variables[y]

            if (opcode & 0xF00F) == 0x8001:
                variables[x] = variables[x] | variables[y]

            if (opcode & 0xF00F) == 0x8002:
                variables[x] = variables[x] & variables[y]

            if (opcode & 0xF00F) == 0x8003:
                variables[x] = variables[x] ^ variables[y]

            if (opcode & 0xF00F) == 0x8004:
                if variables[x] + variables[y] > 255:
                    variables[0xF] = 1
                else:
                    variables[0xF] = 0

                variables[x] = (variables[x] + variables[y]) % 256

            if (opcode & 0xF00F) == 0x8005:
                if variables[x] > variables[y]:
                    variables[0xF] = 1
                else:
                    variables[0xF] = 0

                variables[x] = (variables[x] - variables[y]) % 256

            if (opcode & 0xF00F) == 0x8006:
                variables[0xF] = variables[x] & 1
                variables[x] = variables[x] >> 1

            if (opcode & 0xF00F) == 0x8007:
                if variables[y] > variables[x]:
                    variables[0xF] = 1
                else:
                    variables[0xF] = 0

                variables[x] = (variables[y] - variables[x]) % 256

            if (opcode & 0xF00F) == 0x800E:
                variables[0xF] = variables[x] >> 7
                variables[x] = (variables[x] << 1) % 256

            if (opcode & 0xF000) == 0x9000:
                if variables[x] != variables[y]:
                    program_counter += 2

            if (opcode & 0xF000) == 0xA000:
                index = nnn

            if (opcode & 0xF000) == 0xB000:
                program_counter = nnn + variables[0] - 2

            if (opcode & 0xF000) == 0xC000:
                variables[x] = random.randint(0, 255) & nn

            if (opcode & 0xF000) == 0xD000:  # todo
                variables[0xF] = 0
                x_pos, y_pos = variables[x] % 64, variables[y] % 32
                sprite = memory[index: index + n]

                for y_sprite, row in enumerate(sprite):
                    for x_sprite, pixel in enumerate(bin(row)[2:].zfill(8)):
                        pixel_x = x_pos + x_sprite
                        pixel_y = y_pos + y_sprite

                        if pixel_x >= 64 or pixel_y >= 32:
                            continue

                        if display[pixel_y][pixel_x] == 1 and int(pixel) == 1:
                            variables[0xF] = 1

                        display[pixel_y][pixel_x] ^= int(pixel)

            if (opcode & 0xF00F) == 0xE00E:
                if keyboard(window)[variables[x]] == 1:
                    program_counter += 2

            if (opcode & 0xF00F) == 0xE001:
                if keyboard(window)[variables[x]] == 0:
                    program_counter += 2

            if opcode & 0xF0FF == 0xF007:
                variables[x] = delay_timer

            if opcode & 0xF0FF == 0xF00A:
                key_press = False

                while not key_press:
                    for key, value in keyboard(window).items():
                        if value == 1:
                            variables[x] = key
                            key_press = True
                            break

            if opcode & 0xF0FF == 0xF015:
                delay_timer = variables[x]

            if opcode & 0xF0FF == 0xF018:
                sound_timer = variables[x]

            if opcode & 0xF0FF == 0xF01E:
                index = variables[x] + index

            if opcode & 0xF0FF == 0xF029:
                index = variables[x] * 5

            if opcode & 0xF0FF == 0xF033:
                memory[index + 0] = (variables[x] // 100) % 10
                memory[index + 1] = (variables[x] // 10) % 10
                memory[index + 2] = (variables[x] // 1) % 10

            if opcode & 0xF0FF == 0xF055:
                memory[index: index + x + 1] = variables[:x + 1]

            if opcode & 0xF0FF == 0xF065:
                variables[:x + 1] = memory[index: index + x + 1]

            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(program)

            width, height = glfw.get_window_size(window)
            matrix = glm.ortho(0, width, height, 0)

            location = glGetUniformLocation(program, "ortho_matrix")
            glUniformMatrix4fv(location, 1, GL_FALSE, glm.value_ptr(matrix))

            verticies = []
            for x in range(64):
                for y in range(32):
                    if display[y][x] == 1:
                        verticies.extend([
                            (x    ) * 10, (y    ) * 10,
                            (x + 1) * 10, (y    ) * 10,
                            (x    ) * 10, (y + 1) * 10,
                            (x + 1) * 10, (y + 1) * 10,
                            (x    ) * 10, (y + 1) * 10,
                            (x + 1) * 10, (y    ) * 10
                        ])

            verticies = numpy.array(verticies, dtype=numpy.float32)

            glBindVertexArray(vao)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, verticies.nbytes, verticies, GL_DYNAMIC_DRAW)

            glDrawArrays(GL_TRIANGLES, 0, len(verticies))

            glBindVertexArray(0)
            glUseProgram(0)

            glfw.swap_buffers(window)

            program_counter += 2
            cycle_clock = time.time()
    glfw.terminate()


if __name__ == "__main__":
    main()
