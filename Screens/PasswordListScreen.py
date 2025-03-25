from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from encryption import encrypt_password, decrypt_password
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
import os
import json

PASSWORDS_FILE = "passwords.json"
MASTER_PASSWORD = 'gAAAAABnq4El7cvRE-m8Tbx3Ac-ckyC4KPRuPl0Pp_x539Pwgd5Xzw-wHZfQBvvC5sdVBVwmFXNIrIHS7Hv8U4vX32R-bnE-RQ=='

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
