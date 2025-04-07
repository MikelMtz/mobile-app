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

MONTH_ORDER = {
    "Enero": 0, "Febrero": 1, "Marzo": 2, "Abril": 3, "Mayo": 4, "Junio": 5,
    "Julio": 6, "Agosto": 7, "Septiembre": 8, "Octubre": 9, "Noviembre": 10, "Diciembre": 11
}


    
def parse_month_year(month_str):
    try:
        parts = month_str.split()
        if len(parts) != 2:
            return None, None
        month, year = parts[0], parts[1]
        if month not in MONTH_ORDER or not year.isdigit():
            return None, None
        return int(year), MONTH_ORDER[month]
    except Exception:
        return None, None

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
            size_hint=(None, None),
            height=50,
            width=200,
            pos_hint={'x': 0, 'top': 1}
        )        
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finances'))
        layout.add_widget(back_button)
        
        # Global summary charts
        self.global_chart = self.create_global_chart()
        layout.add_widget(self.global_chart)
        
        # Button to navigate to months management screen
        manage_months_button = Button(text="Manage Months", size_hint_y=None, height=50)
        manage_months_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'months_list'))
        layout.add_widget(manage_months_button)
        
        self.add_widget(layout)
        
    def load_finance_data(self):
        if os.path.exists(FINANCE_FILE):
            with open(FINANCE_FILE, "r") as file:
                return json.load(file)
        return {}
    
    def save_finance_data(self):
        with open(FINANCE_FILE, "w") as file:
            json.dump(self.data, file, indent=4)
    
    def create_global_chart(self):
        fig, ax = plt.subplots()
        ax.set_title("Global Income vs Expenses")
        ax.set_ylabel("Amount")

        months = list(self.data.keys())
        total_income = sum(sum(self.data[m]["Income"][length]["amount"] for length in range(len(self.data[m]["Income"]))) for m in months if len(self.data[m]["Income"]) != 0)
        total_expenses = sum(sum(self.data[m]["Expenses"][length]["amount"] for length in range(len(self.data[m]["Expenses"]))) for m in months if len(self.data[m]["Expenses"]) != 0)
        ax.bar(["Income", "Expenses"], [total_income, total_expenses], color=["green", "red"])
        
        return FigureCanvasKivyAgg(fig)

class MonthsListScreen(Screen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager
        self.data = self.load_finance_data()

        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Back button
        back_button = Button(text="Back", size_hint_y=None, height=50)
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finance_main_screen'))
        main_layout.add_widget(back_button)

        # Input field to add new month
        self.month_input = TextInput(hint_text="Ejemplo: 2024 Septiembre", size_hint_y=None, height=50)
        main_layout.add_widget(self.month_input)

        add_month_button = Button(text="Add New Month", size_hint_y=None, height=50)
        add_month_button.bind(on_press=self.add_new_month)
        main_layout.add_widget(add_month_button)

        # Scrollable list container with fixed height
        container = BoxLayout(orientation='vertical', size_hint=(1, None), height=400)  # Set a fixed height or adjust dynamically
        self.scroll_view = ScrollView(size_hint=(1, None), height=400)  # Adjust as needed for scrollable area

        self.months_list = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=5)
        self.months_list.bind(minimum_height=self.months_list.setter('height'))  # Ensure dynamic height adjustment
        self.scroll_view.add_widget(self.months_list)
        container.add_widget(self.scroll_view)
        main_layout.add_widget(container)

        # Populate months list
        self.populate_months_list()

        self.add_widget(main_layout)

    def load_finance_data(self):
        if os.path.exists(FINANCE_FILE):
            with open(FINANCE_FILE, "r") as file:
                data = json.load(file)
                print(f"Loaded finance data: {data}")  # Debugging statement
                return data
        return {}

    
    def add_new_month(self, instance):
        new_month = self.month_input.text.strip()
        if new_month and new_month not in self.data:
            self.data[new_month] = {"Income": [], "Expenses": []}
            self.save_finance_data()
            self.populate_months_list()
            self.month_input.text = ""  # Clear the input box after adding the month

    def save_finance_data(self):
        with open(FINANCE_FILE, "w") as file:
            json.dump(self.data, file, indent=4)

    def delete_month(self, month):
        if month in self.data:
            del self.data[month]
            self.save_finance_data()
            self.populate_months_list()

    def populate_months_list(self):
        self.months_list.clear_widgets()

        valid_months = []
        for month in self.data.keys():
            year, month_order = parse_month_year(month)
            if year is not None and month_order is not None:
                valid_months.append((year, month_order, month))

        sorted_months = sorted(valid_months, key=lambda x: (-x[0], -x[1]))

        self.months_list.height = len(sorted_months) * 50  # Adjust height dynamically

        for _, _, month in sorted_months:
            month_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

            month_button = Button(text=month, size_hint_x=0.8)
            month_button.bind(on_press=lambda instance, m=month: self.open_selected_month(m))

            delete_button = Button(text="X", size_hint_x=0.2)
            delete_button.bind(on_press=lambda instance, m=month: self.delete_month(m))

            month_layout.add_widget(month_button)
            month_layout.add_widget(delete_button)
            self.months_list.add_widget(month_layout)


    def open_selected_month(self, month):
        screen_name = f"finances_{month}"
        if screen_name not in self.screen_manager.screen_names:
            month_screen = FinanceMonthScreen(self.screen_manager, name=screen_name, month=month)
            self.screen_manager.add_widget(month_screen)
        self.screen_manager.current = screen_name


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
        back_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'months_list'))
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

        finances_button = Button(text="Finances", size_hint_y=None, height=50)
        finances_button.bind(on_press=lambda instance: setattr(screen_manager, 'current', 'finances'))
        layout.add_widget(finances_button)

        self.add_widget(layout)
class AssistantApp(App):
    def build(self):
        screen_manager = ScreenManager()

        # Add primary screens
        screen_manager.add_widget(MenuScreen(screen_manager, name="menu"))
        screen_manager.add_widget(FinanceScreen(screen_manager, name="finances"))
        screen_manager.add_widget(FinanceMainScreen(screen_manager, name="finance_main_screen"))
        screen_manager.add_widget(FinanceScreenInvestmets(screen_manager, name="finances_investments")) 
        screen_manager.add_widget(MonthsListScreen(screen_manager, name="months_list"))

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