from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
import subprocess
import spotify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import speech_recognition as sr
from kivy.uix.popup import Popup
from kivy.uix.label import Label


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
