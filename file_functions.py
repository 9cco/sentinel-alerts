# File functions

import os
import json
import re

# Functionality for interacting with files

# Function loads a json file from a specified path
def loadJsonFile(path):
    
    if os.path.exists(path):
        with open(path, "r") as f:
            output = json.load(f)
        return output
    else:
        raise ValueError(f"ERROR in loadJsonFile.\nPath: {path} does not exist.")

# Load the settings file in the same folder as the current script resides.
def loadSettings(filename = "settings.conf"):
    
    current_folder = os.path.normpath(os.path.abspath(''))
    path = current_folder + "/" + filename
    
    return loadJsonFile(path)

# Reads a text file into a list of lines and does a series of tests to validate the
# format of the input file.
def readInputFile(path):
    with open(path, 'r') as f:
        input = [line.strip() for line in f.readlines()]
    
    # Tests of format
    if not re.match(r"^(OCD_INC[0-9]+)", input[0]):
        raise ValueError("ERROR in readInputFile:\nCould not find case number in first line of input file at\n" + path)
    return input

# Reads a list of lines coming from CDC output and generates a dictionary
def formatAlertDict(lines):
    m = re.match(r"^(OCD_INC[0-9]+)", lines[0])
    alert_dict = {'case-number': m.group(1)}
    
    m = re.search(r"([0-9]{4}\-[0-9]{2}\-[0-9]{2})T([0-9:\.]+)Z$", lines[2])
    alert_dict['timestamp'] = m.expand(r"\g<1> \g<2> UTC")
    
    for line in lines[3:]:
        m = re.match(r"^([^:]+):[\s ]*(.*)$", line)
        key = m.group(1).lower().strip()
        value = m.group(2).strip()
        # Take special care of cusetomer name line
        if key == "customername":
            alert_dict['customer-name'] = value
        else:
            alert_dict[key] = value
    
    return alert_dict

# Reads the code dictionary pointed to by the second argument and outputs the code name
# associated with the first argument
def generateCustomerCode(customer_name, code_path):
    code_dictionary = loadJsonFile(code_path)
    
    for key in code_dictionary.keys():
        if code_dictionary[key].lower() in customer_name.lower():
            return key
    
    raise ValueError("ERROR in generateCustomerCode:\nCould not find \"" + customer_name + "\" in dictionary at\n\"" + code_path + "\"")

# Generates a file name for the report of the format "<day>_<code name>_<case_number>.md".
def generateFileName(alert_dict, code_path):

    timestamp = alert_dict['timestamp']
    m = re.match(r"^[0-9]{4}\-[0-9]{2}\-([0-9]{2})", timestamp)
    day = m.group(1)
    
    code = generateCustomerCode(alert_dict['customer-name'], code_path)
    
    return f"{day}_{code}_{alert_dict['case-number']}.md"

def returnIfNonempty(description, alert_dict, key, end="\n", enclose="", fill="  "):
    try:
        input_string = alert_dict[key]
    except KeyError:
        return ""
    if input_string != "" and input_string != "``":
        return f"{description}:{fill}{enclose}{input_string}{enclose}" + end
    else:
        return ""

def reportWhat(alert_dict, line_string):
    string = "\n\nWhat:  \n" + line_string
    string += returnIfNonempty("Description", alert_dict, "info description")
    string += returnIfNonempty("Pattern", alert_dict, "info sub name")
    
    if 'process name' in alert_dict:
        string += "\n**Initiating process**  \nName:  " + alert_dict['process name'] + "\n"
        string += returnIfNonempty("Path", alert_dict, "process path")
        string += returnIfNonempty("Command", alert_dict, "process commandline", enclose="`")
        string += returnIfNonempty("SHA256", alert_dict, "process sha256")
    
    if 'parent process' in alert_dict:
        string += "\n**Parent process**  \nName:  " + alert_dict['parent process'] + "\n"
        string += returnIfNonempty("Command", alert_dict, "parent process commandline", enclose="`")
    
    return string

# Generates the report string from the alert dictionary
def generateReportString(alert_dict):
    
    # Title
    report_title = ''
    report_title += alert_dict['case-number'] + "\n==================================\n\n\n"
    
    line_string = "----------------------------------------------------------\n\n"
    
    # Who
    report_who = 'Who:  \n' + line_string
    if 'asset user' in alert_dict:
        report_who += "User:  " + alert_dict['asset user'] + "\n"
    else:
        report_who += "User:  \n"
    report_who += "Name:  \n\n"

    report_who += "Host:  "
    if 'asset key' in alert_dict and not ('asset ipv4' in alert_dict and alert_dict['asset key'] == alert_dict['asset ipv4']):
        report_who += alert_dict['asset key']
    report_who += "\nOS:  \n"
    report_who += "IP:  "
    if 'asset ipv4' in alert_dict:
        report_who += alert_dict['asset ipv4']
    report_who += "\n"
    
    # Where
    report_where = "\n\nWhere:  \n" + line_string
    report_where += "\n"
    
    # What
    report_what = reportWhat(alert_dict, line_string)
    
    # Why
    report_why = "\n\nWhy:  \n" + line_string
    report_why += "\n"
    
    # When
    report_when = "\n\nWhen:  \n" + line_string
    report_when += alert_dict['timestamp'] + "\n"
    
    # Closing
    report_closing = "\n\nRecommendations:  \n" + line_string + "\n" + "\n\nConclusion:  \n" + line_string + "\n\n\n"
    
    return report_title + report_who + report_where + report_what + report_why + report_when + report_closing

# Write string to file. Check with user about reading before writing to existing path.
def writeStringToFile(path, string):
    write = True
    if os.path.exists(path):
        choice = input(f"File {path} already exists. Overwrite? (y/n): ")
        if not 'y' in choice.lower():
           write = False 
           
    if write:
        with open(path, "w") as f:
            print(string, file=f, end='')