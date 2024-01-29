# Main-file reserved for future feature creep and command line options
# v. 0.0.1

from file_functions import loadSettings, readInputFile, formatAlertDict, generateReportString
from file_functions import generateFileName, writeStringToFile

from auto_update import update

import os
import sys

def main(argv):
    
    settings_dict = loadSettings()
    input_path = os.path.normpath(settings_dict['output-folder'] + "/" + settings_dict['output-filename'])
    
    input = readInputFile(input_path)
    alert_dict = formatAlertDict(input)

    if 'incident url' in alert_dict:
        print("Debug hello world")
        os.system("echo " + alert_dict['incident url'] + " | clip")
    
    report = generateReportString(alert_dict)
    
    output_fn = generateFileName(alert_dict, settings_dict['code-names'])
    output_path = os.path.normpath(settings_dict['output-folder'] + "/" + output_fn)
    
    writeStringToFile(output_path, report)
    
    cmd = settings_dict['text-program-path'] + " \"" + output_path + "\""
    os.system(cmd)
    
    if settings_dict['auto-update']:
       update(settings_dict)
        
    return

if __name__ == "__main__":
   main(sys.argv[1:])
