# TODO: Make script take in a parameter that determines if setup script is run, or if only repository is downloaded

# Check if python is installed with ver >= 3
$download_python = $true
$output = python --version 2>&1
if ($output -match "^Python ([0-9])") {
    $ver = [int]($matches.1 -as [int])
        if ($ver -ge 3) {
            Write-Host "Python detected."
            $download_python = $false
        }
}

if ($download_python) {
    Write-Host "Python not detected, downloading..."
    # Download python installer
    (curl -usebasicparsing https://www.python.org/downloads/).content > python_web.html
    $htmlSource = get-content -path .\python_web.html -raw
    $htmlSource -match '<h1[^>]*>Download the latest version for Windows</h1>[^<]*<p[^<]+<a[^>]+href="([^"]+)"'
    $url = $Matches.1
    invoke-webrequest -uri $url -outfile .\python_install.exe

    # Install python
    start-process -filepath .\python_install.exe -argumentlist "/passive PrependPath=1 Include_test=0" -Wait

    # Update the current powershell sessions path variable to the newly created ones
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', [System.EnvironmentVariableTarget]::User)
}

# Download sentinel alert repository
Write-Host "Downloading and extracting repository."
invoke-webrequest -uri https://github.com/9cco/sentinel-alerts/archive/refs/heads/main.zip -outfile sentinel-alerts.zip
expand-archive -force -path .\sentinel-alerts.zip -DestinationPath .

# Clean up files
rm .\sentinel-alerts.zip

if ($download_python) {
    rm .\python_web.html
    rm .\python_install.exe
}

cd .\sentinel-alerts-main

# Remove duplicates of the install scripts
rm .\install.ps1
#rm ".\Install Sentinel Alerts.lnk"

Write-Host "Creating shortcut for hotkey execution of script"
# Create a shortcut to the python script and put it on the desktop with shortcut 
# CTRL + ALT + Q
$source_file_path = (get-location).path + "\sentinel_alerts.py"
$shortcut_path = [System.Environment]::GetFolderPath("Desktop") + "\sentinel_alerts.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcut_path)
$Shortcut.TargetPath = $source_file_path
$Shortcut.Hotkey = "CTRL+ALT+Q"
$Shortcut.WorkingDirectory = (get-location).path
$Shortcut.Save()

# Installing requirements
Write-Host "Installing required modules with pip from requirements.txt`n`n-----------------------------------------------"
pip install -r requirements.txt 2>&1
Write-Host "-----------------------------------------------`n"

Write-Host "Starting python setup script"
python .\setup.py