import arcpy
import os

class Toolbox(object):
    def __init__(self):
        self.label = "Toolbox"
        self.alias = ""
        self.tools = [BuildingProximity]

class BuildingProximity(object):
    def __init__(self):
        self.label = "BuildingProximity"
        self.description = "Determine which buildings on TAMU's campus are near a targeted building"
        self.canRunInBackground = False
        self.category = "Building Tools"

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="GDB Folder", 
            name="gdb_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )
        param1 = arcpy.Parameter(
            displayName="GDB Name",
            name="gdb_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param2 = arcpy.Parameter(
            displayName="Garage CSV File",
            name="garage_csv_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )        
        param3 = arcpy.Parameter(
            displayName="Garage Layer Name",
            name="garage_layer_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )        
        param4 = arcpy.Parameter(
            displayName="Campus GDB",
            name="campus_gdb",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )
        param5 = arcpy.Parameter(
            displayName="Buffer Radius",
            name="buffer_radius",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
        )
        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        try:
            # Enable overwriting output
            arcpy.env.overwriteOutput = True

            folder_path = parameters[0].valueAsText
            gdb_name = parameters[1].valueAsText
            gdb_path = os.path.join(folder_path, gdb_name + ".gdb")

            # Create File Geodatabase
            if not arcpy.Exists(gdb_path):
                arcpy.AddMessage(f"Creating geodatabase: {gdb_path}")
                arcpy.CreateFileGDB_management(folder_path, gdb_name)
            else:
                arcpy.AddMessage(f"Geodatabase already exists: {gdb_path}")

            csv_path = parameters[2].valueAsText
            garage_layer_name = parameters[3].valueAsText

            # Create XY Event Layer
            arcpy.AddMessage("Creating XY Event Layer")
            garages = arcpy.MakeXYEventLayer_management(csv_path, 'X', 'Y', garage_layer_name)

            # Feature Class to Geodatabase
            arcpy.AddMessage("Converting Feature Class to Geodatabase")
            arcpy.FeatureClassToGeodatabase_conversion(garages, gdb_path)
            garage_points = os.path.join(gdb_path, garage_layer_name)

            campus = parameters[4].valueAsText
            buildings_campus = os.path.join(campus, 'Structures')
            buildings = os.path.join(gdb_path, 'Buildings')

            # Copy Buildings
            arcpy.AddMessage("Copying Buildings")
            arcpy.Copy_management(buildings_campus, buildings)

            # Project Garage Points
            arcpy.AddMessage("Projecting Garage Points")
            spatial_ref = arcpy.Describe(buildings).spatialReference
            garage_points_reproj = os.path.join(gdb_path, 'garage_points_reproj')
            arcpy.Project_management(garage_points, garage_points_reproj, spatial_ref)

            # Buffer Analysis
            arcpy.AddMessage("Performing Buffer Analysis")
            buffer_distance = parameters[5].value
            garage_buffer = os.path.join(gdb_path, 'garage_points_buffer')
            arcpy.Buffer_analysis(garage_points_reproj, garage_buffer, buffer_distance)

            # Intersect Analysis
            arcpy.AddMessage("Performing Intersect Analysis")
            garage_building_intersect = os.path.join(gdb_path, 'garage_building_intersect')
            arcpy.Intersect_analysis([garage_buffer, buildings], garage_building_intersect, 'ALL')

            # Export to CSV
            arcpy.AddMessage("Exporting to CSV")
            output_csv = os.path.join(arcpy.env.workspace, 'nearby_buildings.csv')
            arcpy.TableToTable_conversion(garage_building_intersect, arcpy.env.workspace, 'nearby_buildings.csv')

            arcpy.AddMessage(f"Output CSV created: {output_csv}")

        except arcpy.ExecuteError:
            arcpy.AddError(arcpy.GetMessages(2))
        except Exception as e:
            arcpy.AddError(f"An error occurred: {str(e)}")

        return

