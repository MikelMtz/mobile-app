from kivy.properties import ObjectProperty
from encryption import encrypt_password, decrypt_password
from kivy.uix.screenmanager import ScreenManager, Screen
import json
import os

PASSWORDS_FILE = "passwords.json"
MASTER_PASSWORD = 'gAAAAABnq4El7cvRE-m8Tbx3Ac-ckyC4KPRuPl0Pp_x539Pwgd5Xzw-wHZfQBvvC5sdVBVwmFXNIrIHS7Hv8U4vX32R-bnE-RQ=='

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
