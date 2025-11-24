# File: ui.py

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue
import threading
from download import CrawlThread

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Website Cloner")
        self.geometry("700x550")  # Increased height slightly for the new field

        # --- State Management ---
        self.driver = None
        self.session_cookies = None
        self.start_url = None
        self.crawl_thread = None
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.recursive_var = tk.BooleanVar(value=True)

        self.create_widgets()
        self.check_log_queue()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- URL Input Frame ---
        url_frame = ttk.Frame(self, padding="10")
        url_frame.pack(fill=tk.X, side=tk.TOP)

        url_label = ttk.Label(url_frame, text="Starting URL:")
        url_label.pack(side=tk.LEFT, padx=(0, 5))

        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.insert(0, "https://example.com/")
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Main Controls Frame ---
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(fill=tk.X, side=tk.TOP)

        self.open_browser_button = ttk.Button(control_frame, text="1. Open Browser", command=self.open_browser)
        self.open_browser_button.pack(side=tk.LEFT, padx=5)

        self.confirm_login_button = ttk.Button(control_frame, text="2. Confirm Page & Get Session", state="disabled", command=self.confirm_page)
        self.confirm_login_button.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(control_frame, text="3. Start Download", state="disabled", command=self.start_crawling)
        self.start_button.pack(side=tk.LEFT, padx=5)

        # --- Secondary Controls Frame ---
        control_frame_2 = ttk.Frame(self, padding="10")
        control_frame_2.pack(fill=tk.X, side=tk.TOP)

        self.pause_button = ttk.Button(control_frame_2, text="Pause", state="disabled", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_button = ttk.Button(control_frame_2, text="Stop", state="disabled", command=self.stop_crawling)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.recursive_checkbox = ttk.Checkbutton(control_frame_2, text="Download Recursively (follow links)", variable=self.recursive_var)
        self.recursive_checkbox.pack(side=tk.LEFT, padx=15, pady=5)

        self.status_label = ttk.Label(self, text="Status: Idle", padding="10")
        self.status_label.pack(fill=tk.X, side=tk.TOP)

        # --- Log Frame ---
        log_frame = ttk.Frame(self, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled", height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, str(message) + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)

    def check_log_queue(self):
        while not self.log_queue.empty():
            try:
                message = self.log_queue.get_nowait()
                if isinstance(message, tuple):
                    msg_type, data = message
                    if msg_type == "STATUS":
                        self.status_label.config(text=f"Status: {data}")
                    elif msg_type == "CRAWL_COMPLETE":
                        self.log(data)
                        self.status_label.config(text=f"Status: {data}")
                        self.reset_ui_after_crawl()
                else:
                    self.log(message)
            except queue.Empty:
                pass
        self.after(100, self.check_log_queue)

    def open_browser(self):
        url_to_open = self.url_entry.get()
        if not url_to_open or not (url_to_open.startswith('http://') or url_to_open.startswith('https://')):
            messagebox.showerror("Invalid URL", "Please enter a valid URL starting with http:// or https://")
            return

        self.open_browser_button.config(state="disabled")
        self.log(f"👉 Opening browser to {url_to_open}. Please log in if needed.")
        threading.Thread(target=self._open_browser_thread, args=(url_to_open,), daemon=True).start()

    def _open_browser_thread(self, url):
        from download import open_browser_for_login
        if not self.driver:
            self.driver = open_browser_for_login(url)

        if self.driver:
            self.log("✅ Browser is open. Navigate to your starting page, then click 'Confirm Page'.")
            self.confirm_login_button.config(state="normal")
        else:
            self.log("❌ Failed to open browser.")
            self.open_browser_button.config(state="normal")

    def confirm_page(self):
        if not self.driver:
            self.log("❌ Browser is not open! Click 'Open Browser' first.")
            return

        self.start_url = self.driver.current_url
        self.session_cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}

        self.log(f"✅ Session updated! Starting URL captured: {self.start_url}")

        self.start_button.config(state="normal")
        self.status_label.config(text="Status: Ready to Download!")

    def start_crawling(self):
        self.start_button.config(state="disabled")
        self.confirm_login_button.config(state="disabled")
        self.recursive_checkbox.config(state="disabled")
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")
        self.open_browser_button.config(state="disabled")  # prevent opening a 2nd browser while crawling

        self.stop_event.clear()
        self.pause_event.clear()
        self.log("\n--- Starting Website Clone ---")

        # Pass the SAME Selenium driver so we can click the sidebar items in-place
        self.crawl_thread = CrawlThread(
            cookies=self.session_cookies,
            base_url=self.start_url,
            log_queue=self.log_queue,
            stop_event=self.stop_event,
            pause_event=self.pause_event,
            recursive=self.recursive_var.get(),
            driver=self.driver,   # <--- NEW
        )
        self.crawl_thread.start()

    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="Pause")
            self.log("▶️ Resuming...")
        else:
            self.pause_event.set()
            self.pause_button.config(text="Resume")
            self.log("⏸️ Paused.")

    def stop_crawling(self):
        if self.crawl_thread and self.crawl_thread.is_alive():
            self.stop_event.set()
            if self.pause_event.is_set():
                self.pause_event.clear()
            self.stop_button.config(state="disabled")

    def reset_ui_after_crawl(self):
        self.confirm_login_button.config(state="normal")
        self.recursive_checkbox.config(state="normal")
        self.start_button.config(state="disabled")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")
        self.open_browser_button.config(state="normal")
        self.log("\nReady for next download. Navigate to a new page and click 'Confirm Page'.")

    def on_closing(self):
        try:
            if self.driver:
                self.driver.quit()
        finally:
            self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
