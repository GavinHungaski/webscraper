from tkinter import scrolledtext
from typing import Optional, Callable
import tkinter as tk
import threading
import os


def get_discord_login(file_path = 'data/discord.txt'):
    result = {'discord_url': '', 'discord_auth': ''}
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                result[key] = value
    return result


class ScraperUI:
    def __init__(
            self,
            master=None,
            scraper_function: Optional[Callable]=None
        ) -> None:
        self.sleep_time = 10
        self.scraper_running = False
        self.discord_url, self.discord_auth = get_discord_login()
        self.discord_url_var = tk.StringVar(value=self.discord_url)
        self.discord_auth_var = tk.StringVar(value=self.discord_auth)
        self.links = []
        self.master = master
        if self.master:
            self.master.title("Craigslist Scraper V1.0")
            try:
                self.master.wm_iconbitmap("./data/diamond_icon.ico")
            except tk.TclError:
                print("Warning: Icon file 'diamond.ico' not found")
        self._create_widgets()

    def _create_widgets(self) -> None:
        # Main Frame Setup
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill="both", expand=True)
        
        # Text Area Frame
        self.text_area_frame = tk.Frame(self.main_frame)
        self.text_area_frame.pack(fill="both", expand=True)

        self.info_text_area = scrolledtext.ScrolledText(
            self.text_area_frame,
            width=40,
            height=20,
            state="disabled",
            wrap="word",
            bg="#2e2e2e",
            fg="white"
            )
        self.info_text_area.pack(fill="both", expand=True)

        # Control Panel Frame
        self.control_panel_frame = tk.Frame(self.main_frame, width=200)
        self.control_panel_frame.pack(side="right", fill="both", expand=True)

        # Input Frame
        self.input_frame = tk.Frame(self.control_panel_frame)
        self.input_frame.pack(side="left", fill="both", expand=True)

        self.input_edit_button = tk.Button(
            self.input_frame,
            text="Edit",
            command=self.edit_inputs,
        )
        self.input_edit_button.grid(row=0, column=1)

        self.discord_url_label = tk.Label(self.input_frame, text="Discord URL:")
        self.discord_url_label.grid(row=1, column=0, sticky="w")
        self.discord_url_input = tk.Entry(
            self.input_frame,
            width=15,
            state="disabled",
            textvariable=self.discord_url_var
            )
        self.discord_url_input.grid(row=1, column=1)

        self.discord_auth_label = tk.Label(self.input_frame, text="Discord Auth:")
        self.discord_auth_label.grid(row=2, column=0, sticky="w")
        self.discord_auth_input = tk.Entry(
            self.input_frame,
            width=15,
            state="disabled",
            textvariable=self.discord_auth_var
            )
        self.discord_auth_input.grid(row=2, column=1)

        self.links_label = tk.Label(self.input_frame, text="Links:")
        self.links_label.grid(row=3, column=0, sticky="w")
        self.links_input = scrolledtext.ScrolledText(
            self.input_frame,
            width=15,
            height=5,
            state="disabled",
            wrap="word"
        )
        self.links_input.grid(row=3, column=1)

        # Time Entry and Label Frame
        self.time_entry_frame = tk.Frame(self.control_panel_frame)
        self.time_entry_frame.pack(side="top", padx=25, pady=25)

        self.time_label = tk.Label(
            self.time_entry_frame, text=f"Scrape interval [in minutes]> {self.sleep_time} <")
        self.time_label.pack(side="left")

        self.time_entry_label = tk.Label(
            self.time_entry_frame, text="")
        self.time_entry_label.pack(side="right")

        self.time_entry = tk.Entry(self.time_entry_frame, width=5)
        self.time_entry.pack(side="left")

        self.set_time_button = tk.Button(
            self.time_entry_frame, text="Set", command=self.set_sleep_time)
        self.set_time_button.pack(side="right")

        # Start Button
        self.start_button = tk.Button(
            self.control_panel_frame,
            text="Start",
            command=self.start,
            bg="#4CAF50",
            activebackground="#45a049"
            )
        self.start_button.pack(pady=20, ipadx=10, ipady=5)

    def edit_inputs(self):
        current_text = self.input_edit_button.cget("text")
        if current_text == "Edit":
            self.input_edit_button.config(text="Done")
            self.discord_url_input.config(state="normal")
            self.discord_auth_input.config(state="normal")
            self.links_input.config(state="normal")
        elif current_text == "Done":
            self.input_edit_button.config(text="Edit")
            self.discord_url_input.config(state="disabled")
            self.discord_auth_input.config(state="disabled")
            self.links_input.config(state="disabled")

    def set_sleep_time(self):
        try:
            temp_time = int(self.time_entry.get())
            if temp_time > 1:
                self.sleep_time = temp_time
                self.time_label['text'] = f"Scrape interval [in minutes]> {self.sleep_time} <"
            else:
                self.write_to_info(
                    "Scrape Interval:\n\tMin: 2 minutes\n")
        except ValueError:
            self.write_to_info("Invalid input. Please enter a valid number.")

    def write_to_info(self, message):
        self.info_text_area.config(state="normal")
        self.info_text_area.insert(tk.END, message + "\n")
        self.info_text_area.see(tk.END)
        self.info_text_area.config(state="disabled")

    def start(self):
        if not self.scraper_running:
            if len(self.get_links()) > 0:
                self.write_to_info("Starting up . . .\n")
                self.scraper_running = True
                self.scrape_thread = threading.Thread(
                    target=self.scraper_function, args=(self,))
                self.scrape_thread.daemon = True
                self.scrape_thread.start()
            else:
                self.write_to_info(
                    "No links found, add links and retry")
        else:
            self.write_to_info(
                "Already running . . .")

    def get_links(self, file_path='./links.txt'):
        try:
            with open(file_path, 'r') as file:
                links = file.read()
                links = links.splitlines()
            return links
        except FileNotFoundError:
            self.write_to_info(f"File {file_path} not found.")
            return []
