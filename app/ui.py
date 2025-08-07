from tkinter import scrolledtext
from typing import Optional, Callable
from tinydb import TinyDB, Query
import tkinter as tk
import threading

class ScraperUI:
    def __init__(
            self,
            master=None,
            scraper_function: Optional[Callable]=None
        ) -> None:
        self.sleep_time = 10
        self.scraper_running = False
        self.scraper_function = scraper_function
        self.db = TinyDB('db.json')
        self.links_table = self.db.table('links')
        self.discord_table = self.db.table('discord')
        self.discord_settings = self.discord_table.all()
        if self.discord_settings:
            discord_data = self.discord_settings[0]
            self.discord_url_var = tk.StringVar(value=discord_data.get("channel_url"))
            self.discord_auth_var = tk.StringVar(value=discord_data.get("auth_token"))
        else:
            self.discord_url_var = tk.StringVar(value="")
            self.discord_auth_var = tk.StringVar(value="")
        self.master = master
        if self.master:
            self.master.title("Craigslist Scraper V0.2.0")
            try:
                self.master.wm_iconbitmap("./data/diamond_icon.ico")
            except tk.TclError:
                print("Warning: Icon file 'diamond.ico' not found")
        self._create_widgets()
        self._set_initial_links()

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
            wrap="none"
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

    def _set_initial_links(self):
        self.links_input.config(state="normal")
        self.links_input.delete("1.0", tk.END)
        for link in self.links_table.all():
            self.links_input.insert(tk.END, link['url'] + "\n")
        self.links_input.config(state="disabled")

    def edit_inputs(self):
        current_text = self.input_edit_button.cget("text")
        if current_text == "Edit":
            self.input_edit_button.config(text="Done")
            self.discord_url_input.config(state="normal")
            self.discord_auth_input.config(state="normal")
            self.links_input.config(state="normal")
        elif current_text == "Done":
            self.input_edit_button.config(text="Edit")
            self.discord_table.truncate()
            self.discord_table.insert({'channel_url': self.discord_url_var.get(), 'auth_token': self.discord_auth_var.get()})
            self.save_links()
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
            if len(self.links_table.all()) > 0:
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

    def save_links(self):
        links_text = self.links_input.get("1.0", tk.END).strip()
        new_links = {link.strip() for link in links_text.split('\n') if link.strip()}
        try:
            existing_links = {doc['url'] for doc in self.links_table.all()}
        except KeyError:
            self.write_to_info("Warning: A document in the links table is missing a 'url' key.")
        links_to_delete = existing_links - new_links
        if links_to_delete:
            query = Query()
            self.links_table.remove(query.url.one_of(links_to_delete))
            self.write_to_info(f"Deleted {len(links_to_delete)} links that are no longer present.")
        links_to_add = new_links - existing_links
        if links_to_add:
            new_link_docs = [{'url': link} for link in links_to_add]
            self.links_table.insert_multiple(new_link_docs)
            self.write_to_info(f"Added {len(links_to_add)} new links.")