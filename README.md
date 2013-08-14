ConfigMerge
===========

ConfigMerge is a Python script for creating multiple IOS/NX-OS configurations based on a template.  It requires the following:

* a template configuration file
* a variables file, which contains replacement values for every host that a config should be generated for.  

The script will parse a list of replacement variables for each host from the variables file, and then create a configuration for each device based on the template file. In short, this is an automated "Find and Replace", with some additional checks and reviews of the data to help catch errors and missing data.

##Additional Features (beyond basic find/replace)
* Provides a list of all hosts found in the variables for review file prior to export.
* Checks for duplicate hostnames in the variables file (in the case of copy/paste errors)
* Allows for a review of all variables loaded for each host, prior to export.
* Will compare all variables found in the template file and the variables file and point out any that only exist in one file or the other (orphaned).
* Once the previous check is complete, it will then check each host's list of variables to make sure it contains replacements for all vars in the template.
* --help (-h) option that explains the syntax of the command as well as available flags.
* --verbose (-v) flag that will force a variables review and give additional information during the write process.
* --quiet (-q) flag that skips all the review and questions and just exports the files (if you are feeling confident).  Will still alert on orphaned variables.

##Using the script
* Once you have the "golden" configuration tempalte.  Replace any part of the configuration file that needs to be changed per-device to a variable name (i.e. &lt;IP_ADDR&gt;)
* Once you have your template configuration file, use the cmerge.py script to create the variables file with as many hosts as you'd like, each with all the variables found in the template.

```
python cmerge.py -c <template_filename> <output_filename>
```

* Modify the output variables file with the values that each hosts should have in its own configuration.

* Run the cmerge script:

```
python cmerge.py <template_filename> <variable_filename>
```

* Gather your configuration files from the configs/ directory, which was created by the script.


