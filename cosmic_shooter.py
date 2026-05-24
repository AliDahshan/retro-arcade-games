import pyglet
import pyglet.gl
import pyglet.shapes
import pyglet.sprite
import pyglet.text
from pyglet.window import key
import pyglet.input
import random
import os

WIDTH, HEIGHT = 800, 600
pyglet.options['dpi_scaling'] = 'scaled'
window = pyglet.window.Window(WIDTH, HEIGHT, "Cosmic Shooter Local Co-Op")

# Input States for Keyboard
pressed_keys = {}

# --- Controller Setup ---
controllers = pyglet.input.get_controllers()
c1, c2 = None, None

p1_ctrl_keys = {'up': False, 'down': False, 'left': False, 'right': False}
p2_ctrl_keys = {'up': False, 'down': False, 'left': False, 'right': False}

if len(controllers) > 0:
    c1 = controllers[0]
    c1.open()
    print(f"Player 1 Controller connected: {c1.name}")
if len(controllers) > 1:
    c2 = controllers[1]
    c2.open()
    print(f"Player 2 Controller connected: {c2.name}")

@window.event
def on_resize(width, height):
    pyglet.gl.glViewport(0, 0, *window.get_framebuffer_size())
    window.projection = pyglet.math.Mat4.orthogonal_projection(0, WIDTH, 0, HEIGHT, -1, 1)
    return pyglet.event.EVENT_HANDLED

@window.event
def on_deactivate():
    pressed_keys.clear()
    for k in p1_ctrl_keys: p1_ctrl_keys[k] = False
    for k in p2_ctrl_keys: p2_ctrl_keys[k] = False

def scale_sprite(sprite, w, h):
    sprite.scale_x = w / sprite.image.width
    sprite.scale_y = h / sprite.image.height

def load_img(name, size):
    try:
        current_folder = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(current_folder, "assets", f"{name}.png")
        return pyglet.image.load(img_path)
    except Exception:
        color = (255, 50, 50, 255) if ("enemy" in name or "chicken" in name) else (255, 255, 255, 255)
        pattern = pyglet.image.SolidColorImagePattern(color)
        return pattern.create_image(*size)

# Load Assets
bg_img = load_img("background", (WIDTH, HEIGHT))
player_img = load_img("airship", (50, 50))
enemy_img = load_img("enemy", (120, 120))
chicken_img = load_img("chicken", (120, 120))

# ADD THIS: Load a list of boss images
boss_imgs = [
    load_img("boss1", (200, 200)),
    load_img("boss2", (200, 200)),
    load_img("boss3", (200, 200)),
    load_img("boss4", (200, 200))
]

bg_sprite1 = pyglet.sprite.Sprite(bg_img, x=0, y=0)
bg_sprite2 = pyglet.sprite.Sprite(bg_img, x=0, y=HEIGHT)
scale_sprite(bg_sprite1, WIDTH, HEIGHT)
scale_sprite(bg_sprite2, WIDTH, HEIGHT)

def colliderect(rect1, rect2):
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

# --- Classes ---
class Player:
    def __init__(self, x, y, tint=(255, 255, 255)):
        self.x, self.y, self.w, self.h = x, y, 50, 50
        self.sprite = pyglet.sprite.Sprite(player_img, x=x, y=y)
        self.sprite.color = tint
        scale_sprite(self.sprite, self.w, self.h)
        self.weapon_level = 1
        self.alive = True

    def fire(self):
        if not self.alive: return
        px, py = self.x, self.y
        if self.weapon_level == 1: 
            bullets.append(Bullet(px, py))
        elif self.weapon_level == 2:
            bullets.extend([Bullet(px - 10, py), Bullet(px + 10, py)])
        elif self.weapon_level == 3:
            bullets.extend([Bullet(px, py), Bullet(px - 15, py, dx=-2), Bullet(px + 15, py, dx=2)])
        elif self.weapon_level == 4:
            bullets.extend([
                Bullet(px - 10, py), Bullet(px + 10, py), 
                Bullet(px - 20, py, dx=-3), Bullet(px + 20, py, dx=3)
            ])
        elif self.weapon_level == 5:
            bullets.extend([
                Bullet(px, py), 
                Bullet(px - 15, py, dx=-2), Bullet(px + 15, py, dx=2), 
                Bullet(px - 25, py, dx=-4), Bullet(px + 25, py, dx=4)
            ])
        elif self.weapon_level >= 6:
            bullets.extend([
                Bullet(px - 10, py), Bullet(px + 10, py), 
                Bullet(px - 20, py, dx=-2), Bullet(px + 20, py, dx=2), 
                Bullet(px - 30, py, dx=-5), Bullet(px + 30, py, dx=5)
            ])
            
    def update_pos(self):
        self.x = max(0, min(self.x, WIDTH - self.w))
        self.y = max(0, min(self.y, HEIGHT - self.h))
        self.sprite.x, self.sprite.y = self.x, self.y

    def draw(self):
        if self.alive: self.sprite.draw()

class Bullet:
    def __init__(self, x, y, dx=0):
        self.x, self.y, self.w, self.h, self.dx = x + 22, y + 50, 6, 12, dx
        self.shape = pyglet.shapes.Rectangle(self.x, self.y, self.w, self.h, color=(255, 255, 0))
    def update(self):
        self.y += 8
        self.x += self.dx
        self.shape.x, self.shape.y = self.x, self.y
    def draw(self): self.shape.draw()

class PowerUp:
    def __init__(self, x, y):
        self.x, self.y, self.w, self.h = x, y, 20, 20
        self.shape = pyglet.shapes.Rectangle(self.x, self.y, self.w, self.h, color=(0, 255, 0))
    def update(self):
        self.y -= 3
        self.shape.y = self.y
    def draw(self): self.shape.draw()

class EnemyAttack:
    def __init__(self, x, y, speed=4, color=(255,0,0)):
        self.x, self.y, self.w, self.h = x, y, 15, 15
        self.speed = speed
        self.shape = pyglet.shapes.Rectangle(self.x, self.y, self.w, self.h, color=color)
    def update(self):
        self.y -= self.speed
        self.shape.y = self.y
    def draw(self): self.shape.draw()

class Enemy:
    def __init__(self, x, y, img, speed_boost, hp=1):
        self.x, self.y, self.w, self.h = x, y, 50, 50
        self.sprite = pyglet.sprite.Sprite(img, x=x, y=y)
        scale_sprite(self.sprite, self.w, self.h)
        self.speed = random.uniform(1.5, 2.5) + speed_boost
        self.direction = 1
        self.hp = hp
        self.max_hp = hp
    def take_hit(self):
        self.hp -= 1
        if self.hp > 0 and self.max_hp > 1:
            ratio = self.hp / self.max_hp
            tint = int(255 * (1 - ratio * 0.5))
            self.sprite.color = (tint, tint, tint)
        return self.hp <= 0
    def update(self):
        self.x += self.speed * self.direction
        if self.x + self.w >= WIDTH or self.x <= 0:
            self.direction *= -1
            self.y -= 30
        self.sprite.x, self.sprite.y = self.x, self.y
    def draw(self): self.sprite.draw()

class Boss(Enemy):
    def __init__(self, x, y, img, name, hp):
        super().__init__(x, y, img, 0, hp)
        self.w, self.h = 200, 200
        scale_sprite(self.sprite, self.w, self.h)
        self.sprite.color = (255, 100, 255) # Tint boss purple
        self.name = name
        self.speed = 3
        
    def update(self):
        # Boss just moves side to side, doesn't drop down
        self.x += self.speed * self.direction
        if self.x + self.w >= WIDTH or self.x <= 0:
            self.direction *= -1
        self.sprite.x, self.sprite.y = self.x, self.y

# --- Difficulty & Wave Logic ---
MAX_DIFFICULTY_WAVE = 15

def get_difficulty(wave_num):
    t = min(wave_num, MAX_DIFFICULTY_WAVE) / MAX_DIFFICULTY_WAVE
    return {
        'speed_boost': t * 4.0,
        'enemy_hp': 1 + int(t * 4),
        'shoot_chance': 0.0007 + t * 0.003,
        'attack_speed': 4 + t * 6,
    }

def spawn_wave(wave_num):
    diff = get_difficulty(wave_num)
    
    # Boss Wave every 5 levels
    if wave_num % 5 == 0:
        boss_names = ["VOID HARBINGER", "WORLD EATER", "STAR CRUSHER", "COSMIC OVERLORD"]
        name_idx = (wave_num // 5 - 1) % len(boss_names)
        boss_hp = 50 + (wave_num * 10) # 100 HP at wave 5, 150 at wave 10...
        
        # Grab the matching image from your new list
        current_boss_img = boss_imgs[name_idx % len(boss_imgs)]
        
        return [Boss(WIDTH // 2 - 100, HEIGHT - 220, current_boss_img, boss_names[name_idx], boss_hp)]
    
    # Regular Wave
    return [Enemy(x * 80 + 80, HEIGHT - (y * 70 + 100),
                  random.choice([enemy_img, chicken_img]),
                  diff['speed_boost'], diff['enemy_hp'])
            for y in range(3) for x in range(8)]

# Game States: "MENU", "PLAYING", "GAME_OVER"
game_state = "MENU"
menu_selection = 1  
num_players = 1

# Players
p1 = Player(WIDTH // 3 - 25, 70, tint=(255, 255, 255)) 
p2 = Player((WIDTH // 3) * 2 - 25, 70, tint=(150, 200, 255)) 

# Entities & Stats
bullets, powerups, enemy_attacks = [], [], []
wave, score, bg_y = 1, 0, 0
enemies = []
boss_death_msg_timer = 0.5 # Tracks how long the "GOD HAS FALLEN" text stays on screen

# --- Labels ---
title_label = pyglet.text.Label("COSMIC SHOOTER", font_name="Arial", font_size=48, x=WIDTH//2, y=HEIGHT - 120, anchor_x="center", anchor_y="center")
opt1_label = pyglet.text.Label("1 PLAYER", font_name="Arial", font_size=32, x=WIDTH//2, y=HEIGHT//2 + 40, anchor_x="center", anchor_y="center")
opt2_label = pyglet.text.Label("2 PLAYERS", font_name="Arial", font_size=32, x=WIDTH//2, y=HEIGHT//2 - 20, anchor_x="center", anchor_y="center")

controls_text = (
    "CONTROLS\n"
    "--------------------\n"
    "Player 1 (White) - Move: Arrow Keys | Shoot: Space\n"
    "Player 2 (Blue) - Move: W A S D | Shoot: L/R Shift\n\n"
    "Press ENTER to Start"
)
controls_label = pyglet.text.Label(controls_text, font_name="Arial", font_size=16, x=WIDTH//2, y=140, anchor_x="center", anchor_y="center", width=700, multiline=True, align="center")

score_label = pyglet.text.Label("", font_name="Arial", font_size=20, x=10, y=HEIGHT - 10, anchor_x="left", anchor_y="top")
game_over_label = pyglet.text.Label("MISSION FAILED", font_name="Arial", font_size=64, x=WIDTH//2, y=HEIGHT//2 + 50, anchor_x="center", anchor_y="center", color=(255, 50, 50, 255))
retry_label = pyglet.text.Label("Final Score: 0 | Press 'R' to Return to Menu", font_name="Arial", font_size=24, x=WIDTH//2, y=HEIGHT//2 - 30, anchor_x="center", anchor_y="center")

# Boss Death Label
god_fallen_label = pyglet.text.Label("A GOD HAS FALLEN", font_name="Arial", font_size=48, x=WIDTH//2, y=HEIGHT//2, anchor_x="center", anchor_y="center", color=(255, 215, 0, 255))

def start_game():
    global bullets, powerups, enemy_attacks, wave, enemies, score, game_state, boss_death_msg_timer
    if num_players == 1:
        p1.__init__(WIDTH // 2 - 25, 70, tint=(255, 255, 255))
        p2.alive = False
    else:
        p1.__init__(WIDTH // 3 - 25, 70, tint=(255, 255, 255))
        p2.__init__((WIDTH // 3) * 2 - 25, 70, tint=(150, 200, 255))
        
    bullets, powerups, enemy_attacks = [], [], []
    wave, score, boss_death_msg_timer = 1, 0, 0
    enemies = spawn_wave(wave)
    game_state = "PLAYING"

def update(dt):
    global wave, enemies, score, bg_y, game_state, boss_death_msg_timer
    
    bg_y = bg_y - 2 if bg_y > -HEIGHT else 0
        
    if game_state != "PLAYING": return
        
    # Handle the boss death sequence delay
    if boss_death_msg_timer > 0:
        boss_death_msg_timer -= 1
        
    # --- Movement ---
    move_speed = 6
    if p1.alive:
        if pressed_keys.get(key.LEFT) or p1_ctrl_keys['left']: p1.x -= move_speed
        if pressed_keys.get(key.RIGHT) or p1_ctrl_keys['right']: p1.x += move_speed
        if pressed_keys.get(key.UP) or p1_ctrl_keys['up']: p1.y += move_speed
        if pressed_keys.get(key.DOWN) or p1_ctrl_keys['down']: p1.y -= move_speed
        p1.update_pos()
        
    if p2.alive:
        if pressed_keys.get(key.A) or p2_ctrl_keys['left']: p2.x -= move_speed
        if pressed_keys.get(key.D) or p2_ctrl_keys['right']: p2.x += move_speed
        if pressed_keys.get(key.W) or p2_ctrl_keys['up']: p2.y += move_speed
        if pressed_keys.get(key.S) or p2_ctrl_keys['down']: p2.y -= move_speed
        p2.update_pos()
    
    # Update Bullets & Collisions
    for b in bullets[:]:
        b.update()
        if b.y > HEIGHT or b.x < 0 or b.x > WIDTH:
            bullets.remove(b)
        else:
            for e in enemies[:]:
                if colliderect((b.x, b.y, b.w, b.h), (e.x, e.y, e.w, e.h)):
                    if b in bullets: bullets.remove(b)
                    if e in enemies:
                        dead = e.take_hit()
                        if dead:
                            if isinstance(e, Boss):
                                boss_death_msg_timer = 180 # Flash message for 3 seconds (60fps * 3)
                                score += 5000
                                # Guarantee some powerups drop from the boss
                                for _ in range(3): powerups.append(PowerUp(e.x + random.randint(0, e.w), e.y))
                            else:
                                if random.random() < 0.15: powerups.append(PowerUp(e.x, e.y))
                                score += 100
                            enemies.remove(e)
                    break
                    
    active_players = [p for p in (p1, p2) if p.alive]
    
    # Update Powerups
    for p_up in powerups[:]:
        p_up.update()
        if p_up.y + p_up.h < 0: 
            powerups.remove(p_up)
            continue
        for player in active_players:
            if colliderect((p_up.x, p_up.y, p_up.w, p_up.h), (player.x, player.y, player.w, player.h)):
                player.weapon_level = min(player.weapon_level + 1, 6)
                if p_up in powerups: powerups.remove(p_up)
                break
            
    # Update Enemy Attacks & Player Death
    for attack in enemy_attacks[:]:
        attack.update()
        if attack.y + attack.h < 0: 
            enemy_attacks.remove(attack)
            continue
        for player in active_players:
            if colliderect((attack.x, attack.y, attack.w, attack.h), (player.x, player.y, player.w, player.h)):
                player.alive = False
                if attack in enemy_attacks: enemy_attacks.remove(attack)
                break
                
    # Update Enemies & Crash Collision
    diff = get_difficulty(wave)
    for e in enemies:
        e.update()
        
        # Enemy Shooting Logic (Boss shoots a 3-way spread frequently)
        if isinstance(e, Boss):
            if random.random() < diff['shoot_chance'] * 8: # Shoots much more often
                atk_spd = diff['attack_speed']
                # Middle, Left angled, Right angled bullets
                enemy_attacks.extend([
                    EnemyAttack(e.x + e.w//2, e.y, speed=atk_spd, color=(255,100,0)),
                    EnemyAttack(e.x + e.w//2 - 40, e.y, speed=atk_spd, color=(255,100,0)),
                    EnemyAttack(e.x + e.w//2 + 40, e.y, speed=atk_spd, color=(255,100,0))
                ])
        else:
            if random.random() < diff['shoot_chance']:
                enemy_attacks.append(EnemyAttack(e.x + e.w//2 - 7, e.y, speed=diff['attack_speed']))
        
        for player in active_players:
            if colliderect((e.x, e.y, e.w, e.h), (player.x, player.y, player.w, player.h)):
                player.alive = False
        
        if e.y <= 0 and not isinstance(e, Boss): # Boss doesn't trigger crash
            p1.alive = False
            p2.alive = False
            
    # Check Game Over State
    if num_players == 1:
        if not p1.alive: game_state = "GAME_OVER"
    else:
        if not p1.alive and not p2.alive: game_state = "GAME_OVER"
            
    # Only spawn the next wave if there are no enemies left AND the death timer is finished
    if not enemies and game_state == "PLAYING" and boss_death_msg_timer <= 0:
        wave += 1
        enemies = spawn_wave(wave)

pyglet.clock.schedule_interval(update, 1/60.0)

# --- Events ---
@window.event
def on_key_press(symbol, modifiers):
    global game_state, menu_selection, num_players
    pressed_keys[symbol] = True
    
    if game_state == "MENU":
        if symbol in [key.UP, key.W]:
            menu_selection = 1
        elif symbol in [key.DOWN, key.S]:
            menu_selection = 2
        elif symbol in [key.ENTER, key.SPACE]:
            num_players = menu_selection
            start_game()
            
    elif game_state == "PLAYING":
        if symbol == key.SPACE: p1.fire()
        if symbol in [key.LSHIFT, key.RSHIFT]: p2.fire()
        
    elif game_state == "GAME_OVER":
        if symbol == key.R: 
            game_state = "MENU"

@window.event
def on_key_release(symbol, modifiers):
    pressed_keys[symbol] = False

# --- Controller Event Listeners ---
if c1:
    @c1.event
    def on_button_press(ctrl, button_name):
        global game_state, num_players
        if game_state == "MENU" and button_name in ['a', 'start']:
            num_players = menu_selection
            start_game()
        elif game_state == "PLAYING" and button_name in ['a', 'x']: 
            p1.fire()
        elif game_state == "GAME_OVER" and button_name == 'start': 
            game_state = "MENU"

    @c1.event
    def on_dpad_motion(ctrl, dpad):
        global menu_selection
        if game_state == "MENU":
            if dpad.y > 0: menu_selection = 1
            elif dpad.y < 0: menu_selection = 2
        p1_ctrl_keys['left'] = dpad.x < 0
        p1_ctrl_keys['right'] = dpad.x > 0
        p1_ctrl_keys['up'] = dpad.y > 0
        p1_ctrl_keys['down'] = dpad.y < 0

    @c1.event
    def on_stick_motion(ctrl, stick_name, vec):
        if stick_name == "leftstick":
            p1_ctrl_keys['left'] = vec.x < -0.2
            p1_ctrl_keys['right'] = vec.x > 0.2
            p1_ctrl_keys['up'] = vec.y > 0.2
            p1_ctrl_keys['down'] = vec.y < -0.2

if c2:
    @c2.event
    def on_button_press(ctrl, button_name):
        if game_state == "PLAYING" and button_name in ['a', 'x']: p2.fire()

    @c2.event
    def on_dpad_motion(ctrl, dpad):
        p2_ctrl_keys['left'] = dpad.x < 0
        p2_ctrl_keys['right'] = dpad.x > 0
        p2_ctrl_keys['up'] = dpad.y > 0
        p2_ctrl_keys['down'] = dpad.y < 0

    @c2.event
    def on_stick_motion(ctrl, stick_name, vec):
        if stick_name == "leftstick":
            p2_ctrl_keys['left'] = vec.x < -0.2
            p2_ctrl_keys['right'] = vec.x > 0.2
            p2_ctrl_keys['up'] = vec.y > 0.2
            p2_ctrl_keys['down'] = vec.y < -0.2

@window.event
def on_draw():
    window.clear()
    bg_sprite1.y, bg_sprite2.y = bg_y, bg_y + HEIGHT
    bg_sprite1.draw()
    bg_sprite2.draw()
    
    if game_state == "MENU":
        title_label.draw()
        if menu_selection == 1:
            opt1_label.color = (255, 255, 0, 255)
            opt2_label.color = (255, 255, 255, 255)
        else:
            opt1_label.color = (255, 255, 255, 255)
            opt2_label.color = (255, 255, 0, 255)
            
        opt1_label.draw()
        opt2_label.draw()
        controls_label.draw()
        
    elif game_state in ["PLAYING", "GAME_OVER"]:
        if p1.alive: p1.draw()
        if p2.alive: p2.draw()
            
        for b in bullets: b.draw()
        for p_up in powerups: p_up.draw()
        for attack in enemy_attacks: attack.draw()
        
        for e in enemies: 
            e.draw()
            
            # Draw Boss UI Elements
            if isinstance(e, Boss):
                # Boss Name
                pyglet.text.Label(e.name, font_name="Arial", font_size=18, x=WIDTH//2, y=HEIGHT - 30, anchor_x="center", anchor_y="center", color=(255,100,255,255)).draw()
                
                # Boss Health Bar (Red background, Green foreground)
                bar_w, bar_h = 400, 15
                bar_x, bar_y = WIDTH//2 - bar_w//2, HEIGHT - 55
                pyglet.shapes.Rectangle(bar_x, bar_y, bar_w, bar_h, color=(100, 0, 0)).draw()
                
                hp_ratio = max(0, e.hp / e.max_hp)
                if hp_ratio > 0:
                    pyglet.shapes.Rectangle(bar_x, bar_y, bar_w * hp_ratio, bar_h, color=(0, 255, 0)).draw()
        
        # If the boss just died, draw the message
        if boss_death_msg_timer > 0:
            god_fallen_label.draw()
            
        p1_status = f"Pwr: {p1.weapon_level}" if p1.alive else "DEAD"
        p2_status = f"Pwr: {p2.weapon_level}" if p2.alive else "DEAD"
        
        if num_players == 1:
            score_label.text = f"Score: {score} | Wave: {wave} | P1 {p1_status}"
        else:
            score_label.text = f"Score: {score} | Wave: {wave} | P1 {p1_status} | P2 {p2_status}"
            
        score_label.draw()
        
        if game_state == "GAME_OVER":
            retry_label.text = f"Final Score: {score} | Press 'R' to Return to Menu"
            game_over_label.draw()
            retry_label.draw()

if __name__ == "__main__":
    pyglet.app.run()