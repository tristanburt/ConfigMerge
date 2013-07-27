import argparse
import os
import re

#=============FUNCTION DEFINITIONS===============#
def hline():
    """This function simply prints a line of 60 "-" chars, to add divisions to screen output"""
    print "-" * 60
    
    
def parse_vars(file):
    """This function takes the file with all the variable and their values, listed for each host, and 
        puts it into a data structure that can later be used to write out each config script.  It also 
        tracks the names of hosts found in the file and returns those for quick review prior to exporting
        the configurations.
        
        The data structure is a dictionary with each hostname as the key, and the value being another 
        dictionary (sub-dictionary?) with each find/replace key and its associated value)"""
        
    #Reset file position to beginnig (just in case)
    file.seek(0)
    host_list = []
    dict_vars = {}
    #This variable tracks whether the line being parsed is part of a host "block" of variables or not.
    hostblock = 0

    for line in file:
        #Ignore comment lines
        if line.startswith("#"):
                pass
                
        #Use a marker so we know if we are inside of a particular host's block of variables.  When we see a
        #HOSTNAME var, it is set to 1, at <--END--> it is set back to 0.
        elif "<--END-->" in line:
            hostblock = 0

        #This string "::" is used to separate the key and value in the variable file.  If any line doesn't
        #have this (with exception of the END line, shown above), ignore it and print an error.
        elif "::" not in line:
            print "Did NOT find Seperator '%r'. Line ignored" % line

        #If we find a HOSTNAME variable, but the function thinks we are still in a host's block of variables, 
        #then throw an error and exit.
        elif "<HOSTNAME>" in line and hostblock == 1:
            hline()
            print "ERROR: <HOSTNAME> found inside another host's variable block."
            print "ERROR LINE: '%r'" % line
            print "Exiting program. Please correct line and try again."
            exit(0)
            
        #HOSTNAME variable after an <--END--> line (hostblock=0) triggers the start of a new host block, and
        #creates an entry in the dictionary for the host.
        elif "<HOSTNAME>" in line and hostblock == 0:
            #Split the variable (<HOSTNAME>) from the value
            label, hostname = line.split('::')
            hostname = hostname.rstrip()
            for imported_host in host_list:
                if hostname == imported_host:
                    print "ERROR: DUPLICATE HOSTNAME IN VARIABLES FILE. EXITING..."
                    exit(0)
            hostblock = 1
            #Create an entry in the dictionary for the host.  The value will be another dictionary.
            host_list.append(hostname)
            dict_vars[hostname] = {}
            #The first value of the sub-dictionary will be the <HOSTNAME> variable and actual hostname for
            #this device
            dict_vars[hostname][label] = hostname
        
        #If the other statements don't match, and we are inside a host's block of variables, then assume
        #this line is a variable and add it to the sub-dictionary for the particular host.    
        elif hostblock == 1:
            #This should match all find/replace lines under a particular hostname.  This code just adds
            #the pairs to the sub-dictionary for the associated host.
            key, value = line.split('::')
            value = value.rstrip()
            dict_vars[hostname][key] = value

        else:
            #If this section matches a line, something was wrong with the file.  It prints an output of
            #the line and under which host this occurred to help track down the error (for example, it
            #could be HOSTNAME line that had an error, so all lines for that host will match this)
            print "INVALID LINE in %s: '%r'" % (hostname, line)
            
    #Return the list of hosts, the host count, and the data structure to the main program.
    return host_list, dict_vars
    
    
def write_configs(vars, template):
    """This template writes each host's configuration file.  It should be passed both the template file
        to use, as well as the data structure generated by the parse_vars() function."""
        
    if args.verbose:
        hline()
    for host in vars:
        #reset the template read position to start for each host
        template.seek(0)
        #create file name based on hostname of the device
        filename = host + ".txt"
        hostinfo = vars[host]
        #Check that the "configs" directory exists.  If not, create it.
        if not os.path.exists("configs"):
            os.makedirs("configs")
        dstfile = open("./configs/" + filename, 'w')
        if args.verbose:
            print "Starting write of file %s." % filename
            hline()
        for line in template:
            # For each line of the template, do a search for each find/replace "key".  If it is found
            # replace it with the actual value.  Each line is process for every find/replace key in case
            # the line has more than one.  i.e.  ip address <INSIDE_IP> <INSIDE_MASK>
            ok_to_write = True
            for key, value in hostinfo.iteritems():
                if key in line:
                    if value == "":
                        #Do not write the line if there is no value for the variable that matched the line
                        ok_to_write = False
                        if args.verbose:
                            print "Found empty value for variable %s. Line '%s' removed." % (key, line)
                    else:
                        line = line.replace(key,value)
                        if args.verbose:
                            print "Found an instance of %s and replaced it with '%s'" % (key, value)
            else:
                #After the line has been checked/modified for all applicable keys (for loop completed), 
                #and the value for the variable wasn't empty, write the line to the output file.
                if ok_to_write:
                    dstfile.write(line)
        if args.verbose:
            print "Configuration %s has been completed" % filename
            hline()
    else:
        #Once the entire loop has finished, all lines in the template have been modified and written.  
        #Close the file.
        print "Configuration files exported."
        dstfile.close()
        
                
def varprint(vars):
    """This should be passed the data structure with all the hostname find/replace variables in it.
        This function will crawl the data structure to list all find/replace variables and values
        grouped by the host they are meant for."""
        
    hline()
    #Loop through the primary dictionary (one entry per host)
    for host in host_list:  #References global host_list
        print "Variables for device %s:" % host
        hline()
        #Loop through the secondary dictionary, which is all variables for that host
        for skey, value in vars[host].items():
            print "KEY: %s , VALUE: %s" % (skey, value)
        else:
            hline()
            #Pause after each host's output.  Allow a method to quit should the user see some 
            #incorrect data
            pause = raw_input("Press ENTER to Continue (q to QUIT)")
            if pause.lower() == "q":
                print "EXITING DUE TO USER REQUEST"
                exit(0)
            hline()
    else:
        hline()
        print "DONE"
        hline()


def unique_vars(file):
    """This function searches the file for all unique find/replace variables, and returns a list
        of unique variables"""
        
    #A list to collect every variable delimited by < >.  All instances (duplicates) will be added.
    all_vars = []

    file.seek(0)
    #Compile a regex that searches for non-whitespace chars between a < and >
    reg=re.compile(r"<\S*?>")
    for line in file:
        #Use findall because some lines may have more than 1 variable on it. Output is a list.
        linematch = reg.findall(line)
        for item in linematch:
            #ignore this special string that only marks the end of a hosts variable block    
            if item == "<--END-->":
                pass
            else:
                #If it is anything else, append it to the list of variables found
                all_vars.append(item)
    else:
        #Sets can't have duplicate items, so by converting the list to a set and back, we will
        #be left with a list with only one copy of each unique variable.
        unique_vars = list(set(all_vars))
    return unique_vars


def var_check(filename1, filename2, vars_1, vars_2):
    """This function will take the list of unique variables found in two files and report if they match.
        If they do not match, then this function will output the difference.  This function will print
        the results and returns a boolean expression on whether the two var lists are identical"""
        
    #Using the "&" operation between 2 sets gives the common items.  If the common item set isn't the 
    #same length as both the var_1 and var_2 sets, then they aren't exactly the same.
    common_set = set(vars_1) & set(vars_2)
    if len(common_set) == len(set(vars_1)) and len(common_set) == len(set(vars_2)):
        print "All variables match between %s and %s\n" % (filename1, filename2)
        return True #because both lists were identical
    else:
        print "WARNING:"
        #Figure out which vars are left when you subtract one set from the other.  Whatever is left only exists
        #in that one file.  Those variables will not be replaced in the output script.
        if len(set(vars_1) - set(vars_2)) != 0:
            print "Variables that only exist in %s are: %s\n" % (filename1, list(set(vars_1) - set(vars_2)))
        if len(set(vars_2) - set(vars_1)) != 0:
            print "Variables that only exist in %s are: %s\n" % (filename2, list(set(vars_2) - set(vars_1)))
        return False #because one list contained more (or different) vars than the other
        

def review_vars():
    """This is a decision tree on whether the user wants to review the variables before
        allowing the program to export all the config files.  It will loop indefinitely until
        a valid respose is received."""
        
    if args.verbose:
        #If verbose flag was selected, automatically review instead of asking, then move onto config write.
        varprint(importdata)
        accept_write()
        exit(0)
    while True:
        answ2 = raw_input("Would you like to review the imported vars before generating configs? ")
        if answ2.lower() == "yes" or answ2.lower() == "y":
            varprint(importdata)
            accept_write()
            break
        elif answ2.lower() == "no" or answ2.lower() == "n":
            accept_write()
            break
        else:
            print "I did not understand that response"
    
    
def accept_write():
    """This is a decision tree on whether the user wants to export the configuration files."""
    while True:
        answ3 = raw_input("Would you like to export the config files? ")
        if answ3.lower() == "yes" or answ3.lower() == "y":
            write_configs(importdata, template)
            template.close()
            break
        elif answ3.lower() == "no" or answ3.lower() == "n":
            print "Configuration files have NOT been exported.  Exiting..."
            exit(0)
        else:
            print "I did not understand that answer"
    
    
#=================BEGIN MAIN PROGRAM=====================#

#This section manages the (-h) help output, with the help of ArgParse, and makes sure that all required arguments are passed to the script when run.
parser = argparse.ArgumentParser(description="This script will generate a configuration file for multiple devices.  It needs a 'template' configuration file that uses variable names in every location where each device needs a different value.  This script also needs a 'variables' file that lists the variables and associated replacement value for the device.  This variables file can contain sections for multiple configuration files.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action="store_true", help="Will provide a more verbose output and automatically trigger a review of all parsed variables")
group.add_argument("-q", "--quiet", action="store_true", help="Will provide minimal output and will automatically skip all review questions")
parser.add_argument("template", help="Name of the file that is the configuration template")
parser.add_argument("variables", help="Name of the file that contains find/replace variables for each device")
#Assign input arguments to the "args" variable for reference later in the script.
args = parser.parse_args()

hline()
print""

var_file = open(args.variables, 'r')
template = open(args.template, 'r')

#Call function to parse variable files and assign outputs to variables
host_list, importdata = parse_vars(var_file)

#Gather unique variables from each file, so they can be compared.
var_file_u = unique_vars(var_file)
template_u = unique_vars(template)
identical = var_check(args.variables, args.template, var_file_u, template_u)

#If there were errors in the comparison, allow the user to decide if they want to continue or not.
if not identical:
    while True:
        answ = raw_input("Would you like to continue with the merge anyway? ")
        if answ.lower() == "yes" or answ.lower() == "y":
            break
        elif answ.lower() == "no" or answ.lower() == "n":
            print "Please modify your input files and try again.  Thanks!"
            var_file.close()
            template.close()
            exit(0)
        else:
            print "I did not understand that response."
    

#Close variables file -- no longer needed
var_file.close()


if args.quiet:
    #If quiet flag was set, skip the review and get straight to the config writing
    write_configs(importdata, template)
else:
    #Otherwise, give brief review of the hosts found
    print "Found settings for %d config files.  They are: " % len(host_list)
    x = 1
    for host in host_list:
        print "%d. %s" % (x, host)
        x = x + 1
    print ""
    #First Decision tree.  Allows user to decide if brief review looks accurate.
    #Other decision tree functions are called depending on the response.
    while True:
        answ = raw_input("Is this correct? (Type 'yes' to continue) ")
        if answ.lower() == "yes" or answ.lower() == "y":
            review_vars()
            break
        elif answ.lower() == "no" or answ.lower() == "n":
            print "Please modify your vars file and try again.  Thanks!"
            template.close()
            exit(0)
        else:
            print "I did not understand that response."

