from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer, QgsField,  QgsFields
from PyQt5.QtCore import  QMetaType, QVariant
from PyQt5.QtGui import QIcon
from fitparse import FitFile
import os

class FitLoaderPlugin:
    def __init__(self, iface):
        """Initialize the plugin with the QGIS interface."""
        self.iface = iface
        self.action = None

    def initGui(self):
        """Create and add the plugin's action to the QGIS GUI."""
        
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "fit_loader.png")
        
        # Create an action in the main QGIS window
        self.action = QAction(QIcon(icon_path), "Load FIT Activity", self.iface.mainWindow())
        # Connect the action to the run method
        self.action.triggered.connect(self.run)
        # Add the action to the QGIS plugin menu under "FitLoader"
        self.iface.addPluginToMenu("&FitLoader", self.action)
        self.iface.addToolBarIcon(self.action)


    def unload(self):
        """Remove the plugin's action from the QGIS GUI when the plugin is unloaded."""
        # Remove the action from the plugin menu
        self.iface.removePluginMenu("&FitLoader", self.action)
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        """Open a dialog to select a FIT file and process it."""
        # Open a file dialog for selecting a FIT file
        fit_path, _ = QFileDialog.getOpenFileName(None, "Select FIT File", "", "FIT Files (*.fit)")
        if not fit_path:
            return  # If no file was selected, exit the function
            
        try:
            # Load the selected FIT file using the fitparse library
            fitfile = FitFile(fit_path)
            # Call the function to create a layer from the FIT file data
            self.create_layer_from_fit(fitfile)
        except Exception as e:
            # Display an error message if loading the file fails
            QMessageBox.critical(None, "Error", f"Failed to load FIT file: {e}")

    def create_layer_from_fit(self, fitfile):
        """Create a point layer in QGIS based on the records from the FIT file."""
        # Create a new memory-based point layer with EPSG:4326 (WGS84)
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "FIT Activity Points", "memory")
        if not layer.isValid():
            # Display an error message if the layer creation fails
            QMessageBox.critical(None, "Error", "Failed to create layer")
            return

        # Get the data provider for the layer (for adding attributes and features)
        pr = layer.dataProvider()
        # Add fields (attributes) to the layer for timestamp, latitude, longitude, speed, and cadence
        

        # Prepare to store the features (points) extracted from the FIT file
        
        field_set = set()
        
        # loop to get all the keys in all the records
        for record in fitfile.get_messages("record"):
            # from record to a dictionary
            dict_record = record.get_values()
            
            if  'position_lat' not in dict_record:
                continue
            
            field_set = field_set.union(set(dict_record.keys()))
            
        fields_list = list(field_set)
        
        fields =  QgsFields()

        for field in fields_list:
            if field == 'activity_type':
                fields.append( QgsField(field, QVariant.String) )
            elif field == 'timestamp':
                #fields.append( QgsField(field) )
                fields.append( QgsField(field, QVariant.DateTime) )
            else:
                fields.append( QgsField(field, QVariant.Double) )
        
        # Integer from 0 that identifies the subtrack that correspond
        # to stop and restart in the recording data
        fields.append( QgsField('seg_num', QVariant.Int) )
        
        pr.addAttributes(fields)
        layer.updateFields()
        
        curr_seg_num = 0
        no_records = True # True iff no records before next event start
        
        # Loop through the "record" messages in the FIT file (these contain activity data)
        for msg in fitfile.messages:
            if msg.name == 'record':
                record = msg
                # from record to a dictionary
                dict_record = record.get_values()
                
                #QMessageBox.critical(None, "Qua")   
                
                # we are interested in georeferenced records
            
                if 'position_lat' not in dict_record:
                    continue
    
                dict_record['position_lat'] = dict_record['position_lat']*180/2**31
                dict_record['position_long'] = dict_record['position_long']*180/2**31
                
                #QgsMessageLog.logMessage(str(dict_record['position_lat']), 'FitLoader', 0)
    
                # Create a point geometry with longitude and latitude
                point = QgsPointXY(dict_record['position_long'], dict_record['position_lat'])
                # Create a new feature for the point
                feature = QgsFeature()
                feature.setFields(fields)
                
                # Set the feature's attributes (timestamp, lat, lon, speed, and cadence)
                for x in dict_record:
                    #QgsMessageLog.logMessage(x  , 'FitLoader', 0)
                    if x in ('timestamp', 'activity_type'):
                        feature.setAttribute(x, str(dict_record[x]) )
                    else:
                        feature.setAttribute(x, dict_record[x] )
                # Add the feature to the list of features
                feature.setGeometry(QgsGeometry.fromPointXY(point))
                feature.setAttribute('seg_num', curr_seg_num)
                pr.addFeature(feature)
                no_records = False
            elif  no_records == False and msg.name == 'event' and\
                    msg.get_values()['event'] == 'timer' and msg.get_values()['event_type'] == 'start':
                curr_seg_num += 1
                no_records = True


        # Add all the features to the layer
        #pr.addFeatures(features)
        # Add the layer to the current QGIS project
        QgsProject.instance().addMapLayer(layer)
