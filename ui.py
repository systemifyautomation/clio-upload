"""
Tkinter UI for uploading files to Clio matters
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from dotenv import load_dotenv
from clio_client import ClioAPIClient
from pathlib import Path
import threading


class ClioUploadUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Clio File Upload")
        self.root.geometry("700x500")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize variables
        self.selected_file = tk.StringVar()
        self.selected_matter = None
        self.matters_list = []
        self.client = None
        
        # Setup UI
        self.setup_ui()
        
        # Initialize Clio client
        self.initialize_client()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Clio File Upload", 
                                font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="1. Select File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.selected_file, state="readonly"
                 ).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(file_frame, text="Browse...", 
                  command=self.browse_file).grid(row=0, column=2)
        
        # Matter selection section
        matter_frame = ttk.LabelFrame(main_frame, text="2. Select Matter", padding="10")
        matter_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), 
                         pady=(0, 10))
        matter_frame.columnconfigure(0, weight=1)
        matter_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Search box
        search_frame = ttk.Frame(matter_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_matters)
        ttk.Entry(search_frame, textvariable=self.search_var
                 ).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Matters list with scrollbar
        list_frame = ttk.Frame(matter_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.matters_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                          height=10)
        self.matters_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.matters_listbox.yview)
        
        ttk.Button(matter_frame, text="Refresh Matters", 
                  command=self.load_matters).grid(row=2, column=0, pady=(5, 0))
        
        # Description section
        desc_frame = ttk.LabelFrame(main_frame, text="3. Description (Optional)", 
                                    padding="10")
        desc_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        desc_frame.columnconfigure(0, weight=1)
        
        self.description_text = tk.Text(desc_frame, height=3, width=50)
        self.description_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Upload section
        upload_frame = ttk.Frame(main_frame)
        upload_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        upload_frame.columnconfigure(0, weight=1)
        
        self.upload_button = ttk.Button(upload_frame, text="Upload File", 
                                       command=self.upload_file, state="disabled")
        self.upload_button.grid(row=0, column=0)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
    
    def initialize_client(self):
        """Initialize the Clio API client"""
        try:
            access_token = os.getenv("CLIO_ACCESS_TOKEN")
            region = os.getenv("CLIO_REGION", "eu")
            
            print(f"DEBUG: Access token loaded: {access_token[:10] if access_token else 'None'}...")
            print(f"DEBUG: Region: {region}")
            
            if not access_token:
                error_msg = ("CLIO_ACCESS_TOKEN not found in environment variables.\n\n"
                           "Please create a .env file with your Clio credentials.\n"
                           "You can copy .env.example to .env and add your token.")
                messagebox.showerror("Configuration Error", error_msg)
                self.status_var.set("Error: Missing access token")
                return
            
            self.client = ClioAPIClient(access_token=access_token, region=region)
            self.status_var.set("Connected to Clio API")
            print("DEBUG: Client initialized successfully")
            
            # Load matters automatically
            self.load_matters()
            
        except Exception as e:
            error_msg = f"Failed to initialize Clio client:\n{str(e)}\n\nPlease check your .env file configuration."
            messagebox.showerror("Initialization Error", error_msg)
            self.status_var.set("Error: Failed to connect")
            print(f"DEBUG: Initialization error: {e}")
            import traceback
            traceback.print_exc()
    
    def browse_file(self):
        """Open file dialog to select a file"""
        filename = filedialog.askopenfilename(
            title="Select file to upload",
            filetypes=[("All files", "*.*")]
        )
        
        if filename:
            self.selected_file.set(filename)
            self.update_upload_button_state()
    
    def load_matters(self):
        """Load matters from Clio API"""
        if not self.client:
            print("ERROR: Clio client not initialized")
            messagebox.showerror("Error", "Clio client not initialized")
            return
        
        print("Loading matters from Clio API...")
        self.status_var.set("Loading matters...")
        self.root.config(cursor="wait")
        
        def fetch_matters():
            try:
                print("Calling get_matters API...")
                matters = self.client.get_matters(limit=100)
                print(f"SUCCESS: Loaded {len(matters)} matters")
                self.root.after(0, lambda: self.display_matters(matters))
            except Exception as e:
                print(f"ERROR loading matters: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self.show_error("Failed to load matters", str(e)))
        
        thread = threading.Thread(target=fetch_matters, daemon=True)
        thread.start()
    
    def display_matters(self, matters):
        """Display matters in the listbox"""
        self.matters_list = matters
        self.filter_matters()
        self.root.config(cursor="")
        self.status_var.set(f"Loaded {len(matters)} matters")
    
    def filter_matters(self, *args):
        """Filter matters based on search text"""
        search_text = self.search_var.get().lower()
        
        self.matters_listbox.delete(0, tk.END)
        
        for matter in self.matters_list:
            display_number = matter.get("display_number", "")
            description = matter.get("description", "")
            client_name = matter.get("client", {}).get("name", "")
            
            # Create display text
            display_text = f"{display_number} - {description}"
            if client_name:
                display_text += f" ({client_name})"
            
            # Filter based on search
            if (not search_text or 
                search_text in display_text.lower() or
                search_text in str(display_number).lower() or
                search_text in description.lower() or
                search_text in client_name.lower()):
                
                self.matters_listbox.insert(tk.END, display_text)
        
        self.update_upload_button_state()
    
    def show_error(self, title, message):
        """Show error message"""
        print(f"\nERROR: {title}")
        print(f"Message: {message}")
        self.root.config(cursor="")
        messagebox.showerror(title, message)
        self.status_var.set(f"Error: {title}")
    
    def update_upload_button_state(self):
        """Enable/disable upload button based on selections"""
        if self.selected_file.get() and self.matters_listbox.curselection():
            self.upload_button.config(state="normal")
        else:
            self.upload_button.config(state="disabled")
    
    def upload_file(self):
        """Upload the selected file to the selected matter"""
        if not self.client:
            messagebox.showerror("Error", "Clio client not initialized")
            return
        
        file_path = self.selected_file.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file")
            return
        
        selection = self.matters_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a matter")
            return
        
        # Get the selected matter
        selected_index = selection[0]
        selected_text = self.matters_listbox.get(selected_index)
        
        # Find the corresponding matter in the filtered list
        search_text = self.search_var.get().lower()
        filtered_matters = []
        for matter in self.matters_list:
            display_number = matter.get("display_number", "")
            description = matter.get("description", "")
            client_name = matter.get("client", {}).get("name", "")
            display_text = f"{display_number} - {description}"
            if client_name:
                display_text += f" ({client_name})"
            
            if (not search_text or 
                search_text in display_text.lower() or
                search_text in str(display_number).lower() or
                search_text in description.lower() or
                search_text in client_name.lower()):
                filtered_matters.append(matter)
        
        if selected_index >= len(filtered_matters):
            messagebox.showerror("Error", "Invalid matter selection")
            return
        
        matter = filtered_matters[selected_index]
        matter_id = matter.get("id")
        
        # Get description
        description = self.description_text.get("1.0", tk.END).strip()
        
        # Confirm upload
        filename = Path(file_path).name
        matter_display = f"{matter.get('display_number')} - {matter.get('description')}"
        
        if not messagebox.askyesno("Confirm Upload", 
                                   f"Upload file:\n{filename}\n\n"
                                   f"To matter:\n{matter_display}\n\n"
                                   f"Continue?"):
            return
        
        # Perform upload
        self.status_var.set("Uploading file...")
        self.upload_button.config(state="disabled")
        self.root.config(cursor="wait")
        
        def perform_upload():
            try:
                print("\n" + "="*60)
                print("UPLOAD ATTEMPT")
                print("="*60)
                print(f"File: {file_path}")
                print(f"Matter ID: {matter_id}")
                print(f"Matter: {matter_display}")
                print(f"Description: {description if description else '(none)'}")
                print("\nCalling upload_file API...")
                
                result = self.client.upload_file(
                    file_path=file_path,
                    matter_id=matter_id,
                    description=description if description else None
                )
                
                print(f"\nSUCCESS: File uploaded!")
                print(f"Response: {result}")
                print("="*60 + "\n")
                self.root.after(0, lambda: self.upload_success(result))
            except Exception as e:
                print(f"\nERROR during upload: {type(e).__name__}")
                print(f"Error message: {str(e)}")
                import traceback
                traceback.print_exc()
                print("="*60 + "\n")
                self.root.after(0, lambda: self.upload_error(str(e)))
        
        thread = threading.Thread(target=perform_upload, daemon=True)
        thread.start()
    
    def upload_success(self, result):
        """Handle successful upload"""
        self.root.config(cursor="")
        self.upload_button.config(state="normal")
        
        uploaded_file = result.get("data", {}).get("name", "File")
        messagebox.showinfo("Success", f"{uploaded_file} uploaded successfully!")
        
        self.status_var.set("Upload completed successfully")
        
        # Clear selections
        self.selected_file.set("")
        self.description_text.delete("1.0", tk.END)
        self.update_upload_button_state()
    
    def upload_error(self, error_message):
        """Handle upload error"""
        self.root.config(cursor="")
        self.upload_button.config(state="normal")
        
        messagebox.showerror("Upload Failed", f"Failed to upload file:\n{error_message}")
        self.status_var.set("Upload failed")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ClioUploadUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
