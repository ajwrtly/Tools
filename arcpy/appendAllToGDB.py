## appendAllToGDB.py - append all datasets from one Geodatabase to another where the names match
## SG September, 2012
## Loop through the lists of source and target datasets and try to append wherever the names match
## The tricky part is that sources and targets may have the same name but in SDE there will be prefixes on the names
## This script compares on names with no prefix.
## NB This means if you have the same table name in multiple SDE databases/instances in the same connection this script won't work for you.
# ---------------------------------------------------------------------------
# Copyright 2012-2013 Vertex3 Inc
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os, sys, traceback, xml.dom.minidom, arcpy, gzSupport


# Local variables...
debug = True
# Parameters
sourceGDB = arcpy.GetParameterAsText(0) # workspace / connection file
if sourceGDB == "#" or sourceGDB == "":
    sourceGDB = "Sample.gdb"  # you can set this to a default like this if you want.

targetGDB = arcpy.GetParameterAsText(1) # workspace / connection file
if targetGDB == "#" or targetGDB == "":
    targetGDB = "Sample(WebMercator).gdb"  # you can set this to a default like this if you want.
gzSupport.workspace = targetGDB # target Geodatabase

gzSupport.xmlFileName = arcpy.GetParameterAsText(2) # optional - xml File for list of datasets
datasetNames = []
if gzSupport.xmlFileName == "#" or gzSupport.xmlFileName == "":
    gzSupport.xmlFileName = None
else:
    xmlDoc = xml.dom.minidom.parse(gzSupport.xmlFileName)
    datasets = gzSupport.getXmlElements(xmlDoc,"Dataset")
    rootElem = gzSupport.getRootElement(xmlDoc)
    gzSupport.logTableName = rootElem.getAttributeNode("logTableName").nodeValue
    gzSupport.errorTableName = rootElem.getAttributeNode("errorTableName").nodeValue
    for dataset in datasets:
        name = dataset.getAttributeNode("name").nodeValue
        datasetNames.append(name.upper())
        
SUCCESS = 3 # parameter number for output success value
gzSupport.startLog()

def main(argv = None):
    # main function - list the source and target datasets, then append where there is a match on non-prefixed name
    success = True
    arcpy.ClearWorkspaceCache_management(gzSupport.workspace)
    try:
        sources = gzSupport.listDatasets(sourceGDB)
        sNames = sources[0]
        sFullNames = sources[1]
        targets = gzSupport.listDatasets(targetGDB)
        tNames = targets[0]
        tFullNames = targets[1]
        s = 0    
        arcpy.SetProgressor("Step","Appending rows...",0,len(sFullNames),1)
        for name in sNames:
            arcpy.SetProgressorPosition(s)
            arcpy.SetProgressorLabel(" Deleting rows in " + name + "...")
            # for each source name
            if debug:
                gzSupport.addMessage(name)
            try:
                # look for the matching name in target names
                t = tNames.index(name)
            except:
                # will get here if no match
                t = -1
            if t > -1:
                # append if there is a match
                if len(datasetNames) == 0 or name.upper() in datasetNames:
                    retVal = doAppend(sFullNames[s],tFullNames[t])
                    gzSupport.logDatasetProcess(name,"appendAlltoGDB",retVal)
                    if retVal == False:
                        success = False
                else:
                    gzSupport.addMessage("Skipping "  + name)

            s = s + 1
    except:
        gzSupport.showTraceback()
        gzSupport.addError("Unable to append datasets")
        success = False
        gzSupport.logDatasetProcess(name,"appendAlltoGDB",success)
    finally:
        arcpy.SetParameter(SUCCESS, success)
        arcpy.ResetProgressor()
        gzSupport.closeLog()
        arcpy.ClearWorkspaceCache_management(targetGDB)

def doAppend(source,target):
    # perform the append from a source table to a target table
    success = False
    if arcpy.Exists(target):
        gzSupport.addMessage("Appending " + source + " |TO| " + target)
        arcpy.Append_management(source,target, "NO_TEST")
        success = True
        if debug:
            gzSupport.addMessage("completed")
    else:
        gzSupport.addMessage("Target: " + target + " does not exist")
    return success

if __name__ == "__main__":
    main()

    