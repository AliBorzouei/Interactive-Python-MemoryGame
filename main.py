import pygame
import sys
import random

pygame.init()

WIDTH, HEIGHT = 400, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Game")

my_rows = 4
my_cols = 5
cell_size = WIDTH // my_cols
padding = 5

background_color = (187, 173, 160)
empty_cell_color = (205, 193, 180)
corner_radius = 4

# Load images and create multiple rotated variants for each image
rotation_angles = [0, 90, 180, 270]
images_dict = {}

for i in range(1, 11):
    base_img = pygame.image.load(f"{i}.png").convert_alpha()
    rotated_versions = []
    for angle in rotation_angles:
        rotated_img = pygame.transform.rotate(base_img, angle)
        rotated_versions.append(rotated_img)
    images_dict[i] = rotated_versions

# Create pairs and shuffle
pair_list = list(range(1, 11)) * 2
random.shuffle(pair_list)

# Assign grid with each cell a dict of 'number' and 'image'
grid = []
for r in range(my_rows):
    row = []
    for c in range(my_cols):
        num = pair_list.pop()
        chosen_img = random.choice(images_dict[num])
        row.append({'number': num, 'image': chosen_img})
    grid.append(row)

# Track which cells are revealed
revealed = [[False for _ in range(my_cols)] for _ in range(my_rows)]

# Store reveal animations: key = (row, col), value = start_time
reveal_start_times = {}


matched_pairs_effects = {}

font = pygame.font.SysFont("bahnschrift", 40)

# Game state variables
first_selection = None
second_selection = None
waiting = False
wait_start = 0
delay_time = 1000

game_over = False
game_over_time = 0

def draw_grid(current_time):
    screen.fill(background_color)
    for r in range(my_rows):
        for c in range(my_cols):
            x = c * cell_size + padding
            y = r * cell_size + padding + 80
            cell_rect = (x, y, cell_size - 2 * padding, cell_size - 2 * padding)
            pygame.draw.rect(screen, empty_cell_color, cell_rect, border_radius=corner_radius)

            # Check if this cell is in a match pulsing effect
            is_matched = (r, c) in matched_pairs_effects
            pulse_info = matched_pairs_effects.get((r, c), None)
            scale_factor = 1.0
            border_color = None

            if is_matched and pulse_info:
                # Calculate pulsing scale
                elapsed = current_time - pulse_info['pivot_time']
                pulse_duration = 300  # milliseconds
                # Pulsing effect: scale up and down
                if pulse_info['pulsing']:
                    # expand and contract
                    # using sine wave for smooth pulsing
                    import math
                    phase = (elapsed / pulse_duration) * math.pi
                    scale_factor = 1 + 0.2 * math.sin(phase)
                else:
                    scale_factor = 1.0

                # Optional: change border color or thickness
                border_color = (255, 255, 0)  # bright yellow

                # End pulsing after some time
                if elapsed > pulse_duration:
                    pulse_info['pulsing'] = False
                    # After pulsing, remove pulse effect after a short delay
                    if elapsed > pulse_duration + 200:
                        del matched_pairs_effects[(r, c)]
                        # Remove from circle so next time it's normal

            # Draw image or question mark
            if revealed[r][c]:
                # Check for fade-in animation
                if (r, c) in reveal_start_times:
                    start_time = reveal_start_times[(r, c)]
                    elapsed_time = current_time - start_time
                    duration = 500
                    alpha = min(255, int((elapsed_time / duration) * 255))
                    if alpha >= 255:
                        del reveal_start_times[(r, c)]
                        alpha = 255
                    img = grid[r][c]['image'].copy()
                    img.set_alpha(alpha)
                    # Apply scaling
                    scaled_img = pygame.transform.smoothscale(
                        img,
                        (int(img.get_width() * scale_factor), int(img.get_height() * scale_factor))
                    )
                    img_rect = scaled_img.get_rect(center=(
                        x + (cell_size - 2 * padding) / 2,
                        y + (cell_size - 2 * padding) / 2))
                    # Draw glow border if in a match pulsing
                    if border_color:
                        border_thickness = 4
                        border_rect = pygame.Rect(
                            img_rect.left - border_thickness,
                            img_rect.top - border_thickness,
                            img_rect.width + 2 * border_thickness,
                            img_rect.height + 2 * border_thickness)
                        pygame.draw.rect(screen, border_color, border_rect, border_thickness,
                                         border_radius=corner_radius)
                    screen.blit(scaled_img, img_rect)
                else:
                    # Already fully revealed
                    img = grid[r][c]['image']
                    scaled_img = pygame.transform.smoothscale(
                        img,
                        (int(img.get_width() * scale_factor), int(img.get_height() * scale_factor))
                    )
                    img_rect = scaled_img.get_rect(center=(
                        x + (cell_size - 2 * padding) / 2,
                        y + (cell_size - 2 * padding) / 2))
                    if border_color:
                        border_thickness = 4
                        border_rect = pygame.Rect(
                            img_rect.left - border_thickness,
                            img_rect.top - border_thickness,
                            img_rect.width + 2 * border_thickness,
                            img_rect.height + border_thickness)
                        pygame.draw.rect(screen, border_color, border_rect, border_thickness,
                                         border_radius=corner_radius)
                    screen.blit(scaled_img, img_rect)
            else:
                # Hidden cell: question mark
                question_mark = font.render("?", True, (0, 0, 0))
                rect = question_mark.get_rect(center=(
                    x + (cell_size - 2 * padding) / 2,
                    y + (cell_size - 2 * padding) / 2))
                screen.blit(question_mark, rect)

    if game_over:
        font_msg = pygame.font.SysFont("Arial", 50)
        msg = font_msg.render("Congratulations!", True, (255, 0, 0))
        rect_msg = msg.get_rect(center=(WIDTH // 2, 50))
        screen.blit(msg, rect_msg)

def get_cell(pos):
    x, y = pos
    if y < 100:
        return None
    row = (y - 100) // cell_size
    col = x // cell_size
    if 0 <= row < my_rows and 0 <= col < my_cols:
        return row, col
    return None

def check_win():
    for r in range(my_rows):
        for c in range(my_cols):
            if not revealed[r][c]:
                return False
    return True

# Main game loop
running = True
while running:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and not waiting:
            if not game_over:
                cell = get_cell(pygame.mouse.get_pos())
                if cell:
                    r, c = cell
                    if revealed[r][c]:
                        # Toggle hide (allow hiding the card)
                        if first_selection == (r, c):
                            revealed[r][c] = False
                            if (r, c) in reveal_start_times:
                                del reveal_start_times[(r, c)]
                            first_selection = None
                        elif second_selection == (r, c):
                            revealed[r][c] = False
                            if (r, c) in reveal_start_times:
                                del reveal_start_times[(r, c)]
                            second_selection = None
                    else:
                        # Reveal cell
                        revealed[r][c] = True
                        # Start fade-in animation
                        reveal_start_times[(r, c)] = current_time
                        if not first_selection:
                            first_selection = (r, c)
                        elif not second_selection and (r, c) != first_selection:
                            second_selection = (r, c)
                            # Check for match
                            r1, c1 = first_selection
                            r2, c2 = second_selection
                            if grid[r1][c1]['number'] == grid[r2][c2]['number']:
                                # Match found, trigger pulse effect
                                pivot_time = current_time
                                matched_pairs_effects[(r1, c1)] = {'pivot_time': pivot_time, 'pulsing': True}
                                matched_pairs_effects[(r2, c2)] = {'pivot_time': pivot_time, 'pulsing': True}
                                first_selection = None
                                second_selection = None
                                if check_win():
                                    # All pairs matched
                                    game_over = True
                                    game_over_time = current_time
                            else:
                                # Not a match, wait before hiding
                                waiting = True
                                wait_start = current_time

    # Hide non-matching pair after delay
    if waiting:
        if current_time - wait_start >= delay_time:
            r1, c1 = first_selection
            r2, c2 = second_selection
            revealed[r1][c1] = False
            revealed[r2][c2] = False
            if (r1, c1) in reveal_start_times:
                del reveal_start_times[(r1, c1)]
            if (r2, c2) in reveal_start_times:
                del reveal_start_times[(r2, c2)]
            first_selection = None
            second_selection = None
            waiting = False

    draw_grid(current_time)

    # When game is over, show message then reveal all after 2 seconds
    if game_over:
        if current_time - game_over_time >= 2000:
            for r in range(my_rows):
                for c in range(my_cols):
                    if not revealed[r][c]:
                        revealed[r][c] = True
                        # Start fade-in for the final reveal
                        reveal_start_times[(r, c)] = current_time
            # Optional: you can auto-close or restart here
        draw_grid(current_time)
        pygame.display.flip()
        continue

    pygame.display.flip()

pygame.quit()
sys.exit()