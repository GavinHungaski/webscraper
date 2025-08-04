from tkinter import scrolledtext
import tkinter as tk
from typing import Optional, Callable
import threading


class ScraperUI:
    def __init__(
            self,
            master=None,
            scraper_function: Optional[Callable]=None
        ) -> None:
        self.sleep_time = 10
        self.scraper_running = False
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
        self.toggle_button = tk.Button(
            self.control_panel_frame,
            text="Start",
            command=self.start,
            font=("Arial", 11),
            bg="#4CAF50",
            activebackground="#45a049"
            )
        self.toggle_button.pack(pady=20, ipadx=10, ipady=5)

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
