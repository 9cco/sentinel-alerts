# Sentinel Alerts

## Use

1. Paste raw text output in the file `output.txt` in the output folder you set up during installation.
2. Hit **CTRL**+**ALT**+**Q** and watch the magic happen.
3. A report file will be automatically generated in the output folder and open in your text-editor.

## Installation and setup

- Download install.ps1 and put it in the parent of a directory where you want the script to be.
- Open a powershell prompt and navigate to the file. 
- Execute the script with `.\install.ps1` and follow the on-screen instructions.
- You will be asked to input code names for customers. This is to anonymize the information on disk.
- After successfull setup, a shortcut called "sentinel-alerts.lnk" is created on your desktop with the shortcut "CTRL+ALT+Q". You can edit this to your hearts preferences.
- If you later want to edit the code names you gave your customers, you can do this by editing the json file `code_names.json`.
- Other settings can be changed by editing the json file `settings.conf`. The names of these settings are self-explanatory.


**Highlighted settings you might want to change**
- Turn off auto updating of the code by setting `"auto-update": false,`.
- Change where you want your output.txt file to be stored by changing the key `output-folder`.
- Change how often (in days) you want the program to query for new updates by changing `check-interval`.
- Change the text editor that is used to open reports by changing the key `text-program-path`. The content of this key is used in the following command to open the report file:

```cmd
"<path to text program exe>" "<path to report txt file>"
```
