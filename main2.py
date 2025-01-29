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
import platform
import sqlite3

# ---- Spotify Integration ----
SPOTIFY_CLIENT_ID = "daf24c1efe184fb6b056e834165b3369"
SPOTIFY_CLIENT_SECRET = "54505bf04599425981d87f0fe42136d2"
SPOTIFY_REDIRECT_URI = "http://localhost:5000/callback"


class SpotifyScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sp = None  # Spotify client

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Back button
        back_button = Button(text="Back to Main Menu", size_hint_y=None, height=50)
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'menu'))
        layout.add_widget(back_button)

        # Title
        layout.add_widget(Label(text="Spotify Connection", font_size=24, size_hint_y=None, height=50))

        # Authenticate Spotify
        connect_button = Button(text="Connect to Spotify", size_hint_y=None, height=50)
        connect_button.bind(on_press=self.connect_to_spotify)
        layout.add_widget(connect_button)

        # Voice command button
        voice_command_button = Button(text="Play Song by Voice Command", size_hint_y=None, height=50)
        voice_command_button.bind(on_press=self.play_song_by_voice)
        layout.add_widget(voice_command_button)

        # Message
        self.message_label = Label(size_hint_y=None, height=50)
        layout.add_widget(self.message_label)

        self.add_widget(layout)
    
    def open_spotify_app(self):
        if platform.system() == "Windows":
            os.system("start spotify")
        elif platform.system() == "Darwin":  # macOS
            os.system("open -a Spotify")
        elif platform.system() == "Linux":
            os.system("spotify &")

    def connect_to_spotify(self, instance):
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="user-modify-playback-state user-read-playback-state"
            ))
            
            # Open Spotify app first
            self.open_spotify_app()

            self.message_label.text = "Connected to Spotify!"
        except Exception as e:
            self.message_label.text = f"Error: {str(e)}"

    def play_song_by_voice(self, instance):
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

            # Recognize speech
            command = recognizer.recognize_google(audio).lower()
            self.message_label.text = f"You said: {command}"

            # Search for the song
            results = self.sp.search(q=command, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]

                # Get active device
                devices = self.sp.devices()
                if not devices["devices"]:
                    self.message_label.text = "No active device found! Open Spotify and try again."
                    return

                device_id = devices["devices"][0]["id"]

                # Start playing the song
                self.sp.start_playback(device_id=device_id, uris=[track['uri']])
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
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Back button
        back_button = Button(text="Back to Main Menu", size_hint_y=None, height=50)
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'menu'))
        layout.add_widget(back_button)

        # Title
        layout.add_widget(Label(text="Task List", font_size=24, size_hint_y=None, height=50))

        # Task input
        self.task_input = TextInput(hint_text="Add a new task", size_hint_y=None, height=50)
        layout.add_widget(self.task_input)

        # Add task button
        add_button = Button(text="Add Task", size_hint_y=None, height=50)
        add_button.bind(on_press=self.add_task)
        layout.add_widget(add_button)

        # Task list
        self.task_list = ScrollView(size_hint=(1, 1))
        self.task_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.task_layout.bind(minimum_height=self.task_layout.setter('height'))
        self.task_list.add_widget(self.task_layout)
        layout.add_widget(self.task_list)

        self.add_widget(layout)

    def add_task(self, instance):
        task_text = self.task_input.text.strip()
        if task_text:
            task_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, padding=(5, 0))
            task_label = Label(text=f"• {task_text}", size_hint_x=0.8, halign='left', valign='middle')
            task_label.bind(size=task_label.setter('text_size'))
            task_box.add_widget(task_label)

            delete_button = Button(text="Delete", size_hint_x=0.2)
            delete_button.bind(on_press=lambda btn: self.delete_task(task_box))
            task_box.add_widget(delete_button)

            self.task_layout.add_widget(task_box)
            self.task_input.text = ""

    def delete_task(self, task_box):
        self.task_layout.remove_widget(task_box)


class PasswordScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Master password input
        self.master_password_input = TextInput(hint_text="Enter Master Password", password=True, size_hint_y=None, height=50)
        layout.add_widget(self.master_password_input)

        # Access button
        access_button = Button(text="Access Passwords", size_hint_y=None, height=50)
        access_button.bind(on_press=self.check_password)
        layout.add_widget(access_button)

        # Message label
        self.message_label = Label(size_hint_y=None, height=50)
        layout.add_widget(self.message_label)

        self.add_widget(layout)

    def check_password(self, instance):
        if self.master_password_input.text == "mmg233":
            self.screen_manager.current = "password_list"
        else:
            self.message_label.text = "Invalid password!"


class PasswordListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Back button
        back_button = Button(text="Back to Main Menu", size_hint_y=None, height=50)
        back_button.bind(on_press=lambda instance: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(back_button)

        # Password input
        self.password_input = TextInput(hint_text="Add a new password", size_hint_y=None, height=50)
        layout.add_widget(self.password_input)

        # Add password button
        add_button = Button(text="Add Password", size_hint_y=None, height=50)
        add_button.bind(on_press=self.add_password)
        layout.add_widget(add_button)

        # Password list
        self.password_list = ScrollView(size_hint=(1, 1))
        self.password_layout = BoxLayout(orientation="vertical", size_hint_y=None)
        self.password_layout.bind(minimum_height=self.password_layout.setter("height"))
        self.password_list.add_widget(self.password_layout)
        layout.add_widget(self.password_list)

        self.add_widget(layout)

    def add_password(self, instance):
        password = self.password_input.text.strip()
        if password:
            password_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, padding=(5, 0))
            password_label = Label(text=password, size_hint_x=0.8, halign="left", valign="middle")
            password_label.bind(size=password_label.setter("text_size"))
            password_box.add_widget(password_label)

            delete_button = Button(text="Delete", size_hint_x=0.2)
            delete_button.bind(on_press=lambda btn: self.delete_password(password_box))
            password_box.add_widget(delete_button)

            self.password_layout.add_widget(password_box)
            self.password_input.text = ""

    def delete_password(self, password_box):
        self.password_layout.remove_widget(password_box)

class MenuScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Title
        layout.add_widget(Label(text="Main Menu", font_size=24, size_hint_y=None, height=50))

        # Menu buttons
        task_button = Button(text="Task List", size_hint_y=None, height=50)
        task_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'tasks'))
        layout.add_widget(task_button)

        password_button = Button(text="Secret Passwords List", size_hint_y=None, height=50)
        password_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'password_entry'))
        layout.add_widget(password_button)

        spotify_button = Button(text="Spotify Connection", size_hint_y=None, height=50)
        spotify_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'spotify'))
        layout.add_widget(spotify_button)

        self.add_widget(layout)


class AssistantApp(App):
    def build(self):
        screen_manager = ScreenManager()

        # Add screens
        screen_manager.add_widget(MenuScreen(screen_manager, name="menu"))
        screen_manager.add_widget(TaskScreen(screen_manager, name="tasks"))
        screen_manager.add_widget(PasswordScreen(screen_manager, name="password_entry"))
        screen_manager.add_widget(PasswordListScreen(name="password_list"))
        screen_manager.add_widget(SpotifyScreen(screen_manager, name="spotify"))

        return screen_manager


if __name__ == "__main__":
    AssistantApp().run()
