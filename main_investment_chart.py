import matplotlib.pyplot as plt
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.popup import Popup
import spotify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import speech_recognition as sr
import os
import json
from kivy.uix.gridlayout import GridLayout
from cryptography.fernet import Fernet
from encryption import encrypt_password, decrypt_password
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from datetime import datetime
from dateutil.relativedelta import relativedelta

FINANCE_FILE = "finance.json"
INVESTMENTS_FILE = "investments.json"
TASKS_FILE = "tasks.json"
PASSWORDS_FILE = "passwords.json"
MASTER_PASSWORD = 'mmg233'

# Spotify credentials (replace with your actual credentials)
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

    def connect_to_spotify(self, instance):
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="user-modify-playback-state user-read-playback-state"
            ))
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

            # Search and play song on Spotify
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
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Load tasks
        self.tasks = self.load_tasks()
        
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
        
        # Display saved tasks
        self.display_tasks()

    def add_task(self, instance):
        task_text = self.task_input.text.strip()
        if task_text:
            self.tasks.append(task_text)  # Add to list
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
            task_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, padding=(5, 0))
            task_label = Label(text=f"• {task}", size_hint_x=0.8, halign='left', valign='middle')
            task_label.bind(size=task_label.setter('text_size'))
            task_box.add_widget(task_label)

            delete_button = Button(text="Delete", size_hint_x=0.2)
            delete_button.bind(on_press=lambda btn, tb=task_box, t=task: self.delete_task(tb, t))
            task_box.add_widget(delete_button)

            self.task_layout.add_widget(task_box)

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
        if self.master_password_input.text == MASTER_PASSWORD:
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Title
        self.layout.add_widget(Label(text="Stored Passwords", font_size=24, size_hint_y=None, height=50))

        # Scrollable password list
        self.scroll_view = ScrollView()
        self.password_list_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.password_list_layout.bind(minimum_height=self.password_list_layout.setter('height'))
        self.scroll_view.add_widget(self.password_list_layout)
        self.layout.add_widget(self.scroll_view)

        # Add Password Button
        add_button = Button(text="Add New Password", size_hint_y=None, height=50)
        add_button.bind(on_press=self.show_add_password_popup)
        self.layout.add_widget(add_button)

        # Back button
        back_button = Button(text="Back to Menu", size_hint_y=None, height=50)
        back_button.bind(on_press=lambda instance: setattr(self.manager, 'current', 'menu'))
        self.layout.add_widget(back_button)

        self.add_widget(self.layout)
        self.passwords = self.load_passwords()
        self.display_passwords()

    def display_passwords(self):
        """Create buttons for each platform that navigate to PasswordDetailsScreen with delete options."""
        self.password_list_layout.clear_widgets()
        for platform, credentials in self.passwords.items():
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

            # Platform button (opens details screen)
            btn = Button(text=platform, size_hint_x=0.7)
            btn.bind(on_press=lambda instance, p=platform: self.show_details_screen(p))
            row.add_widget(btn)

            # Delete button
            delete_btn = Button(text="Delete", size_hint_x=0.3)
            delete_btn.bind(on_press=lambda instance, p=platform: self.delete_password(p))
            row.add_widget(delete_btn)

            self.password_list_layout.add_widget(row)

    def show_details_screen(self, platform):
        """Switch to PasswordDetailsScreen and display details."""
        details_screen = self.manager.get_screen("password_details")
        details_screen.display_details(platform, self.passwords[platform])
        self.manager.current = "password_details"

    def show_add_password_popup(self, instance):
        """Popup to add new password."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        platform_input = TextInput(hint_text="Platform")
        username_input = TextInput(hint_text="Username")
        password_input = TextInput(hint_text="Password")

        save_button = Button(text="Save")
        save_button.bind(on_press=lambda x: self.add_password(platform_input.text, username_input.text, password_input.text))

        popup_layout.add_widget(platform_input)
        popup_layout.add_widget(username_input)
        popup_layout.add_widget(password_input)
        popup_layout.add_widget(save_button)

        popup = Popup(title="Enter new password entry", content=popup_layout, size_hint=(0.8, 0.5))
        save_button.bind(on_press=lambda x: popup.dismiss())  # Close popup after saving
        popup.open()

    def add_password(self, platform, username, password):
        """Save new password to storage and refresh list."""
        if platform and username and password:
            self.passwords[platform] = {"username": username, "password": encrypt_password(password)}
            self.save_passwords()
            self.display_passwords()

    def delete_password(self, platform):
        """Delete password and refresh list."""
        if platform in self.passwords:
            del self.passwords[platform]
            self.save_passwords()
            self.display_passwords()

    def load_passwords(self):
        """Load passwords from JSON file."""
        if os.path.exists(PASSWORDS_FILE):
            try:
                with open(PASSWORDS_FILE, "r") as file:
                    return json.load(file)
            except Exception as e:
                print("Error loading passwords:", e)
        return {}

    def save_passwords(self):
        """Save passwords to JSON file."""
        try:
            with open(PASSWORDS_FILE, "w") as file:
                json.dump(self.passwords, file, indent=4)
        except Exception as e:
            print("Error saving passwords:", e)
class PasswordDetailsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.title_label = Label(text="Password Details", font_size=24, size_hint_y=None, height=50)
        self.layout.add_widget(self.title_label)

        self.platform_label = Label(text="", font_size=18, size_hint_y=None, height=50)
        self.layout.add_widget(self.platform_label)

        self.username_label = Label(text="", font_size=16, size_hint_y=None, height=50)
        self.layout.add_widget(self.username_label)

        self.password_label = Label(text="", font_size=16, size_hint_y=None, height=50)
        self.layout.add_widget(self.password_label)

        # Delete button
        self.delete_button = Button(text="Delete Password", size_hint_y=None, height=50)
        self.delete_button.bind(on_press=self.delete_password)
        self.layout.add_widget(self.delete_button)

        # Back button
        back_button = Button(text="Back to List", size_hint_y=None, height=50)
        back_button.bind(on_press=lambda instance: setattr(self.manager, 'current', 'password_list'))
        self.layout.add_widget(back_button)

        self.add_widget(self.layout)

    def display_details(self, platform, credentials):
        """Update screen with password details."""
        self.platform = platform  # Store for deletion
        self.platform_label.text = f"Platform: {platform}"
        self.username_label.text = f"Username: {credentials['username']}"
        self.password_label.text = f"Password: {decrypt_password(credentials['password'])}"

    def delete_password(self, instance):
        """Delete password and go back to list."""
        password_screen = self.manager.get_screen("password_list")
        password_screen.delete_password(self.platform)
        self.manager.current = "password_list"

class FinanceScreen(Screen):
    def __init__(self,screen_manager, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)


        # Title
        layout.add_widget(Label(text="Finances Menu", font_size=24, size_hint_y=None, height=50))

        # Menu buttons
        back_button = Button(
            text="Back to Main Menu",
            size_hint=(None, None),  # Disable size_hint to use width and height directly
            height=50,
            width=200,  # Set width as per your requirement
            pos_hint={'x': 0, 'top': 1}  # Top-left corner
        )        
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'menu'))
        layout.add_widget(back_button)

        expenses_and_income_button = Button(text="Incomes and Expenses", size_hint_y=None, height=50)
        expenses_and_income_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finance_main_screen'))
        layout.add_widget(expenses_and_income_button)

        investments_button = Button(text='Investments', size_hint_y=None, height=50)
        investments_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finances_investments'))
        layout.add_widget(investments_button)

        self.add_widget(layout)

class FinanceMainScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.data = self.load_finance_data()
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Back button
        back_button = Button(
            text="Back to Finance Menu",
            size_hint=(None, None),  # Disable size_hint to use width and height directly
            height=50,
            width=200,  # Set width as per your requirement
            pos_hint={'x': 0, 'top': 1}  # Top-left corner
        )        
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finances'))
        layout.add_widget(back_button)
        
        # Global summary charts
        self.global_chart = self.create_global_chart()
        layout.add_widget(self.global_chart)
        
        # Dropdown for selecting a month
        self.month_selector = Spinner(text="Select a Month", values=sorted(list(self.data.keys())), size_hint_y=None, height=50)
        self.month_selector.bind(text=self.open_selected_month)
        layout.add_widget(self.month_selector)
        
        # Button to add new month with custom name
        self.month_input = TextInput(hint_text="Enter Month Name", size_hint_y=None, height=50)
        layout.add_widget(self.month_input)
        
        add_month_button = Button(text="Add New Month", size_hint_y=None, height=50)
        add_month_button.bind(on_press=self.add_new_month)
        layout.add_widget(add_month_button)
        
        # Scrollable container for all months' charts
        self.scroll_view = ScrollView()
        self.chart_container = GridLayout(cols=1, size_hint_y=None)
        self.chart_container.bind(minimum_height=self.chart_container.setter('height'))
        self.scroll_view.add_widget(self.chart_container)
        #layout.add_widget(self.scroll_view)
        
        self.add_widget(layout)
        self.update_all_months_charts()
    
    def load_finance_data(self):
        if os.path.exists(FINANCE_FILE):
            with open(FINANCE_FILE, "r") as file:
                return json.load(file)
        return {}
    
    def save_finance_data(self):
        with open(FINANCE_FILE, "w") as file:
            json.dump(self.data, file, indent=4)
    
    def add_new_month(self, instance):
        new_month = self.month_input.text.strip()
        if new_month and new_month not in self.data:
            self.data[new_month] = {"Income": [], "Expenses": []}
            self.save_finance_data()
            self.month_selector.values = list(self.data.keys())
            self.update_all_months_charts()
    
    def create_global_chart(self):
        fig, ax = plt.subplots()
        ax.set_title("Global Income vs Expenses")
        ax.set_ylabel("Amount")

        months = list(self.data.keys())
        total_income = sum(sum(self.data[m]["Income"][length]["amount"] for length in range(len(self.data[m]["Income"]))) for m in months if len(self.data[m]["Income"]) != 0)
        total_expenses = sum(sum(self.data[m]["Expenses"][length]["amount"] for length in range(len(self.data[m]["Expenses"]))) for m in months if len(self.data[m]["Expenses"]) != 0)
        ax.bar(["Income", "Expenses"], [total_income, total_expenses], color=["green", "red"])
        
        return FigureCanvasKivyAgg(fig)
    
    def create_month_chart(self, month):
        fig, ax = plt.subplots()
        ax.set_title(f"{month}: Income vs Expenses")
        ax.set_ylabel("Amount")
        
        income = sum(self.data[month]["Income"][length]["amount"] for length in range(len(self.data[month]["Income"]))) 
        expenses = sum(self.data[month]["Expenses"][length]["amount"] for length in range(len(self.data[month]["Expenses"])))
        ax.bar(["Income", "Expenses"], [income, expenses], color=["green", "red"])
        
        return FigureCanvasKivyAgg(fig)
    
    def update_all_months_charts(self):
        self.data = self.load_finance_data()
        self.chart_container.clear_widgets()
        for month in sorted(self.data.keys()):
            chart_box = BoxLayout(orientation='vertical', size_hint_y=None)
            month_chart = self.create_month_chart(month)
            chart_box.add_widget(month_chart)
            self.chart_container.add_widget(chart_box)
    
    def open_selected_month(self, spinner, text):
        if text and f"finances_{text}" not in self.screen_manager.screen_names:
            month_screen = FinanceMonthScreen(self.screen_manager, f"finances_{text}", text)
            self.screen_manager.add_widget(month_screen)
        self.screen_manager.current = f"finances_{text}"

class FinanceMonthScreen(Screen):
    def __init__(self, screen_manager, name, month, **kwargs):
        super().__init__(name=name, **kwargs)
        self.month = month
        self.screen_manager = screen_manager
        self.data = self.load_finance_data()
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text=f"Finance - {month}", font_size=24, size_hint_y=None, height=50))
        
        # Grid Layout with scroll
        scroll_view = ScrollView(size_hint=(1, 1))
        self.grid = GridLayout(cols=4, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        # Headers
        header_layout = GridLayout(cols=4, size_hint_y=None, height=50)
        header_layout.add_widget(Label(text="Category", font_size=18))
        header_layout.add_widget(Label(text="Amount", font_size=18))
        header_layout.add_widget(Label(text="Description", font_size=18))
        header_layout.add_widget(Label(text="Delete", font_size=18))
        layout.add_widget(header_layout)
        
        scroll_view.add_widget(self.grid)
        layout.add_widget(scroll_view)
        
        # Load existing data
        self.entry_inputs = []
        self.load_existing_entries()
        
        # Add new entry section
        self.new_category = Spinner(text="Income", values=["Income", "Expense"], size_hint_y=None, height=50)
        self.new_amount = TextInput(hint_text="Amount", size_hint_y=None, height=50)
        self.new_description = TextInput(hint_text="Description", size_hint_y=None, height=50)
        add_entry_btn = Button(text="Add", size_hint_y=None, height=50)
        add_entry_btn.bind(on_press=self.add_entry)
        
        new_entry_layout = GridLayout(cols=4, size_hint_y=None, height=50)
        new_entry_layout.add_widget(self.new_category)
        new_entry_layout.add_widget(self.new_amount)
        new_entry_layout.add_widget(self.new_description)
        new_entry_layout.add_widget(add_entry_btn)
        
        layout.add_widget(new_entry_layout)
        
        # Back button
        back_button = Button(text="Back", size_hint_y=None, height=50)
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)
        
        self.add_widget(layout)
    
    def load_finance_data(self):
        if os.path.exists(FINANCE_FILE):
            with open(FINANCE_FILE, "r") as file:
                return json.load(file)
        return {self.month: {"Income": [], "Expenses": []}}
    
    def save_finance_data(self):
        with open(FINANCE_FILE, "w") as file:
            json.dump(self.data, file, indent=4)
    
    def load_existing_entries(self):
        for category in ["Income", "Expenses"]:
            for entry in self.data.get(self.month, {}).get(category, []):
                self.add_entry_to_grid(category, str(entry["amount"]), entry["description"])
    
    def add_entry_to_grid(self, category, amount, description):
        category_label = Label(text=category, size_hint_y=None, height=50)
        amount_input = TextInput(text=amount, size_hint_y=None, height=50)
        description_input = TextInput(text=description, size_hint_y=None, height=50)
        delete_btn = Button(text="X", size_hint_y=None, height=50)
        
        def remove_entry(instance):
            self.grid.remove_widget(category_label)
            self.grid.remove_widget(amount_input)
            self.grid.remove_widget(description_input)
            self.grid.remove_widget(delete_btn)
            self.entry_inputs.remove((category, amount_input, description_input))
        
        delete_btn.bind(on_press=remove_entry)
        
        self.grid.add_widget(category_label)
        self.grid.add_widget(amount_input)
        self.grid.add_widget(description_input)
        self.grid.add_widget(delete_btn)
        
        self.entry_inputs.append((category, amount_input, description_input))
    
    def add_entry(self, instance):
        category = self.new_category.text.strip()
        amount = self.new_amount.text.strip()
        description = self.new_description.text.strip()
        
        if category and amount.isdigit():
            self.add_entry_to_grid(category, amount, description)
            self.new_category.text = "Income"
            self.new_amount.text = ""
            self.new_description.text = ""
    
    def on_leave(self):
        self.data[self.month] = {"Income": [], "Expenses": []}
        for category, amount_input, description_input in self.entry_inputs:
            if amount_input.text.isdigit():
                self.data[self.month]["Income" if category == "Income" else "Expenses"].append({"amount": int(amount_input.text), "description": description_input.text})
        self.save_finance_data()
    
    def go_back(self, instance):
        self.screen_manager.get_screen("finance_main_screen").update_all_months_charts()
        self.screen_manager.current = "finance_main_screen"


class FinanceScreenInvestmets(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.data = self.load_finance_data()
        
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Dropdown to select category
        self.category_spinner = Spinner(
            text="Select Category",
            values=("Investments"),
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.category_spinner)

        # Input fields
        self.amount_input = TextInput(hint_text="Amount", size_hint_y=None, height=50)
        layout.add_widget(self.amount_input)

        # Back button
        back_button = Button(text="Back to Finances Menu", size_hint_y=None, height=50)
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finances'))
        layout.add_widget(back_button)

        # Add Entry button
        add_button = Button(text="Add Entry", size_hint_y=None, height=50)
        add_button.bind(on_press=self.add_entry)
        layout.add_widget(add_button)

        # Dropdown to remove entry
        self.remove_spinner = Spinner(
            text="Select Entry to Remove", 
            size_hint_y=None, 
            height=50
        )
        layout.add_widget(self.remove_spinner)

        # Remove Entry button
        remove_button = Button(text="Remove Entry", size_hint_y=None, height=50)
        remove_button.bind(on_press=self.remove_entry)
        layout.add_widget(remove_button)

        # Matplotlib chart widgets
        self.investment_chart = self.create_pie_chart()
        
        layout.add_widget(self.investment_chart)
        
        self.add_widget(layout)
        self.update_charts()
    
    def load_finance_data(self):
        if os.path.exists(INVESTMENTS_FILE):
            with open(INVESTMENTS_FILE, "r") as file:
                return json.load(file)
        return {"Investments": {}}

    def save_finance_data(self):
        with open(INVESTMENTS_FILE, "w") as file:
            json.dump(self.data, file, indent=4)

    def add_entry(self, instance):
        category = self.category_spinner.text
        amount = self.amount_input.text.strip()
        if category != "Select Category" and amount.isdigit():
            amount = int(amount)
            if category == "Investments":
                investment_name = f"Investment {len(self.data['Investments']) + 1}"
                self.data["Investments"][investment_name] = amount
            
            self.amount_input.text = ""
            self.save_finance_data()
            self.update_charts()

    def remove_entry(self, instance):
        selected_entry = self.remove_spinner.text
        if selected_entry.startswith("Investment"):
            del self.data["Investments"][selected_entry]
        
        self.save_finance_data()
        self.update_charts()
    
    def create_pie_chart(self):
        fig, ax = plt.subplots()
        ax.set_title("Investment Portfolio")
        return FigureCanvasKivyAgg(fig)
    
    def update_charts(self):

        # Update Pie Chart
        self.investment_chart.figure.clear()
        ax2 = self.investment_chart.figure.add_subplot(111)
        investments = self.data["Investments"]
        labels = investments.keys()
        amounts = investments.values()
        ax2.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=140)
        ax2.set_title("Investment Portfolio")
        self.investment_chart.figure.canvas.draw()
        
        # Update dropdown for removing entries
        self.remove_spinner.values = (
            list(self.data["Investments"].keys())
        )

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

        finances_button = Button(text="Finances", size_hint_y=None, height=50)
        finances_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finances'))
        layout.add_widget(finances_button)

        self.add_widget(layout)
class AssistantApp(App):
    def build(self):
        screen_manager = ScreenManager()

        # Add primary screens
        screen_manager.add_widget(MenuScreen(screen_manager, name="menu"))
        screen_manager.add_widget(TaskScreen(screen_manager, name="tasks"))
        screen_manager.add_widget(PasswordScreen(screen_manager, name="password_entry"))
        screen_manager.add_widget(PasswordListScreen(name="password_list"))
        screen_manager.add_widget(SpotifyScreen(screen_manager, name="spotify"))
        screen_manager.add_widget(PasswordDetailsScreen(name="password_details"))
        screen_manager.add_widget(FinanceScreen(screen_manager, name="finances"))
        screen_manager.add_widget(FinanceMainScreen(screen_manager, name="finance_main_screen"))
        screen_manager.add_widget(FinanceScreenInvestmets(screen_manager, name="finances_investments")) 

        # Dynamically add past finance month screens
        self.add_month_screens(screen_manager)

        return screen_manager

    def add_month_screens(self, screen_manager):
        """Dynamically adds the past 6 months to the screen manager"""
        months = self.get_last_six_months()  # Get last 6 months dynamically
        for month in months:
            screen_name = f"finances_{month}"
            if not screen_manager.has_screen(screen_name):  # Avoid duplicates
                screen_manager.add_widget(FinanceMonthScreen(screen_manager, screen_name, month))

    def get_last_six_months(self):
        """Returns a list of the last 6 months as strings (e.g., ['Feb', 'Jan', 'Dec', ...'])"""
        today = datetime.today()  # Use the full module path
        return [(today - relativedelta(months=i)).strftime("%b") for i in range(6)]


if __name__ == "__main__":
    AssistantApp().run()