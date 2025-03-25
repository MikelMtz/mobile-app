import os
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.app import App

# Define path to styles folder
KV_PATH = os.path.join(os.path.dirname(__file__), "styling")

# Load KV files
Builder.load_file(os.path.join(KV_PATH, "menu_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "task_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "spotify_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "password_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "password_list_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "password_details_style.kv"))

from Screens.TaskScreen import TaskScreen
from Screens.SpotifyScreen import SpotifyScreen
from Screens.PasswordScreen import PasswordScreen
from Screens.PasswordListScreen import PasswordListScreen
from Screens.PasswordDetailsScreen import PasswordDetailsScreen

class MenuScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager  # Keep reference to switch screens if needed

class AssistantApp(App):
    def build(self):
        screen_manager = ScreenManager()

        # Add screens
        screen_manager.add_widget(MenuScreen(screen_manager, name="menu"))
        screen_manager.add_widget(TaskScreen(screen_manager, name="tasks"))
        screen_manager.add_widget(PasswordScreen(screen_manager, name="password_entry"))
        screen_manager.add_widget(PasswordListScreen(name="password_list"))
        screen_manager.add_widget(SpotifyScreen(screen_manager, name="spotify"))
        screen_manager.add_widget(PasswordDetailsScreen(name="password_details"))  # Add details screen

        return screen_manager

if __name__ == "__main__":
    AssistantApp().run()
