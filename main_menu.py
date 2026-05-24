import pyglet
from pyglet.window import key
import pyglet.input
import subprocess
import sys
import os

class GameLauncher(pyglet.window.Window):
    def __init__(self):
        super().__init__(width=800, height=600, caption="Arcade Hub")
        
        self.selected_index = 0
        self.stick_in_neutral = True # Prevents rapid scrolling
        
        self.games = [
            {"name": "Cosmic Shooter", "file": "cosmic_shooter.py"},
            {"name": "Snake Xenzia", "file": "snake_2.py"}
        ]
        
        self.title_label = pyglet.text.Label('MAIN MENU', font_size=36, x=400, y=450, anchor_x='center')
        self.instruction_label = pyglet.text.Label('Use Stick/D-PAD to select, A to play', font_size=14, x=400, y=180, anchor_x='center', color=(150, 150, 150, 255))
        self.quit_label = pyglet.text.Label('Press B or ESC to Quit', font_size=14, x=400, y=150, anchor_x='center', color=(100, 100, 100, 255))

        self.option_labels = [pyglet.text.Label(g["name"], font_size=24, x=400, y=300 - (i * 60), anchor_x='center') for i, g in enumerate(self.games)]

        # --- Controller Setup ---
        controllers = pyglet.input.get_controllers()
        if controllers:
            self.controller = controllers[0]
            self.controller.open()
            self.controller.push_handlers(self)
            print(f"Controller connected: {self.controller.name}")
        else:
            self.controller = None
            print("No controller found. Using keyboard fallback.")

    def move_up(self):
        self.selected_index -= 1
        if self.selected_index < 0:
            self.selected_index = len(self.games) - 1
            
    def move_down(self):
        self.selected_index += 1
        if self.selected_index >= len(self.games):
            self.selected_index = 0

    def confirm_selection(self):
        self.launch_game(self.games[self.selected_index]["file"])

    # --- Controller Input Handlers ---
    def on_button_press(self, controller, button_name):
        if button_name == 'dpup': self.move_up()
        elif button_name == 'dpdown': self.move_down()
        elif button_name in ['a', 'start']: self.confirm_selection()
        elif button_name == 'b': pyglet.app.exit()

    # --- Controller Input Handlers ---
    def on_button_press(self, controller, button_name):
        if button_name == 'dpup': self.move_up()
        elif button_name == 'dpdown': self.move_down()
        elif button_name in ['a', 'start']: self.confirm_selection()
        elif button_name == 'b': pyglet.app.exit()

    def on_dpad_motion(self, controller, dpad):
        # dpad is now a Vec2(x, y) object
        if dpad.y > 0: self.move_up()
        elif dpad.y < 0: self.move_down()

    def on_stick_motion(self, controller, stick_name, vec):
        # vec is now a Vec2(x, y) object
        if stick_name == "leftstick":
            if vec.y > 0.5 and self.stick_in_neutral:
                self.move_up()
                self.stick_in_neutral = False
            elif vec.y < -0.5 and self.stick_in_neutral:
                self.move_down()
                self.stick_in_neutral = False
            elif -0.2 < vec.y < 0.2: # Stick returned to center
                self.stick_in_neutral = True

    # --- Keyboard Input Handlers ---
    def on_key_press(self, symbol, modifiers):
        if symbol == key.UP: self.move_up()
        elif symbol == key.DOWN: self.move_down()
        elif symbol in (key.ENTER, key.RETURN): self.confirm_selection()
        elif symbol == key.ESCAPE:
            pyglet.app.exit() 
            return pyglet.event.EVENT_HANDLED

    def launch_game(self, filename):
        self.set_visible(False) 
        full_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        try:
            subprocess.run([sys.executable, full_file_path], check=True)
        except Exception as e:
            print(f"Error launching '{filename}': {e}")
        self.set_visible(True)

    def on_draw(self):
        self.clear() 
        self.title_label.draw()
        self.instruction_label.draw()
        self.quit_label.draw()

        for i, label in enumerate(self.option_labels):
            if i == self.selected_index:
                label.color = (255, 255, 50, 255) 
                label.text = f">  {self.games[i]['name']}  <"
            else:
                label.color = (150, 150, 150, 255) 
                label.text = self.games[i]['name']
            label.draw()

if __name__ == '__main__':
    window = GameLauncher()
    pyglet.app.run()