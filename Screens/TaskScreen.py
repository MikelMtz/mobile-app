from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
import os
import json

TASKS_FILE = "tasks.json"

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