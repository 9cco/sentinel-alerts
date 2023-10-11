# Setup script for sentinel_alerts

import sys
import os
import json
import time
import tkinter as tk
from tkinter import filedialog

# Create a UI loop for inserting customer names and code
def getCodeNames():
    print("\n######################################\nConfigure customer code names.\n This will be used when generating the filenames of the reports. You can omit any 'AS' etc. in the customer names.\n\nInsert 'x' as the code name to exit and save.\n")
    key = ''
    code_dict = {"example-code" : "Customer Name"}
    while True:
        key = input("Customer code: ")
        if key == 'x':
            break
        value = input("Customer name: ")
        code_dict[key] = value
        
    print("######################################\n")
    return code_dict

# Shows a button with the specified text in the middle of the screen
def flashButton(text):

    # Let user specify path to code directory
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    width = 300
    height = 100
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg="white")
    root.title("Folder Selector")
    browse_button = tk.Button(root, text=text, command=lambda: root.destroy(), bg="pink", fg="black", font=("Verdana", 16))
    #browse_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    browse_button.pack(expand=True, ipadx=5, ipady=5)
    
    root.mainloop()
   
    

def main(argv):
    
    codes_fn = "code_names.json"
    settings_fn = "settings.conf"
    output_fn = "output.txt"
    example_fn = "example_output.txt"

    flashButton("Select Output Folder")
    folder_path = os.path.normpath(filedialog.askdirectory())
    if not os.path.isdir(folder_path):
        raise Exception("ERROR: cannot find directory {folder_path}.")
    
    #print(folder_string)

    # Get all the code names for the customers
    codes_dict = getCodeNames()
    current_folder = os.path.normpath(os.path.abspath(''))
    code_path = os.path.normpath(current_folder + "/" + codes_fn)
    
    # Then we save this to a file
    if os.path.exists(code_path):
        choice = input("File already exists at '" + code_path + "'. Overwrite (y/n)? ")
        if not 'y' in choice.lower():
            exit()
    with open(code_path, 'w') as f:
        print(json.dumps(codes_dict, indent=4), file=f)
    
    # Determine available text program
    editor_path = "C:\\Program Files\\Notepad++\\notepad++.exe"
    if not os.path.exists(editor_path):
        editor_path = "C:\\Program Files (x86)\\Notepad++\\notepad++.exe"
        if not os.path.exists(editor_path):
            flashButton("Select text editor exe file")
            editor_path = filedialog.askopenfilename(title="Choose text editor", filetypes = [("Executable files", "*.exe")])
            if not os.path.exists(editor_path):
                editor_path = "C:\\Windows\\System32\\notepad.exe"
                if not os.path.exists(editor_path):
                    raise Exception("ERROR: cannot find notepad. Is this even Windows?")
    
    # Now we are ready to set up the settings dictionary
    settings_dict = {"output-folder" : folder_path, "output-filename" : output_fn, "code-names" : code_path, "text-program-path" : "\"" + editor_path + "\"", "auto-update" : True, "remote-url" : "https://raw.githubusercontent.com/9cco/sentinel-alerts/main/sentinel_alerts.py", "check-interval" : 4, "last-check-fn" : "last_check.dat", "repo-url" : "https://github.com/9cco/web_test/archive/refs/heads/main.zip"}
    
    settings_path = os.path.normpath(current_folder + "/" + settings_fn)
    if os.path.exists(settings_path):
        choice = input("File already exists at '" + settings_path + "'. Overwrite (y/n)? ")
        if not 'y' in choice.lower():
            exit()
    with open(settings_path, 'w') as f:
        print(json.dumps(settings_dict, indent=4, sort_keys=True), file=f, end='')
    
    # Write timestamp of update
    with open(settings_dict['last-check-fn'], 'w') as f:
        print(int(time.time()), file=f, end='')
    
    print("\nSuccessfully setup sentinel_alerts.py!\nAttempt to run it by clicking CTRL + ALT + Q")
    
    # Copy example output file to output directory such that something exists.
    with open(example_fn, 'r') as f:
        example_file = f.read()
    output_path = os.path.normpath(folder_path + "/" + output_fn)
    if os.path.exists(output_path):
        choice = input("File already exists at '" + output_path + "'. Overwrite (y/n)? ")
        if not 'y' in choice.lower():
            exit()
    with open(output_path, 'w') as f:
        print(example_file, file=f, end='')
    
    input("Type any key to exit installer...")

if __name__ == "__main__":
   main(sys.argv[1:])
