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
    with open(path, 'r', encoding="utf8") as f:
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
        if m:
            key = m.group(1).lower().strip()
            value = m.group(2).strip()
            # Take special care of cusetomer name line
            if key == "customername":
                alert_dict['customer-name'] = value
            else:
                alert_dict[key] = value
            last_key = key

        else:
            # If the line doesn't contain a key like it doesn't after the description field in Sentinelv2 alerts, then we just add the line to the last non-zero key.
            if last_key != "":
                alert_dict[key] += " " + line

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
    
    string += returnIfNonempty("Description", alert_dict, "info description")   # Sentinel alert
    string += returnIfNonempty("Description", alert_dict, "incident title")     # Defender alert
    string += returnIfNonempty("Category", alert_dict, "category")
    string += returnIfNonempty("Pattern", alert_dict, "info sub name")
    string += returnIfNonempty("\nDetails", alert_dict, "description") #Sentinel v2 alert
    string += returnIfNonempty("\nDetails", alert_dict, "title")          # Defender alert
    
    if 'process name' in alert_dict:
        string += "\n**Initiating process**  \nName:  " + alert_dict['process name'] + "\n"
        string += returnIfNonempty("Path", alert_dict, "process path")
        string += returnIfNonempty("Command", alert_dict, "process commandline", enclose="`")
        string += returnIfNonempty("SHA256", alert_dict, "process sha256")
    
    if 'parent process' in alert_dict:
        string += "\n**Parent process**  \nName:  " + alert_dict['parent process'] + "\n"
        string += returnIfNonempty("Command", alert_dict, "parent process commandline", enclose="`")
    
    # Defender output
    if 'process' in alert_dict:
        process_cmds = [c.strip() for c in alert_dict['process'].split(',')]
        processes = [p.strip() for p in alert_dict['process exec'].split(',')]
        process_paths = [p.strip() for p in alert_dict['process path'].split(',')]
        process_shas = [h.strip() for h in alert_dict['process hash sha256'].split(',')]
        process_users = [u.strip() for u in alert_dict['process owner'].split(',')]
        process_parents = [p.strip() for p in alert_dict['parent process exec'].split(',')]
        
        N = min(len(process_cmds), len(processes), len(process_shas), len(process_users), len(process_parents))
        for i in range(0, N):
            string += "\n**Execution flow " + str(i+1) + "**\n"
            string += "Parent Process:  " + process_parents[i] + "\n"
            string += "Process:  " + processes[i] + "\n"
            string += "Path:  " + process_paths[i] + "\n"
            string += "CMD:  `" + process_cmds[i] + "`\n"
            string += "User:  " + process_users[i] + "\n"
            string += "SHA256:  " + process_shas[i] + "\n"
    
    string += returnIfNonempty("\nE-mail", alert_dict, 'mailbox address', enclose="`")
    
    return string

# Generate host section for a sentinel alert
def sentinelHost(alert_dict):
    report_who = ""
    report_who += "Host:  "
    if 'asset key' in alert_dict and not ('asset ipv4' in alert_dict and alert_dict['asset key'] == alert_dict['asset ipv4']):
        report_who += alert_dict['asset key']
    report_who += "\nOS:  \n"
    report_who += "IP:  "
    if 'asset ipv4' in alert_dict:
        report_who += alert_dict['asset ipv4']
    report_who += "\n"
    return report_who

# Generate host-section for a defender-alert
def defenderHost(alert_dict):
    report_host = ""
    hosts = alert_dict['dvc'].split(',')
    
    for host in hosts[:-1]:
        host = host.strip()
        report_host += "Host:  " + host + "\n"
        report_host += "OS:  \n\n"
    
    report_host += "Host:  " + hosts[-1].strip() + "\n"
    report_host += "OS:  \n"
    
    return report_host

def returnUser(user):
    string = "User:  " + user + "\n"
    string += "Name:  \n\n"
    return string

# Generate 'Who'-section of an alert.
def reportWho(alert_dict, line_string):
    report_who = ""
    if 'asset user' in alert_dict:
        report_who += returnUser(alert_dict['asset user'])
    elif 'user' in alert_dict:
        users = alert_dict['user'].split(',')
        for user in users:
            user = user.strip()
            report_who += returnUser(user)
    else:
        returnUser("")

    # If it is a sentinel alert, then it will contain asset key or asset ipv4
    if 'asset key' in alert_dict or 'asset ipv4' in alert_dict:
        report_who += sentinelHost(alert_dict)
    elif 'dvc' in alert_dict:
        report_who += defenderHost(alert_dict)
    if 'ip' in alert_dict:
        report_who += returnIfNonempty("IP", alert_dict, "ip")
        
    
    return report_who


# Generates the report string from the alert dictionary
def generateReportString(alert_dict):
    
    # Title
    report_title = ''
    report_title += alert_dict['case-number']
    if 'incident id' in alert_dict:
        report_title += " | Incident-ID " + alert_dict['incident id']
    report_title += "\n==================================\n\n\n"
    
    line_string = "-------------------------------------------------------\n\n"
    
    # Who
    report_who = 'Who:  \n' + line_string
    report_who += reportWho(alert_dict, line_string)
    
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
        with open(path, "w", encoding="utf8") as f:
            print(string, file=f, end='')
