import sys
import pygame

# Initialize Pygame
pygame.init()

# Set the window size
window_size = (800, 600)

floorhight = 400


# Create the window
screen = pygame.display.set_mode(window_size)

# Set the title of the window
pygame.display.set_caption('Jump and Run')

# Set up the clock to control the frame rate
clock = pygame.time.Clock()

# Set up the player character
player_image = pygame.image.load('player.png')
player_rect = player_image.get_rect()

# Set the starting position of the player
player_rect.x = 100
player_rect.y = floorhight

# Set the player's starting speed
player_speed = 5

# Set up the gravity
gravity = 0.5

# Set up the jump strength
jump_strength = 10
jump_length = 0
# Set up the player's jumping status
is_jumping = False
double_jump = False
double_jump_ready = False


# Set up the player's jumping velocity
jump_velocity = 0

# Set up the game loop
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Check for key presses
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        # Move the player to the left
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT]:
        # Move the player to the right
        player_rect.x += player_speed
    if keys[pygame.K_SPACE]:
        # Start the player jumping
        if not is_jumping:
            is_jumping = True
            jump_velocity = jump_strength
        else:
            if not double_jump and double_jump_ready:
                double_jump = True
                jump_velocity = jump_strength
    else:
        if is_jumping and not double_jump:
            double_jump_ready = True

    # Update the player's position based on gravity
    if is_jumping:
        jump_length += 1
        player_rect.y -= jump_velocity
        jump_velocity -= gravity
        if player_rect.y >= floorhight:
            # The player has landed
            jump_length = 0
            is_jumping = False
            double_jump = False
            double_jump_ready = False
            player_rect.y = floorhight

    # Draw the player
    screen.fill((0, 0, 0))
    screen.blit(player_image, player_rect)

    # Update the display
    pygame.display.flip()

    # Limit the frame rate to 60 FPS
    clock.tick(60)