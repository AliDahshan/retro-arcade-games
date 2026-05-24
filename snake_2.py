import pyglet
import random
from pyglet import shapes
import pyglet.input # Added for controller support
import os 

WIDTH, HEIGHT = 540, 600
CELL_SIZE = 20
window = pyglet.window.Window(WIDTH, HEIGHT, "Snake Xenzia")

STATE_START = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
current_state = STATE_START

# --- Controller Setup ---
controllers = pyglet.input.get_controllers()
controller = None
if controllers:
    controller = controllers[0]
    controller.open()
    print(f"Controller connected: {controller.name}")
else:
    print("No controller found. Using keyboard fallback.")

# Updated Image Loading to use the absolute path
try:
    current_folder = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(current_folder, 'snake_22.jpg')
    
    bg_img = pyglet.image.load(img_path)
    background_sprite = pyglet.sprite.Sprite(bg_img, x=0, y=0)
    background_sprite.scale_x = WIDTH / bg_img.width
    background_sprite.scale_y = HEIGHT / bg_img.height
except Exception as e:
    print(f"Image Error: {e}")
    background_sprite = None

grid_batch = pyglet.graphics.Batch()
grid_lines = []
# Create vertical lines
for x in range(0, WIDTH, CELL_SIZE):
    grid_lines.append(shapes.Line(x, 0, x, HEIGHT, color=(255, 255, 255, 30), batch=grid_batch))
# Create horizontal lines
for y in range(0, HEIGHT, CELL_SIZE):
    grid_lines.append(shapes.Line(0, y, WIDTH, y, color=(255, 255, 255, 30), batch=grid_batch))

def create_label(text, size, x, y, anchor_x='left', anchor_y='baseline'):
    return pyglet.text.Label(text, font_name='Arial', font_size=size,
                             x=x, y=y, anchor_x=anchor_x, anchor_y=anchor_y,
                             color=(255, 255, 255, 255))

score_label = create_label('Score: 0', 14, 10, HEIGHT - 25)
start_label = create_label('PRESS SPACE OR START', 20, WIDTH//2, HEIGHT//2, 'center', 'center')
game_over_label = create_label('GAME OVER - PRESS R OR START', 16, WIDTH//2, HEIGHT//2, 'center', 'center')

snake_coords = []
direction = (0, CELL_SIZE)
score = 0
food_coord = (0, 0)

# --- Fading Motivational Messages ---
MOTIVATIONAL_MESSAGES = [
    'WOW!', 'KEEP GOING!', 'GOOD BOY!', 'AMAZING!', 'ON FIRE!',
    'UNSTOPPABLE!', 'LEGENDARY!', 'BEAST MODE!', 'INSANE!', 'GODLIKE!'
]
fade_label = pyglet.text.Label('', font_name='Arial', font_size=36,
                               x=WIDTH // 2, y=HEIGHT // 2 + 60,
                               anchor_x='center', anchor_y='center',
                               color=(255, 255, 0, 255))
fade_alpha = 0  # current alpha (0 = invisible)
FADE_SPEED = 130  # alpha units lost per second

def trigger_message():
    global fade_alpha
    fade_label.text = random.choice(MOTIVATIONAL_MESSAGES)
    fade_alpha = 255

def update_fade(dt):
    global fade_alpha
    if fade_alpha > 0:
        fade_alpha = max(0, fade_alpha - FADE_SPEED * dt)
        r, g, b, _ = fade_label.color
        fade_label.color = (r, g, b, int(fade_alpha))

pyglet.clock.schedule_interval(update_fade, 1 / 60.0)

def reset_game():
    global snake_coords, direction, score, food_coord, current_state
    start_x = (WIDTH // 2 // CELL_SIZE) * CELL_SIZE
    start_y = (HEIGHT // 2 // CELL_SIZE) * CELL_SIZE
    snake_coords = [(start_x, start_y)]
    direction = (0, CELL_SIZE) 
    score = 0
    score_label.text = "Score: 0"
    food_coord = get_random_food()

def get_random_food():
    cols, rows = WIDTH // CELL_SIZE, HEIGHT // CELL_SIZE
    x = random.randint(0, cols - 1) * CELL_SIZE
    y = random.randint(0, rows - 1) * CELL_SIZE
    while (x, y) in snake_coords:
        x = random.randint(0, cols - 1) * CELL_SIZE
        y = random.randint(0, rows - 1) * CELL_SIZE
    return (x, y)

def set_direction(new_dx, new_dy):
    global direction
    # Prevent the snake from reversing directly into itself
    if direction != (-new_dx, -new_dy):
        direction = (new_dx, new_dy)

# --- Keyboard Events ---
@window.event
def on_key_press(symbol, modifiers):
    global current_state
    
    if current_state == STATE_START and symbol == pyglet.window.key.SPACE:
        reset_game()
        current_state = STATE_PLAYING
        return
        
    if current_state == STATE_GAMEOVER:
        if symbol == pyglet.window.key.R:
            reset_game()
            current_state = STATE_PLAYING
            return
        elif symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit() 
            return pyglet.event.EVENT_HANDLED

    if current_state == STATE_PLAYING:
        if symbol == pyglet.window.key.UP: set_direction(0, CELL_SIZE)
        elif symbol == pyglet.window.key.DOWN: set_direction(0, -CELL_SIZE)
        elif symbol == pyglet.window.key.LEFT: set_direction(-CELL_SIZE, 0)
        elif symbol == pyglet.window.key.RIGHT: set_direction(CELL_SIZE, 0)
        elif symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit() 
            return pyglet.event.EVENT_HANDLED

# --- Controller Events ---
if controller:
    @controller.event
    def on_button_press(ctrl, button_name):
        global current_state
        if current_state == STATE_START and button_name in ['a', 'start']:
            reset_game()
            current_state = STATE_PLAYING
        elif current_state == STATE_GAMEOVER:
            if button_name == 'start':
                reset_game()
                current_state = STATE_PLAYING
            elif button_name == 'b':
                pyglet.app.exit()
        elif current_state == STATE_PLAYING:
            if button_name == 'b':
                pyglet.app.exit()

    @controller.event
    def on_dpad_motion(ctrl, dpad):
        if current_state == STATE_PLAYING:
            if dpad.y > 0: set_direction(0, CELL_SIZE)
            elif dpad.y < 0: set_direction(0, -CELL_SIZE)
            elif dpad.x < 0: set_direction(-CELL_SIZE, 0)
            elif dpad.x > 0: set_direction(CELL_SIZE, 0)

    @controller.event
    def on_stick_motion(ctrl, stick_name, vec):
        if current_state == STATE_PLAYING and stick_name == "leftstick":
            # Check deadzone so resting thumb doesn't trigger movement
            if abs(vec.x) > 0.3 or abs(vec.y) > 0.3: 
                # Check if stick is pushed more Vertically or Horizontally
                if abs(vec.y) > abs(vec.x):
                    if vec.y > 0: set_direction(0, CELL_SIZE) # Up
                    else: set_direction(0, -CELL_SIZE) # Down
                else:
                    if vec.x > 0: set_direction(CELL_SIZE, 0) # Right
                    else: set_direction(-CELL_SIZE, 0) # Left

def update(dt):
    global snake_coords, food_coord, score, current_state

    if current_state != STATE_PLAYING:
        return

    new_x = (snake_coords[0][0] + direction[0]) % WIDTH
    new_y = (snake_coords[0][1] + direction[1]) % HEIGHT
    new_head = (new_x, new_y)

    if new_head in snake_coords:
        current_state = STATE_GAMEOVER
        return

    snake_coords.insert(0, new_head)

    if new_head == food_coord:
        score += 1
        score_label.text = f'Score: {score}'
        food_coord = get_random_food()
        if score % 20 == 0:
            trigger_message()
    else:
        snake_coords.pop()

@window.event
def on_draw():
    window.clear()
    if background_sprite:
        background_sprite.draw()
        
    grid_batch.draw()

    if current_state == STATE_START:
        start_label.draw()
    
    elif current_state == STATE_PLAYING or current_state == STATE_GAMEOVER:
        # Draw Food
        shapes.Rectangle(food_coord[0], food_coord[1], CELL_SIZE-1, CELL_SIZE-1, color=(255, 50, 50)).draw()
        
        if snake_coords:
            # Body
            for i in range(1, len(snake_coords)):
                x, y = snake_coords[i]
                taper = min(i, 8)
                size = CELL_SIZE - taper
                offset = taper // 2
                shapes.Rectangle(x + offset, y + offset, size - 1, size - 1, color=(200, 10, 10)).draw()
            
            # Head
            hx, hy = snake_coords[0]
            shapes.Rectangle(hx, hy, CELL_SIZE-1, CELL_SIZE-1, color=(255, 10, 10)).draw()
            
            # Eyes
            e_size = 3
            if direction == (CELL_SIZE, 0): # R
                shapes.Circle(hx+15, hy+14, e_size, color=(0,0,0)).draw()
                shapes.Circle(hx+15, hy+6, e_size, color=(0,0,0)).draw()
            elif direction == (-CELL_SIZE, 0): # L
                shapes.Circle(hx+5, hy+14, e_size, color=(0,0,0)).draw()
                shapes.Circle(hx+5, hy+6, e_size, color=(0,0,0)).draw()
            elif direction == (0, CELL_SIZE): # U
                shapes.Circle(hx+14, hy+15, e_size, color=(0,0,0)).draw()
                shapes.Circle(hx+6, hy+15, e_size, color=(0,0,0)).draw()
            else: # D
                shapes.Circle(hx+14, hy+5, e_size, color=(0,0,0)).draw()
                shapes.Circle(hx+6, hy+5, e_size, color=(0,0,0)).draw()

        score_label.draw()
        
        # Draw fading motivational message
        if fade_alpha > 0:
            fade_label.draw()
        
        if current_state == STATE_GAMEOVER:
            # Semi-transparent overlay for Game Over
            shapes.Rectangle(0, 0, WIDTH, HEIGHT, color=(0, 0, 0, 150)).draw()
            game_over_label.draw()

pyglet.clock.schedule_interval(update, 1/10.0)

if __name__ == "__main__":
    pyglet.app.run()