
"""
MAP Client Plugin Step
"""
import json

import os
import sys
import argparse
import glob
import pandas as pd
from PySide2 import QtGui
from mapclient.mountpoints.workflowstep import WorkflowStepMountPoint
from mapclientplugins.heartdataconverterstep.configuredialog import ConfigureDialog
from mapclientplugins.heartdataconverterstep.app import ProgramArguments, read_csv, write_ex


class HeartDataConverterStep(WorkflowStepMountPoint):
    """
    Skeleton step which is intended to be a helpful starting point
    for new steps.
    """

    def __init__(self, location):
        super(HeartDataConverterStep, self).__init__('Heart Data Converter', location)
        self._configured = False # A step cannot be executed until it has been configured.
        self._category = 'Utility'
        # Add any other initialisation code here:
        self._icon =  QtGui.QImage(':/heartdataconverterstep/images/utility.png')
        # Ports:
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#provides',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'))
        # Port data:
        self._port0_inputDataFile = None # 'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'
        self._port1_inputDataFile = None # 'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'
        self._port2_outputExFile = None # 'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'
        # Config:
        self._config = {}
        self._config['identifier'] = ''

    def execute(self):
        """
        Add your code here that will kick off the execution of the step.
        Make sure you call the _doneExecution() method when finished.  This method
        may be connected up to a button in a widget for example.
        """
        # Put your execute step code here before calling the '_doneExecution' method.
        args = ProgramArguments()
        args.input_csvs=self._port0_inputDataFile
        args.output_ex=self._port1_inputDataFile
        if args.input_csvs:
            if os.path.exists(args.input_csvs):
                n_frames = len(glob.glob(os.path.abspath(args.input_csvs)+"\\AV*.csv"))
                contents = read_csv(args.input_csvs,n_frames)
                if n_frames > 1:
                    for frame, data in contents.items():
                        if args.output_ex is None:
                            output_ex = os.path.join(args.input_csvs, 'combined_{}.ex'.format(frame))
                        else:
                            output_ex = os.path.join(args.output_ex, 'combined_{}.ex'.format(frame))
                        write_ex(output_ex, data)
                else:
                    if args.output_ex is None:
                        output_ex = os.path.join(args.input_csvs, 'combined.ex')
                    else:
                        output_ex = os.path.join(args.output_ex, 'combined.ex')
                    write_ex(output_ex, contents)
                self._port2_outputExFile=os.path.abspath(output_ex+'\\..')
            else:
                raise TypeError('no path to input')
        else:
            raise TypeError('no input')
        self._doneExecution()

    def setPortData(self, index, dataIn):
        """
        Add your code here that will set the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        uses port for this step then the index can be ignored.

        :param index: Index of the port to return.
        :param dataIn: The data to set for the port at the given index.
        """
        if index == 0:
            self._port0_inputDataFile = dataIn # 'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'
        elif index == 1:
            self._port1_inputDataFile = dataIn # 'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'

    def getPortData(self, index):
        """
        Add your code here that will return the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        provides port for this step then the index can be ignored.

        :param index: Index of the port to return.
        """
        return self._port2_outputExFile # 'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'

    def configure(self):
        """
        This function will be called when the configure icon on the step is
        clicked.  It is appropriate to display a configuration dialog at this
        time.  If the conditions for the configuration of this step are complete
        then set:
            self._configured = True
        """
        dlg = ConfigureDialog(self._main_window)
        dlg.identifierOccursCount = self._identifierOccursCount
        dlg.setConfig(self._config)
        dlg.validate()
        dlg.setModal(True)

        if dlg.exec_():
            self._config = dlg.getConfig()

        self._configured = dlg.validate()
        self._configuredObserver()

    def getIdentifier(self):
        """
        The identifier is a string that must be unique within a workflow.
        """
        return self._config['identifier']

    def setIdentifier(self, identifier):
        """
        The framework will set the identifier for this step when it is loaded.
        """
        self._config['identifier'] = identifier

    def serialize(self):
        """
        Add code to serialize this step to string.  This method should
        implement the opposite of 'deserialize'.
        """
        return json.dumps(self._config, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def deserialize(self, string):
        """
        Add code to deserialize this step from string.  This method should
        implement the opposite of 'serialize'.

        :param string: JSON representation of the configuration in a string.
        """
        self._config.update(json.loads(string))

        d = ConfigureDialog()
        d.identifierOccursCount = self._identifierOccursCount
        d.setConfig(self._config)
        self._configured = d.validate()


