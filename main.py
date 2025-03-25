import matplotlib.pyplot as plt
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
import spotify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import speech_recognition as sr
import os
import json
import subprocess
from kivy.uix.gridlayout import GridLayout
from cryptography.fernet import Fernet
from encryption import encrypt_password, decrypt_password
from kivy.lang import Builder
from kivy.properties import ObjectProperty

# Define path to styles folder
KV_PATH = os.path.join(os.path.dirname(__file__), "styling")

# Load KV files
Builder.load_file(os.path.join(KV_PATH, "menu_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "task_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "spotify_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "password_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "password_list_style.kv"))
Builder.load_file(os.path.join(KV_PATH, "password_details_style.kv"))


TASKS_FILE = "tasks.json"
PASSWORDS_FILE = "passwords.json"
# The MASTER password was encryoted with the same method as the ones stored in passwords.json, with the master KEY in key.key. 
# After encrypting it, the result was copied as the master key, which is decrypted each time the page is accessed
MASTER_PASSWORD = 'gAAAAABnq4El7cvRE-m8Tbx3Ac-ckyC4KPRuPl0Pp_x539Pwgd5Xzw-wHZfQBvvC5sdVBVwmFXNIrIHS7Hv8U4vX32R-bnE-RQ=='

# Spotify credentials (replace with your actual credentials)
SPOTIFY_CLIENT_ID = "daf24c1efe184fb6b056e834165b3369"
SPOTIFY_CLIENT_SECRET = "54505bf04599425981d87f0fe42136d2"
SPOTIFY_REDIRECT_URI = "http://localhost:5000/callback"

class SpotifyScreen(Screen):
    message_label = ObjectProperty(None)

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.sp = None  # Spotify client

    def connect_to_spotify(self):
        try:
            # Open Spotify app in the background
            subprocess.Popen(["spotify"])  # Opens the Spotify app in the background

            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="user-modify-playback-state user-read-playback-state"
            ))
            self.message_label.text = "Connected to Spotify!"
        except Exception as e:
            self.message_label.text = f"Error: {str(e)}"

    def play_song_by_voice(self):
        if not self.sp:
            self.message_label.text = "Please connect to Spotify first!"
            return

        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        popup = Popup(title="Listening...",
                      content=Label(text="Speak the song name"),
                      size_hint=(0.6, 0.4))
        popup.open()

        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
                popup.dismiss()

            command = recognizer.recognize_google(audio).lower()
            self.message_label.text = f"You said: {command}"

            results = self.sp.search(q=command, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                self.sp.start_playback(uris=[track['uri']])
                self.message_label.text = f"Playing: {track['name']} by {track['artists'][0]['name']}"
            else:
                self.message_label.text = "Song not found!"
        except sr.UnknownValueError:
            self.message_label.text = "Sorry, I didn't understand that."
        except sr.RequestError as e:
            self.message_label.text = f"Speech recognition error: {str(e)}"
        except Exception as e:
            self.message_label.text = f"Error: {str(e)}"
class TaskScreen(Screen):
    task_input = ObjectProperty(None)
    task_layout = ObjectProperty(None)

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.tasks = self.load_tasks()
        self.display_tasks()

    def add_task(self):
        task_text = self.task_input.text.strip()
        if task_text:
            self.tasks.append(task_text)
            self.display_tasks()
            self.save_tasks()
            self.task_input.text = ""

    def delete_task(self, task_box, task_text):
        if task_text in self.tasks:
            self.tasks.remove(task_text)
        self.task_layout.remove_widget(task_box)
        self.save_tasks()

    def display_tasks(self):
        self.task_layout.clear_widgets()
        for task in self.tasks:
            task_box = self.create_task_box(task)
            self.task_layout.add_widget(task_box)

    def create_task_box(self, task):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button

        task_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, padding=(5, 0))
        task_label = Label(text=f"• {task}", size_hint_x=0.8, halign='left', valign='middle', color=(0,0,0,1))
        task_label.bind(size=task_label.setter('text_size'))
        task_box.add_widget(task_label)

        delete_button = Button(text="Delete", size_hint_x=0.2)
        delete_button.bind(on_press=lambda btn, tb=task_box, t=task: self.delete_task(tb, t))
        task_box.add_widget(delete_button)

        return task_box

    def load_tasks(self):
        if os.path.exists(TASKS_FILE):
            try:
                with open(TASKS_FILE, "r") as file:
                    return json.load(file)
            except Exception as e:
                print("Error loading tasks:", e)
        return []

    def save_tasks(self):
        try:
            with open(TASKS_FILE, "w") as file:
                json.dump(self.tasks, file, indent=4)
        except Exception as e:
            print("Error saving tasks:", e)
class PasswordScreen(Screen):
    master_password_input = ObjectProperty(None)
    message_label = ObjectProperty(None)
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager

    def check_password(self, instance=None):
        if self.master_password_input.text == decrypt_password(MASTER_PASSWORD):
            self.master_password_input.text = ""  # Clear input field
            self.remove_master_password()
            self.screen_manager.current = "password_list"
        else:
            self.message_label.text = "Invalid password!"

    def remove_master_password(self):
        if os.path.exists(PASSWORDS_FILE):
            try:
                with open(PASSWORDS_FILE, "r") as file:
                    data = json.load(file)
                
                if "master" in data:
                    del data["master"]
                    with open(PASSWORDS_FILE, "w") as file:
                        json.dump(data, file, indent=4)
            except Exception as e:
                print("Error updating password file:", e)
class PasswordListScreen(Screen):
    password_list_layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.passwords = self.load_passwords()  # Load stored passwords
        self.display_passwords()  # Display them


    def display_passwords(self):
        """
        Create buttons for each stored password.
        """
        self.password_list_layout.clear_widgets()  # Clear previous entries

        for platform, credentials in self.passwords.items():
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50)

            # Platform button (opens details screen)
            btn = Button(
                text=platform,
                size_hint_x=0.7,
                color=(0, 0, 0, 1),  # Black text
                background_color=(0.7, 0.9, 1, 1)  # Light blue background
            )
            btn.bind(on_press=lambda instance, p=platform: self.show_details_screen(p))
            row.add_widget(btn)

            # Delete button
            delete_btn = Button(
                text="Delete",
                size_hint_x=0.3,
                background_color=(1, 0, 0, 1)  # Red button
            )
            delete_btn.bind(on_press=lambda instance, p=platform: self.delete_password(p))
            row.add_widget(delete_btn)

            self.password_list_layout.add_widget(row)  # Add the row to the list

    def show_add_password_popup(self, instance=None):
        """Popup to add a new password with improved styling."""
        
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Styled text inputs
        platform_input = TextInput(
            hint_text="Platform",
            size_hint_y=None,
            height=50,
            foreground_color=(0, 0, 0, 1),  # Black text
            background_color=(1, 1, 1, 1)   # White background
        )

        username_input = TextInput(
            hint_text="Username",
            size_hint_y=None,
            height=50,
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1)
        )

        password_input = TextInput(
            hint_text="Password",
            size_hint_y=None,
            height=50,
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1)
        )

        # Styled Save button
        save_button = Button(
            text="Save",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 1, 1)  # Blue background
        )
        save_button.bind(on_press=lambda x: self.add_password(platform_input.text, username_input.text, password_input.text))

        # Adding widgets
        popup_layout.add_widget(platform_input)
        popup_layout.add_widget(username_input)
        popup_layout.add_widget(password_input)
        popup_layout.add_widget(save_button)

        # Popup window
        popup = Popup(
            title="Add a New Password",
            title_size=20,
            title_color=(0, 0, 0, 1),  # Black title
            content=popup_layout,
            size_hint=(0.8, 0.5)
        )

        # Close popup after saving
        save_button.bind(on_press=lambda x: popup.dismiss())

        popup.open()



    def show_details_screen(self, platform):
        """Navigate to PasswordDetailsScreen and display details."""
        details_screen = self.manager.get_screen("password_details")
        details_screen.display_details(platform, self.passwords[platform])
        self.manager.current = "password_details"

    def add_password(self, platform, username, password):
        """Save new password and refresh list."""
        if platform and username and password:
            self.passwords[platform] = {"username": username, "password": encrypt_password(password)}
            self.save_passwords()
            self.display_passwords()

    def delete_password(self, platform):
        """Delete a stored password and refresh list."""
        if platform in self.passwords:
            del self.passwords[platform]
            self.save_passwords()
            self.display_passwords()

    def load_passwords(self):
        """Load passwords from a file."""
        if os.path.exists(PASSWORDS_FILE):
            try:
                with open(PASSWORDS_FILE, "r") as file:
                    return json.load(file)
            except Exception as e:
                print("Error loading passwords:", e)
        return {}

    def save_passwords(self):
        """Save passwords to a file."""
        try:
            with open(PASSWORDS_FILE, "w") as file:
                json.dump(self.passwords, file, indent=4)
        except Exception as e:
            print("Error saving passwords:", e)
class PasswordDetailsScreen(Screen):
    platform_label = ObjectProperty(None)
    username_label = ObjectProperty(None)
    password_label = ObjectProperty(None)

    def display_details(self, platform, credentials):
        """Update screen with password details."""
        self.platform = platform  # Store for deletion
        self.platform_label.text = f"Platform: {platform}"
        self.username_label.text = f"Username: {credentials['username']}"
        self.password_label.text = f"Password: {decrypt_password(credentials['password'])}"

    def delete_password(self):
        """Delete password and return to list."""
        password_screen = self.manager.get_screen("password_list")
        password_screen.delete_password(self.platform)
        self.manager.current = "password_list"
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