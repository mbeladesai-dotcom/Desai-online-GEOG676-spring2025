# -*- coding: utf-8 -*-
import time
import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [GraduatedColorsRenderer, testTool]

class testTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Tool"
        self.description = ""
        self.canRunInBackground = False
        self.category = "MapTools"

class GraduatedColorsRenderer(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "graduated color"
        self.description = "Classifies the given features by area. Larger area classes are designated by darker colors."
        self.canRunInBackground = False
        self.category = "MapTools"

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName = "Input ArcGIS Pro Project name",
            name = "aprxInputName",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )
        param1 = arcpy.Parameter(
            displayName = "Layer to classify (which layer you want to use to generate a color map)",
            name = "LayerClassifier",
            datatype = "GPLayer",
            parameterType = "Required",
            direction = "Input"
        )
        param2 = arcpy.Parameter(
            displayName = "Output location",
            name = "OutputLocation",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input"
        )
        param3 = arcpy.Parameter(
            displayName = "Output Project Name",
            name = "OutputProjectName",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # define progressor variables 
        # time for users to view progress
        readTime = 3
        # start position of the progress bar    
        start = 0
        # end position of the progress bar
        max = 100
        # The progress bar interval 
        step = 33

        # progress bar set up 
        arcpy.SetProgressor("step", "Validating Project File...", start, max, step)
        time.sleep(readTime)

        # Add message to the results pane
        arcpy.AddMessage("Validating Project File...")

        try:
            # set project file to var
            project = arcpy.mp.ArcGISProject(parameters[0].valueAsText)

            # capture first instance of map from the .aprx
            campus = project.listMaps('Map')[0]

            # increment Progressor
            arcpy.SetProgressorPosition(start + step)
            arcpy.SetProgressorLabel("Locating Map Layer...")
            time.sleep(readTime)
            arcpy.AddMessage("Locating Map Layer...")

            # loop through map layers
            for layer in campus.listLayers():
                # Check if Layer is a feature layer 
                if layer.isFeatureLayer:
                    #copy layer Symbology
                    symbology = layer.symbology
                    # ensure Symbology renderer has attributes
                    if hasattr(symbology, 'renderer'):
                        # check layer name 
                        if layer.name == parameters[1].valueAsText: # ensure it matches input layer

                            # increment Progressor 
                            arcpy.SetProgressorPosition(start + step*2) # 66% completed
                            arcpy.SetProgressorLabel("Calculating and classifying ...")
                            time.sleep(readTime)
                            arcpy.AddMessage("Calculating and Classifying...")

                            # update the copy's Renderer to "Graduated Colors Renderer"
                            symbology.updateRenderer("GraduatedColorsRenderer")

                            # Check for Shape_Area field and set classification field
                            if "Shape_Area" in [field.name for field in arcpy.ListFields(layer)]:
                                symbology.renderer.classificationField = "Shape_Area"
                            else:
                                arcpy.AddWarning("Shape_Area field not found. Using the first numeric field instead.")
                                numeric_fields = [field.name for field in arcpy.ListFields(layer) if field.type in ["Double", "Integer", "Single", "SmallInteger"]]
                                if numeric_fields:
                                    symbology.renderer.classificationField = numeric_fields[0]
                                else:
                                    arcpy.AddError("No numeric fields found for classification.")
                                    return
                            
                            # Set how many classes we'll have for the map
                            symbology.renderer.breakCount = 5

                            # Set Color Ramp
                            color_ramp = project.listColorRamps('Oranges (5 Classes)')
                            if color_ramp:
                                symbology.renderer.colorRamp = color_ramp[0]
                            else:
                                arcpy.AddWarning("Oranges (5 Classes) color ramp not found. Using default color ramp.")

                            # Set the layer's actual symbology equal to the copy
                            layer.symbology = symbology

                            arcpy.AddMessage("Finished Generating Layer...")
                            break
            else:
                arcpy.AddError(f"No layer named '{parameters[1].valueAsText}' found")
                return
            
            # Increment Progressor
            arcpy.SetProgressorPosition(start + step*3) #now it's set to 99%/finished
            arcpy.SetProgressorLabel("Saving...")
            time.sleep(readTime)
            arcpy.AddMessage("Saving...")

            #param 2 is folder loc and param 3 is the name of the proj
            project.saveACopy(parameters[2].valueAsText + "\\" + parameters[3].valueAsText + ".aprx")
            arcpy.AddMessage("Project saved successfully.")

        except Exception as e:
            arcpy.AddError(f"An error occurred: {str(e)}")

        return
