from encryption import encrypt_password, decrypt_password
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty


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
