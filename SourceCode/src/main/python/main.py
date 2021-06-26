import numpy as np
from numpy import array, int32
import cv2 as cv
import sys
import os
from os import path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from enum import Enum
from math import sqrt, pi
from fbs_runtime.application_context.PyQt5 import ApplicationContext

# Current version of the software
__version__ = '1.3'
COMPATIBLE_VERSIONS = [
    '0.1',
    '0.2',
    '0.3',
    '0.4',
    '0.5',
    '0.6',
    '0.7',
    '1.0',
    '1.1',
    '1.2',
    '1.3'
]

class ToolMode(Enum):
    """This enum indicates the current selected mode of operation"""
    SEL_AXON = '1' # select an axon
    SEL_MYELIN_IN = '2' # selecting myelin inside
    SEL_MYELIN_OUT = '3' # selecting myelin outside
    DESELECT = '4' # deselect previous selections
    INFO = '5' # get info about currently selected axons
    SEL_MISC = '6'
    CUT = 'Q' # draw white lines
    DRAW = 'W' # draw black lines
    ERASE = 'E' # remove lines and counters
    COUNT = '' # the overarching count mode
    COUNT_UNMYEL = 'R' # counts unmyelinated axons
    COUNT_MYEL = 'T' # counts myelinated axons

class Colors(Enum):
    """These are colors for use within the software"""
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    PINK = (228, 20, 255)
    PURPLE = (255, 20, 232)
    LIME = (5, 247, 150)
    RED_HIGHLIGHT = (135, 135, 255)
    GREEN_HIGHLIGHT = (138, 255, 175)
    CYAN_HIGHLIGHT = (241, 245, 132)
    ORANGE_HIGHLIGHT = (0, 153, 255)
    YELLOW_HIGHLIGHT = (128, 251, 255)

class Quality(Enum):
    """Quality options for image import"""
    ORIGINAL = 1
    VERY_HIGH = 0.9
    HIGH = 0.8
    MEDIUM = 0.7
    LOW = 0.6
    VERY_LOW = 0.5

image_file_extensions = 'All Files (*);;TIF Files (*.tif);;PNG Files (*.png);;'

class MainWindow(QMainWindow):
    """This is the main UI container"""
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # General window setup
        self.setWindowTitle('MyelTracer')
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.image_view = DisplayImageWidget(self)
        self.layout.addWidget(self.image_view)
        self.save_filename = None
        self.resize(800, 800)

        self.main_menu = self.menuBar()
        # File Menu
        self.file_menu = self.main_menu.addMenu('File')
        # -New
        self.new_menu_item = self.add_menu_item(
            'New', 'Ctrl+N', 'Import an image to start a new session',
            self.new, self.file_menu)
        # -Open
        self.open_menu_item = self.add_menu_item(
            'Open', 'Ctrl+O', 'Open previous session', self.open,
            self.file_menu)
        # --------
        self.file_menu.addSeparator()
        # -Save
        self.save_menu_item = self.add_menu_item(
            'Save', 'Ctrl+S', 'Save current session', self.save, self.file_menu,
            False)
        # -Save As
        self.save_as_menu_item = self.add_menu_item(
            'Save As...', 'Ctrl+Shift+S', 'Save current session as...',
            self.save_as, self.file_menu, False)
        # -Export
        self.export_menu_item = self.add_menu_item(
            'Export', 'Ctrl+E',
            'Export the data as a .csv with a reference image', self.export, 
            self.file_menu, False)
        # --------
        self.file_menu.addSeparator()
        # -Exit
        self.exit_menu_item = self.add_menu_item('Exit', 'Ctrl+Q', 
            'Exit application', self.close, self.file_menu)

        # Edit Menu
        self.edit_menu = self.main_menu.addMenu('Edit')
        self.edit_menu.setEnabled(False)
        # -Undo
        self.undo_menu_item = self.add_menu_item(
            'Undo', 'Ctrl+Z', 'Undo last action', self.image_view.undo,
            self.edit_menu, False)
        # -Redo
        self.redo_menu_item = self.add_menu_item(
            'Redo', 'Ctrl+Y', 'Redo last action', self.image_view.redo,
            self.edit_menu, False)

        # Tool Menu
        self.tool_menu = self.main_menu.addMenu('Tool')
        self.tool_menu.setEnabled(False)
        # -Axon Tool
        self.axon_tool = self.add_menu_item(
            'Axon Tool', ToolMode.SEL_AXON.value, 'Select the axon itself',
            lambda: self.image_view.handle_key(ToolMode.SEL_AXON.value),
            self.tool_menu)
        # -Myelin Inner Tool
        self.myelin_inner_tool = self.add_menu_item(
            'Inner Myelin Tool', ToolMode.SEL_MYELIN_IN.value,
            'Select inner edge of the myelin sheaths',
            lambda: self.image_view.handle_key(ToolMode.SEL_MYELIN_IN.value),
            self.tool_menu)
        # -Myelin Outer Tool
        self.myelin_outer_tool = self.add_menu_item(
            'Outer Myelin Tool', ToolMode.SEL_MYELIN_OUT.value, 
            'Select outer edge of the myelin sheaths',
            lambda: self.image_view.handle_key(ToolMode.SEL_MYELIN_OUT.value), 
            self.tool_menu)
        # -Deselect Tool
        self.deselect_tool = self.add_menu_item(
            'Deselect Tool', ToolMode.DESELECT.value, 
            'Deselect any current selection',
            lambda: self.image_view.handle_key(ToolMode.DESELECT.value), 
            self.tool_menu)
        # -Info Tool
        self.info_tool = self.add_menu_item(
            'Info Tool', ToolMode.INFO.value, 
            'Check the status of a selection',
            lambda: self.image_view.handle_key(ToolMode.INFO.value), 
            self.tool_menu)
        # -Misc. Select Tool
        self.misc_tool = self.add_menu_item(
            'Misc. Select Tool', ToolMode.SEL_MISC.value, 
            'Select any kind of feature',
            lambda: self.image_view.handle_key(ToolMode.SEL_MISC.value), 
            self.tool_menu)
        # --------
        self.tool_menu.addSeparator()
        # -Cut Tool
        self.cut_tool = self.add_menu_item(
            'Cut Tool', ToolMode.CUT.value, 
            'Click to draw and separate sheaths. Press shift for a straight \
            line.', lambda: self.image_view.handle_key(ToolMode.CUT.value), 
            self.tool_menu)
        # -Draw Tool
        self.draw_tool = self.add_menu_item(
            'Draw Tool', ToolMode.DRAW.value,
            'Click to draw and complete sheaths. Press shift for a straight \
            line.', lambda: self.image_view.handle_key(ToolMode.DRAW.value), 
            self.tool_menu)
        # -Erase Tool
        self.erase_tool = self.add_menu_item(
            'Erase Tool', ToolMode.ERASE.value, 'Remove lines and points',
            lambda: self.image_view.handle_key(ToolMode.ERASE.value),
            self.tool_menu)
        # --------
        self.tool_menu.addSeparator()
        # -Unmyelinated Counting Tool
        self.unmyel_counting_tool = self.add_menu_item(
            'Unmyelinated Axon Counting Tool', ToolMode.COUNT_UNMYEL.value,
            'Count unmyelinated axons',
            lambda: self.image_view.handle_key(ToolMode.COUNT_UNMYEL.value), 
            self.tool_menu)
        # -Myelinated Counting Tool
        self.myel_counting_tool = self.add_menu_item(
            'Myelinated Axon Counting Tool', ToolMode.COUNT_MYEL.value,
            'Count myelinated axons',
            lambda: self.image_view.handle_key(ToolMode.COUNT_MYEL.value),
            self.tool_menu)
        # --------
        self.tool_menu.addSeparator()
        # -Threshold
        self.threshold_sub_menu = QMenu('Threshold', self)
        self.tool_menu.addMenu(self.threshold_sub_menu)
        # --Increment Threshold
        self.inc_thresh_menu_item = self.add_menu_item(
            'Increment Threshold', Qt.Key_Right, 'Increase boundary threshold',
            self.image_view.threshold_slider.increment, self.threshold_sub_menu)
        # --Decrement Threshold
        self.dec_thresh_menu_item = self.add_menu_item(
            'Decrement Threshold', Qt.Key_Left, 'Decrease boundary threshold',
            self.image_view.threshold_slider.decrement, self.threshold_sub_menu)
        # -Smoothing
        self.smoothing_sub_menu = QMenu('Smoothing', self)
        self.tool_menu.addMenu(self.smoothing_sub_menu)
        self.smoothing_action_group = QActionGroup(self)
        # --No Smoothing
        self.smoothing_none_menu_item = self.add_menu_item(
            'No Smoothing', None, 'Turn smoothing off', 
            lambda: self.image_view.set_blur(0), self.smoothing_sub_menu, 
            checkable=True)
        self.smoothing_action_group.addAction(self.smoothing_none_menu_item)
        # --Low Smoothing
        self.smoothing_low_menu_item = self.add_menu_item(
            'Low Smoothing', None, 'Set smoothing to low',
            lambda: self.image_view.set_blur(2), self.smoothing_sub_menu,
            checkable=True)
        self.smoothing_action_group.addAction(self.smoothing_low_menu_item)
        # --Medium Smoothing
        self.smoothing_med_menu_item = self.add_menu_item(
            'Medium Smoothing', None, 'Set smoothing to medium',
            lambda: self.image_view.set_blur(6), self.smoothing_sub_menu,
            checkable=True)
        self.smoothing_action_group.addAction(self.smoothing_med_menu_item)
        # --High Smoothing
        self.smoothing_high_menu_item = self.add_menu_item(
            'High Smoothing', None, 'Set smoothing to high',
            lambda: self.image_view.set_blur(9), self.smoothing_sub_menu,
            checkable=True)
        self.smoothing_action_group.addAction(self.smoothing_high_menu_item)

        # View Menu
        self.view_menu = self.main_menu.addMenu('View')
        self.view_menu.setEnabled(False)
        # -Zoom
        self.zoom_sub_menu = QMenu('Zoom', self)
        self.view_menu.addMenu(self.zoom_sub_menu)
        # --Reset Zoom
        self.zoom_100_sub_menu_item = self.add_menu_item(
            'Zoom to Fit', '0', 'Set the size of the image to the frame', 
            self.image_view.refit, self.zoom_sub_menu)
        # --Zoom in
        self.zoom_in_sub_menu_item = self.add_menu_item(
            'Zoom in', '=', 'Zoom in on the image', self.image_view.zoomIn, 
            self.zoom_sub_menu)
        # --Zoom out
        self.zoom_out_sub_menu_item = self.add_menu_item(
            'Zoom out', '-', 'Zoom out of the image', self.image_view.zoomOut, 
            self.zoom_sub_menu)
        # --Enable Scroll Wheel Zoom
        self.scroll_enabled_sub_menu_item = self.add_menu_item(
            'Scroll to Zoom', None, 'Enable or disable zoom by scrolling',
            self.image_view.viewer.setScrollZoomEnabled, self.zoom_sub_menu, 
            checkable=True)
        self.scroll_enabled_sub_menu_item.setChecked(True)
        # ---------
        self.view_menu.addSeparator()
        # -Visibility
        # -Toggle Outlines
        self.outline_toggle_menu_item = self.add_menu_item(
            'Show Outlines', 'O', 'Toggle outline visibility',
            self.image_view.toggle_outlines, self.view_menu, checkable=True)
        # -Toggle Highlights
        self.highlight_toggle_menu_item = self.add_menu_item(
            'Show Highlights', 'H', 'Toggle highlight visibility',
            self.image_view.toggle_highlights, self.view_menu, checkable=True)
        # -Toggle Numbers
        self.number_toggle_menu_item = self.add_menu_item(
            'Show Numbers', 'N', 'Toggle number label visibility',
            self.image_view.toggle_counters, self.view_menu, checkable=True)
        # -Toggle Lines
        self.line_toggle_menu_item = self.add_menu_item(
            'Show Lines', 'L', 'Toggle line visibility',
            self.image_view.toggle_lines, self.view_menu, checkable=True)
        # -Toggle Threshold Overlay
        self.threshold_toggle_menu_item = self.add_menu_item(
            'Show Threshold Overlay', 'Y', 'Toggle Threshold Overlay',
            self.image_view.toggle_threshold_overlay, self.view_menu, 
            checkable=True)
        self.threshold_toggle_menu_item.setChecked(False)

        self.setStatusBar(QStatusBar(self))
        self.show()

        self.directory = os.getcwd() # for autosaves

        # Setup the autosave timer
        self.timer = QTimer(self)
        self.timer.setInterval(5 * 60 * 1000) # convert 5 mins to milliseconds
        self.timer.timeout.connect(self.autosave)
        self.timer.start()


    def add_menu_item(
            self, action, shortcut, status_tip, callback, parent, 
            enabled=True, checkable=False):
        """
        Adds a menu item to the given menu.

        Arguments:
            action (str): the action to perform
            shortcut (str): the shortcut key for this action
            status_tip (str): the status tip to display when hovering
            callback (function): the function to run when the item is clicked
            parent (QAction): the menu to add this item to
            enabled (bool): should the menu item be enabled?
            checkable (bool): should this menu item be checkable

        Returns:
            new_menu_item (QAction): the item added to the menu
        """
        new_menu_item = QAction(action, self)
        if shortcut: new_menu_item.setShortcut(shortcut)
        if status_tip: new_menu_item.setStatusTip(status_tip)
        if callback: new_menu_item.triggered.connect(callback)
        new_menu_item.setCheckable(checkable)
        parent.addAction(new_menu_item)
        new_menu_item.setEnabled(enabled)
        return new_menu_item

    def new(self):
        """Loads in an image file for editing"""
        self.filename, _extensions = QFileDialog.getOpenFileName(
            win, 'Open new image', filter=image_file_extensions)
        if not self.filename:
            return
        self.save_filename = None
        
        open_dialog = OpenDialog(self)
        if open_dialog.exec_():
            try:
                self.image_view.new(self.filename,
                                    open_dialog.get_quality().value)
            except Exception as e:
                message = "<font color='red'><b>Failed to open image.</b> \
                           </font> Please check that you selected the correct \
                           file and try again."
                self.displayMessage(message, 'Failed to open')
                print(e)
                return
            self.enable_menu(self.filename)

    def enable_menu(self, filename):
        """Rename window and enable menus for editing"""
        self.setWindowTitle('MyelTracer - ' + filename)

        self.new_menu_item.setEnabled(True)
        self.save_menu_item.setEnabled(True)
        self.save_as_menu_item.setEnabled(True)
        self.export_menu_item.setEnabled(True)
        self.edit_menu.setEnabled(True)
        self.tool_menu.setEnabled(True)
        self.view_menu.setEnabled(True)

        self.undo_menu_item.setEnabled(False)
        self.redo_menu_item.setEnabled(False)

        self.outline_toggle_menu_item.setChecked(True)
        self.highlight_toggle_menu_item.setChecked(True)
        self.number_toggle_menu_item.setChecked(True)
        self.line_toggle_menu_item.setChecked(True)
        self.threshold_toggle_menu_item.setChecked(False)

        self.smoothing_none_menu_item.setChecked(False)
        self.smoothing_low_menu_item.setChecked(False)
        self.smoothing_med_menu_item.setChecked(False)
        self.smoothing_high_menu_item.setChecked(True)

    def export(self):
        """Prompt user with export options and export files"""
        def push_button(button_num, _checkboxes):
            """
            Checks/unchecks entire row/column/all checkboxes

            Arguments:
                button_num (int): the id of the button pressed
                _checkboxes (list): the checkboxes
            """
            if button_num < 3: # column
                boxes = _checkboxes[button_num:button_num+7:3]
            elif button_num < 7: # row
                boxes = _checkboxes[(button_num-3)*3:(button_num-3)*3+3]
            else: # all boxes
                boxes = _checkboxes
            if any([not box.isChecked() for box in boxes]):
                for box in boxes:
                    box.setChecked(True)
            else:
                for box in boxes:
                    box.setChecked(False)

        def toggle_menu(show_, menu, window):
            """
            Shows/hides the given menu

            Arguments:
                show_ (bool): should the menu be shown?
                menu (QWidget): menu to toggle visibility
                window (QDialog): dialog window to resize
            """
            if show_:
                menu.show()
                window.adjustSize()
            else:
                menu.hide()
                window.adjustSize()

        # Setup dialog window with one button for export
        export_dialog = QDialog(self)
        QBtn = QDialogButtonBox.Ok
        export_dialog_btn = QDialogButtonBox(QBtn)
        export_dialog_btn.button(QBtn).setText('Export')
        export_dialog.setWindowTitle('Export Settings')
        export_dialog_btn.accepted.connect(export_dialog.accept)

        # add the framework for the advanced settings
        advanced_settings_layout = QVBoxLayout()
        export_label = QLabel('Select which features you want to export')
        advanced_settings_layout.addWidget(export_label)

        # the checkboxes for what to export
        checkbox_layout = QGridLayout()
        checkboxes = [QCheckBox() for _ in range(12)]
        for c in checkboxes:
            c.setChecked(False)
        for i in (2, 5, 8): # the defaults, only diameters
            checkboxes[i].setChecked(True)

        # buttons for rows/columns/all
        buttons = [
            QPushButton('Perimeter'),
            QPushButton('Area'),
            QPushButton('Diameter'),
            QPushButton('Axon'),
            QPushButton('Inner Myelin'),
            QPushButton('Outer Myelin'),
            QPushButton('Miscellaneous'),
            QPushButton('All/None')
        ]
        for b in range(len(buttons)):
            buttons[b].pressed.connect(
                lambda btn=b: push_button(btn, checkboxes))

        # and add to the grid layout
        checkbox_layout.addWidget(buttons[0], 0, 1)
        checkbox_layout.addWidget(buttons[1], 0, 2)
        checkbox_layout.addWidget(buttons[2], 0, 3)
        checkbox_layout.addWidget(buttons[3], 1, 0)
        checkbox_layout.addWidget(buttons[4], 2, 0)
        checkbox_layout.addWidget(buttons[5], 3, 0)
        checkbox_layout.addWidget(buttons[6], 4, 0)
        checkbox_layout.addWidget(buttons[7], 0, 0)
        for c in range(12):
            checkbox_layout.addWidget(checkboxes[c], (c//3)+1, (c%3)+1)
        advanced_settings_layout.addLayout(checkbox_layout)

        # add extra options for g-ratio and counters
        gratio_checkbox = QCheckBox('Calculate g-ratio')
        gratio_checkbox.setChecked(True)
        advanced_settings_layout.addWidget(gratio_checkbox)
        counters_checkbox = QCheckBox('Include counters')
        counters_checkbox.setChecked(True)
        advanced_settings_layout.addWidget(counters_checkbox)

        # add this to the export window
        export_layout = QVBoxLayout()
        advanced_settings_frame_layout = QVBoxLayout()
        advanced_settings_frame = QFrame()
        advanced_settings_frame.setLayout(advanced_settings_layout)
        advanced_settings_frame_layout.addWidget(advanced_settings_frame)
        advanced_settings_frame.hide()
        advanced_settings_box = QGroupBox('Advanced Options')
        advanced_settings_box.setCheckable(True)
        advanced_settings_box.setChecked(False)
        advanced_settings_box.toggled.connect(
            lambda on: toggle_menu(on, advanced_settings_frame, export_dialog))
        advanced_settings_box.setLayout(advanced_settings_frame_layout)
        export_layout.addWidget(advanced_settings_box)
        export_layout.addWidget(export_dialog_btn)

        export_dialog.setLayout(export_layout)
        if not export_dialog.exec_(): # check if user pressed the 'x'
            return

        # Convert checkboxes to dict to pass to exporter
        export_selections = {
            'Axon Perimeter': checkboxes[0].isChecked(),
            'Axon Area': checkboxes[1].isChecked(),
            'Axon Diameter': checkboxes[2].isChecked(),
            'Inner Myelin Perimeter': checkboxes[3].isChecked(),
            'Inner Myelin Area': checkboxes[4].isChecked(),
            'Inner Myelin Diameter': checkboxes[5].isChecked(),
            'Outer Myelin Perimeter': checkboxes[6].isChecked(),
            'Outer Myelin Area': checkboxes[7].isChecked(),
            'Outer Myelin Diameter': checkboxes[8].isChecked(),
            'Misc. Perimeter': checkboxes[9].isChecked(),
            'Misc. Area': checkboxes[10].isChecked(),
            'Misc. Diameter': checkboxes[11].isChecked(),
            'g-ratio': gratio_checkbox.isChecked(),
            'Counters': counters_checkbox.isChecked()
        }

        self.export_directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Export to")
        if self.export_directory:
            try:
                self.image_view.export(
                    self.export_directory, export_selections)
                message = "Export Complete"
            except PermissionError as e:
                message = "<font color='red'><b>Export failed.</b></font> \
                            Please close the data files or check permissions \
                            before trying again.<br><br>{}".format(e)
            
            self.displayMessage(message, 'Export Status')
        
    def save_as(self):
        """Saves current session to new file"""
        save_filename, _extensions = QFileDialog.getSaveFileName(
            self, 'Save Data as...',
            self.directory + '/'+ self.image_view.get_filename() + '-data.txt',
            'Data file (*.txt)')
        if save_filename:
            try:
                self.image_view.save(save_filename)
                message = "Save Complete"
                self.save_filename = save_filename
            except PermissionError as e:
                message = "<font color='red'><b>Save failed.</b></font> \
                           Please close the data file or check permissions \
                           before trying again.<br><br>{}".format(e)
            
            self.displayMessage(message, 'Save Status')

    def save(self):
        """Overwrites current save file if exists, otherwise uses save_as"""
        if self.save_filename:
            if path.exists(self.save_filename):               
                try:
                    self.image_view.save(self.save_filename)
                    message = "Save Complete"
                except PermissionError as e:
                    message = "<font color='red'><b>Save failed.</b></font> \
                               Please close the data file or check \
                               permissions before trying again. \
                               <br><br>{}".format(e)
                self.displayMessage(message, 'Save Status')
            else:
                self.save_as()
        else:
            self.save_as()

    @pyqtSlot()
    def autosave(self):
        """Automatically saves file as a backup in root directory"""
        autosave_path = self.directory + '/backups'
        if not os.path.isdir(autosave_path):
            os.mkdir(autosave_path)
        if self.image_view.get_filename():
            autosave_filename = (autosave_path 
                                 + '/' + self.image_view.get_filename() 
                                 + '-data-backup.txt')
            try:
                self.image_view.save(autosave_filename)
                print('saved successfully as',autosave_filename)
            except PermissionError as e:
                print('failed to autosave to {}'.format(autosave_filename))
                pass


    def open(self):

        self.filename, _extensions = QFileDialog.getOpenFileName(
            win, 'Open data file', filter='Data file (*.txt)')
        if not self.filename:
            return
        
        feedback = self.image_view.open(self.filename)
        if feedback:
            if feedback == 'incompatible version':
                message = "<font color='red'><b>Failed to open file.</b>\
                           </font> The data file you attempted to import is \
                           incompatible with this version of the software."
            elif feedback == 'no image':
                message = "<font color='red'><b>Image not found.</b></font>\
                           The data file you imported is valid, but the image \
                           used cannot be found on your computer. To resolve, \
                           first use 'New' to open the image, then use 'Open' \
                           to import this file and try again."
            else:
                if feedback != 'success':
                    self.enable_menu(feedback)
                message = "File successfully opened."
                self.save_filename = self.filename
                return
        else:
            message = "<font color='red'><b>Failed to open file.</b></font> \
                       Please check that you are opening the correct file."
            
        self.displayMessage(message, 'Import Status')

    def displayMessage(self, message, title):
        """
        Displays a popup

        Arguments:
            message (str): the message to be displayed
            title (str): the popup window name
        """
        message_dialog = QDialog(self)
        QBtn = QDialogButtonBox.Ok
        message_dialog_btn = QDialogButtonBox(QBtn)
        message_dialog.setWindowTitle(title)
        message_dialog_btn.accepted.connect(message_dialog.accept)

        message_layout = QVBoxLayout()
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_layout.addWidget(message_label)
        message_layout.addWidget(message_dialog_btn)
        message_dialog.setLayout(message_layout)
        message_dialog.exec_()

    def set_undo_enabled(self, enable):
        """Enables/disables the undo menu button"""
        self.undo_menu_item.setEnabled(enable)

    def set_redo_enabled(self, enable):
        """Enables/disables the redo menu button"""
        self.redo_menu_item.setEnabled(enable)

    # PyQt5 callbacks
    def resizeEvent(self, event):
        """Refit the canvas when the window is resized"""
        self.image_view.refit()

    def keyPressEvent(self, event):
        """Pass keypresses to the canvas"""
        self.image_view.handle_key(event.key())

class PhotoViewer(QGraphicsView):
    """
    This is a modified version of what's found here:
    https://stackoverflow.com/questions/35508711/how-to-enable-pan-and-zoom-in-a-qgraphicsview
    Basically this allows the OpenCV editor become pannable and zoomable
    """
    photoClicked = pyqtSignal(QPoint)
    photoReleased = pyqtSignal(QPoint)
    photoHovered = pyqtSignal(QPoint)
    keyPressed = pyqtSignal(int)
    keyReleased = pyqtSignal(int)

    def __init__(self, parent):
        """
        Arguments:
            parent (object): the parent of the PhotoViewer
        """
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)
        self._last_pos = None
        self._pan_enabled = False
        self._scroll_zoom_enabled = True

    def hasPhoto(self):
        """Check if photo exists"""
        return not self._empty

    def fitInView(self):
        """Resizes photo to fit the view"""
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    def setPhoto(self, pixmap=None, new_image=True):
        """
        Loads the photo into the view

        Arguments:
            pixmap (QPixmap): the photo to display
            new_image (bool): is this the first time this image is shown?
        """
        if new_image:
            self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self._photo.setPixmap(QPixmap())
        if new_image:
            self.fitInView()

    def zoomIn(self):
        """Zoom in on the image"""
        self._factor = 1.25
        self._zoom += 1
        self.applyZoom()

    def zoomOut(self):
        """Zoom out on the image"""
        self._factor = 0.8
        self._zoom -= 1
        self.applyZoom()

    def applyZoom(self):
        """Apply the current zoom value, or reset the view"""
        if self._zoom > 0:
            self.scale(self._factor, self._factor)
        elif self._zoom == 0:
            self.fitInView()
        else:
            self._zoom = 0

    def wheelEvent(self, event):
        """Handle mouse scroll events by zooming"""
        if self.hasPhoto() and self._scroll_zoom_enabled:
            if event.angleDelta().y() > 0:
                self.zoomIn()
            else:
                self.zoomOut()

    def setScrollZoomEnabled(self, enabled):
        """Turns on/off the ablility to zoom by scrolling"""
        self._scroll_zoom_enabled = enabled

    def mousePressEvent(self, event):
        """Handles mouse press events for panning"""
        if event.button() == Qt.LeftButton:
            if not self._pan_enabled:
                if self._photo.isUnderMouse():
                    self.photoClicked.emit(
                        self.mapToScene(event.pos()).toPoint())
        if event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            left_click = QMouseEvent(QEvent.MouseButtonPress, event.pos(), 
                                     Qt.LeftButton, Qt.LeftButton,
                                     Qt.NoModifier)
            self.mousePressEvent(left_click)
        super(PhotoViewer, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handles mouse release events to stop panning"""
        if event.button() == Qt.LeftButton and not self._pan_enabled:
            self.photoReleased.emit(self.mapToScene(event.pos()).toPoint())
        if not self._pan_enabled:
            self.setDragMode(QGraphicsView.NoDrag)
        super(PhotoViewer, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Pans the image when dragged"""
        if self._photo.isUnderMouse():
            self.photoHovered.emit(self.mapToScene(event.pos()).toPoint())
        self._last_pos = event.pos()
        super(PhotoViewer, self).mouseMoveEvent(event)

    def keyPressEvent(self, event):
        """Handles space bar presses to enable panning"""
        if event.isAutoRepeat(): # only accept the first press
            return
        if event.key() == Qt.Key_Space and not self._pan_enabled:
            self._pan_enabled = True
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.keyPressed.emit(event.key())

    def keyReleaseEvent(self, event):
        """Handles space bar releases to disable panning"""
        if event.isAutoRepeat():
            return
        if event.key() == Qt.Key_Space and self._pan_enabled:
            self._pan_enabled = False
            self.setDragMode(QGraphicsView.NoDrag)
        self.keyReleased.emit(event.key())

class OpenDialog(QDialog):
    """This is the window that contains the quality settings for a new image"""
    def __init__(self, parent=None):
        """
        Arguments:
            parent (object): the parent of the OpenDialog
        """
        super(OpenDialog, self).__init__(parent)
        
        self.setWindowTitle("Import settings")
        self.quality = Quality.MEDIUM
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        
        self.button_box = QDialogButtonBox(QBtn)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


        radio_button_layout = QVBoxLayout()
        self.radio_label = QLabel('Select image import quality\nNote: Higher \
                                   quality may mean slower performance')
        radio_button_layout.addWidget(self.radio_label)
        # Original Quality
        self.radio_original = QRadioButton('Original:\t100%')
        self.radio_original.toggled.connect(
            lambda: self.set_quality(Quality.ORIGINAL))
        radio_button_layout.addWidget(self.radio_original)
        # Very High Quality
        self.radio_very_high = QRadioButton('Very High:\t90%')
        self.radio_very_high.toggled.connect(
            lambda: self.set_quality(Quality.VERY_HIGH))
        radio_button_layout.addWidget(self.radio_very_high)
        # High Quality
        self.radio_high = QRadioButton('High:\t80%')
        self.radio_high.toggled.connect(lambda: self.set_quality(Quality.HIGH))
        radio_button_layout.addWidget(self.radio_high)
        # Medium Quality
        self.radio_medium = QRadioButton('Medium:\t70%')
        self.radio_medium.setChecked(True)
        self.radio_medium.toggled.connect(
            lambda: self.set_quality(Quality.MEDIUM))
        radio_button_layout.addWidget(self.radio_medium)
        # Low Quality
        self.radio_low = QRadioButton('Low:\t\t60%')
        self.radio_low.toggled.connect(lambda: self.set_quality(Quality.LOW))
        radio_button_layout.addWidget(self.radio_low)
        # Very Low Quality
        self.radio_very_low = QRadioButton('Very Low:\t50%')
        self.radio_very_low.toggled.connect(
            lambda: self.set_quality(Quality.VERY_LOW))
        radio_button_layout.addWidget(self.radio_very_low)


        self.layout = QVBoxLayout()
        self.layout.addLayout(radio_button_layout)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def set_quality(self, quality):
        """Updates the quality selection"""
        self.quality = quality

    def get_quality(self):
        """Returns the current quality selection"""
        return self.quality

class HButtonSlider(QWidget):
    """This packages a slider with buttons and a value preview text box"""
    valueChanged = pyqtSignal(int)

    def __init__(self, parent, title, min_val, max_val, default_val):
        """
        Arguments:
            parent (object): the parent of the HButtonSlider
            title (string): the name to appear beside the slider
            min_val (int): the lower bound on the slider
            max_val (int): the upper bound on the slider
            default_val (int): the starting value on the slider
        """
        super(HButtonSlider, self).__init__()
        self.default_val = int(default_val)
        self.layout = QHBoxLayout(self)

        self.title_label = QLabel(title)

        self.left_button = QToolButton(self)
        self.left_button.setText('<')
        self.left_button.pressed.connect(self.decrement)
        self.left_button.setAutoRepeat(True)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.valueChanged.emit)
        self.slider.setMinimum(int(min_val))
        self.slider.setMaximum(int(max_val))
        self.slider.setValue(int(default_val))
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.slider.setSizePolicy(size_policy)

        self.right_button = QToolButton(self)
        self.right_button.setText('>')
        self.right_button.pressed.connect(self.increment)
        self.right_button.setAutoRepeat(True)

        self.value_label = QLineEdit(self)
        self.value_label.setText('{}'.format(self.slider.value()))
        self.slider.valueChanged.connect(self.set_text)
        self.value_label.setReadOnly(True)
        size_policy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.value_label.setSizePolicy(size_policy)

        self.reset_button = QToolButton(self)
        self.reset_button.setText('Reset')
        self.reset_button.pressed.connect(self.reset)
        self.reset_button.setAutoRepeat(False)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.left_button)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.right_button)
        self.layout.addWidget(self.value_label)
        self.layout.addWidget(self.reset_button)

    def value(self):
        """Returns the current value of the slider"""
        return self.slider.value()

    def setValue(self, value):
        """
        Updates the current value of the slider

        Arguments:
            value (int): the desired value
        """
        self.slider.setValue(int(value))

    def decrement(self):
        """Decreases the current value by 1"""
        self.slider.setValue(self.slider.value()-1)
        self.set_text()

    def increment(self):
        """Increases the current value by 1"""
        self.slider.setValue(self.slider.value()+1)
        self.set_text()

    def reset(self):
        """Restores the slider to the default value"""
        self.slider.setValue(self.default_val)
        self.set_text()

    def constrain_max(self, value):
        """Constrains the upper bound of the slider to value"""
        if self.slider.value() >= value:
            self.slider.setValue(value-1)

    def constrain_min(self, value):
        """Constrains the lower bound of the slider to value"""
        if self.slider.value() <= value:
            self.slider.setValue(value+1)

    def set_text(self):
        """Updates the text to match the current value"""
        self.value_label.setText('{}'.format(self.slider.value()))

class HButtonGroup(QWidget):
    """The toolbox button class"""
    buttonPressed = pyqtSignal(str)

    def __init__(self, parent, names, values, status_tips, tool_tips, 
                 use_icons = False, line_split = None):
        """
        Arguments:
            parent (obj): the parent object
            names (str): the text to display on the button or the path to
                         a button icon
            values (ToolMode): the corresponding tool mode and keyboard value
            status_tips (str): status tip to display on hover
            tool_tips (str): tool tip to to display on hover
            use_icons (bool): does names correspond to a filepath?
            line_split (int): number of buttons per line
        """
        super(HButtonGroup, self).__init__()
        self.buttons = []
        self.layout = QGridLayout(self)

        if line_split == None: # all buttons on one line
            line_split = len(names)

        for i in range(len(names)):
            if use_icons:
                btn = QToolButton(self)
                btn.setIcon(QIcon(QPixmap(names[i])))
            else:
                btn = QToolButton(names[i])
            btn.setCheckable(True)
            btn.setIconSize(QSize(40, 40))
            btn.clicked.connect(lambda checked, 
                                value=values[i].value: self.press_btn(value))
            btn.setStatusTip(status_tips[i])
            btn.setToolTip(tool_tips[i])
            self.buttons.append((btn, values[i]))
            self.layout.addWidget(btn, i//line_split, i%line_split)

    def press_btn(self, value):
        """
        Converts keypress into button press
        
        Arguments:
            value (int, str): the key being pressed
        """
        # First, convert to a character value
        if isinstance(value, int):
            if value < 256:
                value = chr(value)
            else:
                return

        # Next, check if any buttons correspond to this value and toggle on
        valid_key = False
        for i in self.buttons:
            if i[1].value == value:
                i[0].setChecked(True)
                valid_key = True
        
        # Finally, turn off all other buttons and trigger event
        if valid_key:
            for i in self.buttons:
                if i[1].value != value:
                    i[0].setChecked(False)
            self.buttonPressed.emit(value)

    def get_val(self, value):
        """
        Gets the corresponding ToolMode value for button's value

        Arguments:
            value (int, str): the button value to search for
        """
        for i in self.buttons:
            if i[1].value == value:
                return i[1]
        return None

    def reset(self):
        """Unchecks all buttons"""
        for i in self.buttons:
            i[0].setChecked(False)

class DisplayImageWidget(QWidget):
    """This is the main GUI interface."""
    def __init__(self, parent=None):
        """
        Arguments:
            parent (obj): the parent object 
        """
        super(DisplayImageWidget, self).__init__(parent)

        self.parent = parent

        self.viewer = PhotoViewer(self)
        self.editor = None
        
        # Defaults
        self.threshold = 122
        self.blur_value = 9
        self.cut_size = 1
        self.draw_size = 2

        # Toolbar
        self.toolbar_layout = QVBoxLayout()
        self.toolbar_layout.setAlignment(Qt.AlignTop)

        # Threshold Slider
        self.threshold_slider = HButtonSlider(self, 'Threshold', 0, 255, 
                                              self.threshold)
        self.threshold_slider.valueChanged.connect(self.set_threshold)
        self.threshold_slider.layout.setAlignment(Qt.AlignTop)
        self.threshold_slider.setStatusTip('Adjust the difference between the \
                                            dark myelin sheath and light axon')
        self.toolbar_layout.addWidget(self.threshold_slider)

        # Calibration
        self.calibration_layout = QHBoxLayout()
        self.calibration_label = QLabel('Calibration:')
        self.calibration_input = QLineEdit('0.003951')
        self.calibration_input.setValidator(QDoubleValidator(0.00,99.99,8))
        self.calibration_input.textChanged.connect(self.set_calibration)
        self.calibration_units = QLabel('um/px')
        self.calibration_layout.addWidget(self.calibration_label)
        self.calibration_layout.addWidget(self.calibration_input)
        self.calibration_layout.addWidget(self.calibration_units)
        self.toolbar_layout.addLayout(self.calibration_layout)

        # Toolbox Buttons
        status_tips = ['Select the axon. Click and drag to manually select.',
                       'Select the inner edge of the myelin sheaths. Click and \
                        drag to manually select.',
                       'Select the outer edge of the myelin sheaths. Click and \
                        drag to manually select.',
                       'Deselect any current selections',
                       'Get information about a selection',
                       'Select any feature.',
                       'Click to draw and separate sheaths. Press shift for a \
                        straight line.',
                       'Click to draw and connect sheaths. Press shift for a \
                        straight line.',
                       'Erase unwanted lines or points',
                       'Click to add an unmyelinated counter',
                       'Click to add a myelinated counter']
        tool_tips = ['Axon Select Tool - <b>1</b><br>Click and drag for manual \
                      selection',
                     'Inner Myelin Select Tool - <b>2</b><br>Click and drag \
                      for manual selection',
                     'Outer Myelin Select Tool - <b>3</b><br>Click and drag \
                      for manual selection',
                     'Deselect Tool - <b>4</b>',
                     'Info Tool - <b>5</b>',
                     'Misc. Select Tool - <b>6</b>',
                     'Cut Tool - <b>Q</b><br>Connect bright areas<br>Shift-\
                      click for straight lines',
                     'Draw Tool - <b>W</b><br>Connect dark areas<br>Shift-\
                      click for straight lines',
                     'Erase Tool - <b>E</b>',
                     'Unmyelinated Axon Counting Tool - <b>R</b>',
                     'Myelinated Axon Counting Tool - <b>T</b>']
        tool_names = [appctxt.get_resource('Icons/AxonTool.png'),
                      appctxt.get_resource('Icons/InnerTool.png'),
                      appctxt.get_resource('Icons/OuterTool.png'),
                      appctxt.get_resource('Icons/DeselectTool.png'),
                      appctxt.get_resource('Icons/InfoTool.png'),
                      appctxt.get_resource('Icons/MiscTool.png'),
                      appctxt.get_resource('Icons/CutTool.png'),
                      appctxt.get_resource('Icons/DrawTool.png'),
                      appctxt.get_resource('Icons/EraseTool.png'),
                      appctxt.get_resource(
                        'Icons/UnmyelinatedCountingTool.png'),
                      appctxt.get_resource('Icons/MyelinatedCountingTool.png')]
        tool_modes = [ToolMode.SEL_AXON,
                      ToolMode.SEL_MYELIN_IN,
                      ToolMode.SEL_MYELIN_OUT,
                      ToolMode.DESELECT,
                      ToolMode.INFO,
                      ToolMode.SEL_MISC,
                      ToolMode.CUT,
                      ToolMode.DRAW,
                      ToolMode.ERASE,
                      ToolMode.COUNT_UNMYEL,
                      ToolMode.COUNT_MYEL]
        self.tool_buttons = HButtonGroup(self, tool_names, tool_modes,
                                        status_tips, tool_tips, True, 6)
        self.tool_buttons.buttonPressed.connect(
            lambda x: self.set_mode(self.tool_buttons.get_val(x)))
        self.tool_buttons.layout.setAlignment(Qt.AlignTop)
        self.toolbar_layout.addWidget(self.tool_buttons)

        # Other Buttons
        self.extra_button_layout = QHBoxLayout()
        self.size_button = QToolButton()
        self.size_button.setText('Change search size parameters')
        self.size_button.pressed.connect(self.show_size_sliders)
        self.extra_button_layout.addWidget(self.size_button)
        self.appearance_button = QToolButton()
        self.appearance_button.setText('Edit overlay appearance')
        self.appearance_button.pressed.connect(self.show_appearance_sliders)
        self.extra_button_layout.addWidget(self.appearance_button)
        self.extra_button_layout.addStretch()
        self.toolbar_layout.addLayout(self.extra_button_layout)

        # Min Size and Max Size Sliders
        self.min_max_slider_layout = QVBoxLayout()
        self.min_slider = HButtonSlider(self, 'Min Size', 0, 800, 1000**0.5)
        self.max_slider = HButtonSlider(self, 'Max Size', 0, 800, 50000**0.5)
        self.min_slider.valueChanged.connect(
            lambda: self.constrain_min_slider(self.min_slider, self.max_slider))
        self.min_slider.layout.setAlignment(Qt.AlignTop)
        self.min_slider.setStatusTip('Set the minimum size of the axon you \
                                      want to see')
        self.min_max_slider_layout.addWidget(self.min_slider)
        self.max_slider.valueChanged.connect(
            lambda: self.constrain_max_slider(self.min_slider, self.max_slider))
        self.max_slider.layout.setAlignment(Qt.AlignTop)
        self.max_slider.setStatusTip('Set the maximum size of the axon you \
                                      want to see')
        self.min_max_slider_layout.addWidget(self.max_slider)
        self.min_max_frame = QFrame()
        self.min_max_frame.setLayout(self.min_max_slider_layout)
        self.toolbar_layout.addWidget(self.min_max_frame)
        self.min_max_frame.hide()

        # Appearance Sliders
        self.appearance_slider_layout = QVBoxLayout()
        # -Alpha Slider
        self.alpha_slider = HButtonSlider(self, 'Transparency', 0, 10, 4)
        self.alpha_slider.slider.setTickPosition(QSlider.TicksBothSides)
        self.alpha_slider.slider.setTickInterval(1)
        self.alpha_slider.valueChanged.connect(self.set_alpha)
        self.alpha_slider.layout.setAlignment(Qt.AlignTop)
        self.alpha_slider.setStatusTip('Adjust the transparency of the overlay')
        self.appearance_slider_layout.addWidget(self.alpha_slider)
        # -Outline Thickness Slider
        self.outline_thickness_slider = HButtonSlider(self, 'Outline Thickness',
                                                      1, 2, 1)
        self.outline_thickness_slider.slider.setTickPosition(
            QSlider.TicksBothSides)
        self.outline_thickness_slider.slider.setTickInterval(1)
        self.outline_thickness_slider.valueChanged.connect(
            self.set_outline_thickness)
        self.outline_thickness_slider.layout.setAlignment(Qt.AlignTop)
        self.outline_thickness_slider.setStatusTip('Adjust the thickness of \
                                                    outlines')
        self.appearance_slider_layout.addWidget(self.outline_thickness_slider)
        # -Font Size Slider
        self.font_size_slider = HButtonSlider(self, 'Font Size',
                                                      1, 20, 2)
        self.font_size_slider.slider.setTickPosition(
            QSlider.TicksBothSides)
        self.font_size_slider.slider.setTickInterval(1)
        self.font_size_slider.valueChanged.connect(
            self.set_font_size)
        self.font_size_slider.layout.setAlignment(Qt.AlignTop)
        self.font_size_slider.setStatusTip('Adjust the size of the font')
        self.appearance_slider_layout.addWidget(self.font_size_slider)
        # -Frame for the sliders
        self.appearance_frame = QFrame()
        self.appearance_frame.setLayout(self.appearance_slider_layout)
        self.toolbar_layout.addWidget(self.appearance_frame)
        self.appearance_frame.hide()

        # Line Thickness Slider
        self.line_thickness_slider_layout = QVBoxLayout()
        self.line_thickness_slider = HButtonSlider(self, 'Line Thickness', 1, 
                                                   3, 2)
        self.line_thickness_slider.slider.setTickPosition(
            QSlider.TicksBothSides)
        self.line_thickness_slider.slider.setTickInterval(1)
        self.line_thickness_slider.valueChanged.connect(
            self.set_line_thickness)
        self.line_thickness_slider.layout.setAlignment(Qt.AlignTop)
        self.line_thickness_slider.setStatusTip('Adjust the thickness of cut \
                                                 and draw lines')
        self.line_thickness_slider_layout.addWidget(self.line_thickness_slider)
        self.line_thickness_frame = QFrame()
        self.line_thickness_frame.setLayout(self.line_thickness_slider_layout)
        self.toolbar_layout.addWidget(self.line_thickness_frame)
        self.line_thickness_frame.hide()

        # Eraser Size Slider
        self.eraser_size_slider_layout = QVBoxLayout()
        self.eraser_size_slider = HButtonSlider(self, 'Eraser Size', 1, 50, 20)
        self.eraser_size_slider.slider.setTickPosition(QSlider.TicksBothSides)
        self.eraser_size_slider.slider.setTickInterval(5)
        self.eraser_size_slider.valueChanged.connect(self.set_eraser_size)
        self.eraser_size_slider.layout.setAlignment(Qt.AlignTop)
        self.eraser_size_slider.setStatusTip('Adjust the size of the eraser')
        self.eraser_size_slider_layout.addWidget(self.eraser_size_slider)
        self.eraser_size_frame = QFrame()
        self.eraser_size_frame.setLayout(self.eraser_size_slider_layout)
        self.toolbar_layout.addWidget(self.eraser_size_frame)
        self.eraser_size_frame.hide()

        # Reset Button
        self.reset_button = QToolButton(self)
        self.reset_button.setText('Reset all parameters to default')
        self.reset_button.pressed.connect(self.reset)
        self.reset_button.setAutoRepeat(False)
        self.reset_button.setToolTip('Reset all parameters back to default')
        self.toolbar_layout.addWidget(self.reset_button, 
                                      alignment=Qt.AlignRight)

        self.toolbar_layout.addStretch()

        # Credits Section
        credits_text = '<p>Created by Feng Lab, code written by Harrison Allen</p>'
        credits_text += "<p><a href='https://github.com/HarrisonAllen/MyelTracer'>View source on GitHub</a></p>"
        # credits_text += "<p><a href='https://google.com'>View the paper</a></p>" # TODO: Replace with real link
        self.credits = QLabel(credits_text)
        self.credits.setOpenExternalLinks(True)
        self.credits.setAlignment(Qt.AlignRight|Qt.AlignBottom)
        self.toolbar_layout.addWidget(self.credits,
                                      alignment=(Qt.AlignRight|Qt.AlignBottom))

        self.viewer.photoClicked.connect(self.photoClicked)
        self.viewer.photoHovered.connect(self.photoHovered)
        self.viewer.photoReleased.connect(self.photoReleased)

        self.toolbarFrame = QFrame()
        self.toolbarFrame.setLayout(self.toolbar_layout)
        self.mainLayout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.viewer)
        self.splitter.addWidget(self.toolbarFrame)
        self.splitter.setSizes([700, 100])
        self.mainLayout.addWidget(self.splitter)

    def constrain_min_slider(self, min_slider, max_slider):
        """
        Constrains the max value on the min_slider to the max_slider's value

        Arguments:
            min_slider (HButtonSlider): the slider to constrain
            max_slider (HButtonSlider): the slider to use as constraint
        """
        min_slider.constrain_max(max_slider.value())
        self.set_min(self.min_slider.value()**2)

    def constrain_max_slider(self, min_slider, max_slider):
        """
        Constrains the min value on the max_slider to the min_slider's value

        Arguments:
            min_slider (HButtonSlider): the slider to use as constraint
            max_slider (HButtonSlider): the slider to constrain
        """
        max_slider.constrain_min(min_slider.value())
        self.set_max(self.max_slider.value()**2)

    def photoClicked(self, pos):
        """Pass photoClicked event to the editor"""
        if self.viewer.dragMode()  == QGraphicsView.NoDrag:
            if self.editor:
                self.editor.mouse_event(cv.EVENT_LBUTTONDOWN, pos.x(), pos.y(), 
                                        None, None,
                                        QApplication.keyboardModifiers())

    def photoHovered(self, pos):
        """Pass photoHovered event to the editor"""
        if self.viewer.dragMode() == QGraphicsView.NoDrag:
            if self.editor:
                self.editor.mouse_event(cv.EVENT_MOUSEMOVE, pos.x(), pos.y(),
                                        None, None, 
                                        QApplication.keyboardModifiers())

    def photoReleased(self, pos):
        """Pass photoReleased event to the editor"""
        if self.viewer.dragMode() == QGraphicsView.NoDrag:
            if self.editor:
                self.editor.mouse_event(cv.EVENT_LBUTTONUP, pos.x(), pos.y(), 
                                        None, None, 
                                        QApplication.keyboardModifiers())

    def new(self, filename, quality):
        """
        Load in an image from a filename

        Arguments:
            filename (str): the file to open
            quality (float): the desired image quality
        """
        config = {
            'threshold': self.threshold_slider.value(),
            'blur': self.blur_value,
            'min_size': self.min_slider.value()**2,
            'max_size': self.max_slider.value()**2,
            'alpha': self.alpha_slider.value() / 10,
            'calibration': float(self.calibration_input.text()),
            'quality': quality,
            'outline_thickness': int(self.outline_thickness_slider.value()),
            'font_size': self.font_size_slider.value(),
            'line_thickness': self.line_thickness_slider.value(),
            'eraser_size': self.eraser_size_slider.value(),
            'cur_group': 'Unmyelinated Axons'
        }
        self.quality = quality
        self.editor = Axon_Editor(filename, quality, config, self.show_image, 
                                  self.parent)
        self.editor.show()
        self.refit()
        self.tool_buttons.reset()

    def export(self, directory, export_selections):
        """
        Export the current session

        Arguments:
            directory (str): the directory to save to
            export_selections (dict): the output from the export menu
        """
        if self.editor:
            self.editor.export(directory, export_selections)

    def get_filename(self):
        """Returns the filename of the current image"""
        if self.editor:
            return self.editor.get_filename()

    def save(self, filename):
        """Saves the current session to 'filename' (str)"""
        if self.editor:
            base_info = {
                'threshold': self.threshold,
                'cut_size': self.cut_size,
                'draw_size': self.draw_size
            }
            self.editor.save(filename, base_info)

    def open(self, filename):
        """
        Opens a session from 'filename' (str)
        
        Returns:
            None if the file is improperly formatted
            'incompatible version' if the data file is from an incompatible
                version of the software (early beta builds)
            filename if an image is found on this computer
            'no image' if the image is not found on this computer, and one isn't
                already loaded in
            'success' if the file is loaded successfully, an image was already
                loaded in, and the image in the file was not found
        """
        file = None
        try:
            with open(filename, 'r') as f:
                import_data = eval(f.read())
        except:
            return None
        if (not 'version' in import_data or 
            not import_data['version'] in COMPATIBLE_VERSIONS):
            return 'incompatible version'
        if isinstance(import_data, dict):
            if 'threshold' in import_data:
                self.threshold_slider.setValue(import_data['threshold'])
            if 'blur' in import_data:
                self.set_blur(import_data['blur'])
            if 'min_size' in import_data:
                self.min_slider.setValue((import_data['min_size'])**0.5)
            if 'max_size' in import_data:
                self.max_slider.setValue((import_data['max_size'])**0.5)
            if 'alpha' in import_data:
                self.alpha_slider.setValue(import_data['alpha']*10)
            if 'calibration' in import_data:
                self.calibration_input.setText(str(import_data['calibration']))
            if 'outline_thickness' in import_data:
                self.outline_thickness_slider.setValue(
                    import_data['outline_thickness'])
            if 'font_size' in import_data:
                self.font_size_slider.setValue(import_data['font_size'])
            if 'line_thickness' in import_data:
                self.line_thickness_slider.setValue(
                    import_data['line_thickness'])
            if 'eraser_size' in import_data:
                self.eraser_size_slider.setValue(import_data['eraser_size'])
            if 'cut_size' in import_data:
                self.cut_size = import_data['cut_size']
            if 'draw_size' in import_data:
                self.draw_size = import_data['draw_size']
            if 'filename' in import_data and 'quality' in import_data:
                file = import_data['filename']
                quality = import_data['quality']
                if path.exists(file):
                    self.new(file, quality)
                else:
                    file = None
        if self.editor:
            self.editor.open(import_data)
        else:
            return 'no image'
        if file:
            return file
        return 'success'

    def refit(self):
        """Reset the zoom on the image to match the frame"""
        self.viewer.fitInView()

    def zoomIn(self):
        """Zoom in on the image"""
        self.viewer.zoomIn()

    def zoomOut(self):
        """Zoom out on the image"""
        self.viewer.zoomOut()

    @pyqtSlot()
    def show_image(self, image, new_image):
        """
        Display the given image

        Arguments:
            image (np.array): the opencv image to display
            new_image (bool): is this image entirely new?
        """
        # this is a fix for the slanted lines artifact
        height, width, _ = np.shape(image)
        total_bytes = image.data.nbytes
        bytes_per_line = int(total_bytes/height)

        self.image = QImage(image.data, width, height, bytes_per_line, 
                            QImage.Format_RGB888).rgbSwapped()
        self.viewer.setPhoto(QPixmap.fromImage(self.image), new_image)

    def toggle_outlines(self, value):
        """Set outlines visible/hidden"""
        if self.editor:
            self.editor.toggle_outlines(value)

    def toggle_highlights(self, value):
        """Set highlights visible/hidden"""
        if self.editor:
            self.editor.toggle_highlights(value)

    def toggle_counters(self, value):
        """Set numbers visible/hidden"""
        if self.editor:
            self.editor.toggle_counters(value)

    def toggle_lines(self, value):
        """Set lines visible/hidden"""
        if self.editor:
            self.editor.toggle_lines(value)

    def toggle_threshold_overlay(self, value):
        """Set threshold overlay visible/hidden"""
        if self.editor:
            self.editor.toggle_threshold_overlay(value)

    def undo(self):
        """Undo the last change"""
        if self.editor:
            self.editor.undo()

    def redo(self):
        """Redo the last undo"""
        if self.editor:
            self.editor.redo()

    def handle_key(self, key):
        """Convert a keypress to a tool button press"""
        self.press_mode_button(key)

    def set_threshold(self, value):
        """Set threshold to value"""
        if self.editor:
            self.editor.set_threshold(value)
            self.threshold = value

    def set_blur(self, value):
        """Set blur to value"""
        self.blur_value = value
        if self.editor:
            self.editor.set_blur(value)

    def set_min(self, value):
        """Set min size to value"""
        if self.editor:
            self.editor.set_min(value)

    def set_max(self, value):
        """Set max size to value"""
        if self.editor:
            self.editor.set_max(value)

    def set_alpha(self, value):
        """Set alpha to value"""
        if self.editor:
            self.editor.set_alpha(value/10) # slider is int, alpha is float

    def set_line_thickness(self, value):
        """Set line thickness for cut/draw tool to value"""
        if self.editor:
            self.editor.set_line_thickness(value)
            if self.editor.mode == ToolMode.CUT:
                self.cut_size = value
            if self.editor.mode == ToolMode.DRAW:
                self.draw_size = value

    def set_outline_thickness(self, value):
        """Set outline thickness to value"""
        if self.editor:
            self.editor.set_outline_thickness(value)

    def set_font_size(self, value):
        """Set the font size to value"""
        if self.editor:
            self.editor.set_font_size(value)

    def set_eraser_size(self, value):
        """Set eraser size to value"""
        if self.editor:
            self.editor.set_eraser_size(value)

    def set_mode(self, value):
        """Set mode to value, and display submenus"""
        if self.editor:
            if value == ToolMode.COUNT_UNMYEL:
                self.editor.set_mode(ToolMode.COUNT)
                self.editor.set_cur_group('Unmyelinated Axons')
            elif value == ToolMode.COUNT_MYEL:
                self.editor.set_mode(ToolMode.COUNT)
                self.editor.set_cur_group('Myelinated Axons')
            else: self.editor.set_mode(value)
        if value == ToolMode.CUT:
            self.show_line_thickness_sliders()
            self.line_thickness_slider.setValue(self.cut_size)
        elif value == ToolMode.DRAW:
            self.show_line_thickness_sliders()
            self.line_thickness_slider.setValue(self.draw_size)
        elif value == ToolMode.ERASE:
            self.show_eraser_size_sliders()
        else:
            self.hide_all_sliders()

    def press_mode_button(self, value):
        """Press the tool button with value value"""
        self.tool_buttons.press_btn(value)

    def set_calibration(self, value):
        """Set calibration to value cast as float"""
        if self.editor:
            self.editor.set_calibration(float(value))

    def reset(self):
        """Reset sliders to default values"""
        self.threshold_slider.reset()
        self.min_slider.reset()
        self.max_slider.reset()
        self.alpha_slider.reset()
        self.line_thickness_slider.reset()

    def displayMessage(self, message, title):
        """Display message with title"""
        self.parent.displayMessage(message, title)

    def set_undo_enabled(self, enable):
        """Enable/disable undo menu item"""
        self.parent.set_undo_enabled(enable)

    def set_redo_enabled(self, enable):
        """Enable/disable redo menu item"""
        self.parent.set_redo_enabled(enable)

    def set_cur_group(self, group):
        """Set current counter group to group"""
        if self.editor:
            self.editor.set_cur_group(group)

    def show_size_sliders(self):
        """Hide all sliders except for Min Size and Max Size"""
        self.hide_all_sliders()
        self.min_max_frame.show()

    def show_appearance_sliders(self):
        """Hide all sliders except for Transparancy and Outline Thickness"""
        self.hide_all_sliders()
        self.appearance_frame.show()

    def show_line_thickness_sliders(self):
        """Hide all sliders except for line thickness slider"""
        self.hide_all_sliders()
        self.line_thickness_frame.show()

    def show_eraser_size_sliders(self):
        """Hide all sliders except for eraser size slider"""
        self.hide_all_sliders()
        self.eraser_size_frame.show()

    def hide_all_sliders(self):
        """Hide all sliders"""
        self.min_max_frame.hide()
        self.appearance_frame.hide()
        self.line_thickness_frame.hide()
        self.eraser_size_frame.hide()

class Axon_Editor:
    """This is the OpenCV image processing implementation"""
    NUM_FEATURES = 3 # number of features to extract

    def __init__(self, filename, quality, config, callback, parent):
        """
        Arguments:
            filename (str): the file to load the image from
            quality (float): the image quality to scale the image to
            config (dict): a variety of parameters to set up the viewport
            callback (function): the function to pass the image to for display
            parent (obj): the parent object of the editor
        """
        self.quality = quality
        self.filename = filename
        self.callback = callback
        self.parent = parent

        # Set up the image
        self.load_image(filename)
        self.image_copy = self.image.copy()
        self.adjust_image()

        # Set up the tools
        self.mode = ToolMode.SEL_AXON
        # -Line Tool Variables
        self.first_point = None
        self.second_point = None
        self.hidden_first_point = None
        self.lines = []
        self.drawing = False
        self.last_img = None
        self.line_thickness = config['line_thickness']
        # -Dot Tool Variables (counter, eraser)
        self.counters = []
        self.cur_point = None
        self.eraser_size = config['eraser_size']
        self.cur_group = config['cur_group']
        # -Contour Tool Variables
        self.cur_contours = []
        self.saved_contours = {
            self.mode_to_string(ToolMode.SEL_AXON): [],
            self.mode_to_string(ToolMode.SEL_MYELIN_IN): [],
            self.mode_to_string(ToolMode.SEL_MYELIN_OUT): [],
            self.mode_to_string(ToolMode.SEL_MISC): []
        }
        self.drawn_contour = []
        self.contour_pairs = []
        self.contour_pairless = []
        self.contour_pairless_grouped = {
            self.mode_to_string(ToolMode.SEL_AXON): [],
            self.mode_to_string(ToolMode.SEL_MYELIN_IN): [],
            self.mode_to_string(ToolMode.SEL_MYELIN_OUT): []
        }
        self.highlight_contours = []
        self.threshold = config['threshold']
        self.blur = config['blur']
        self.min_size = config['min_size']
        self.max_size = config['max_size']
        self.correction_scaling = 1.00 # Change this to scale contours
        # -Misc Display Options
        self.display_options = {
            'outlines': True,
            'highlights': True,
            'counters': True,
            'lines': True,
            'threshold': False,
        }
        self.alpha = config['alpha']
        self.outline_thickness = config['outline_thickness']
        self.font_size = config['font_size']
        self.calibration = config['calibration']

        # Flags For Drawing in show function
        self.force_redraw = False
        self.first_draw = True
        self.redraw_contours = True

        # Undo and Redo History
        self.undo_history = []
        self.redo_history = []
        self.undo_history_len = 30
        self.check_undo_status()

        self.show()
        self.first_draw = False

    def load_image(self, filename):
        """Load image from filename (str)"""
        self.image = cv.imread(self.filename)
        self.filename = filename

    def adjust_image(self):
        """Resizes image to the percent indicated by self.quality"""
        height, width, channels = self.image.shape 

        new_dims = (int(width*self.quality), int(height*self.quality))
        self.image_copy = cv.resize(self.image, None, 
                                    fx=self.quality, fy=self.quality, 
                                    interpolation=cv.INTER_AREA)

    def set_threshold(self, value):
        """Sets the threshold to value (int) and redraws contours"""
        if value != self.threshold:
            self.threshold = value
            self.redraw_contours = True
            self.last_img = None
            self.show()

    def set_blur(self, value):
        """Sets the blur to value (int) and redraws contours"""
        if value != self.blur:
            self.blur = value
            self.redraw_contours = True
            self.show()

    def set_min(self, value):
        """Sets the min acceptable area to value (int) and redraws contours"""
        if value != self.min_size:
            self.min_size = value
            self.redraw_contours = True
            self.show()

    def set_max(self, value):
        """Sets the max acceptable area to value (int) and redraws contours"""
        if value != self.max_size:
            self.max_size = value
            self.redraw_contours = True
            self.show()

    def set_alpha(self, value):
        """Sets the overlay alpha to value (float)"""
        if value != self.alpha:
            self.alpha = value
            self.show()

    def set_line_thickness(self, value):
        """Sets the line thickness to value (int)"""
        if value != self.line_thickness:
            self.line_thickness = value
            self.show()

    def set_outline_thickness(self, value):
        """Sets the outline thickness to value (int)"""
        if value != self.outline_thickness:
            self.outline_thickness = value
            self.show()

    def set_font_size(self, value):
        """Sets the font size to value (float)"""
        if value != self.font_size:
            self.font_size = value
            self.show()

    def set_eraser_size(self, value):
        """Sets the eraser size to value (int)"""
        if value != self.eraser_size:
            self.eraser_size = value
            self.show()

    def set_calibration(self, value):
        """Sets the calibration value to value (float)"""
        if value != self.calibration:
            self.calibration = value
            self.show()

    def set_quality(self, value):
        """Sets the quality to value (float)"""
        if value != self.quality:
            self.quality = value

    def set_cur_group(self, value):
        """Sets the current group to value (str)"""
        self.cur_group = value

    def toggle_outlines(self, value):
        """Toggles outline visibility depending on value (bool)"""
        self.display_options['outlines'] = value
        self.force_redraw = True
        self.last_img = None
        self.show()

    def toggle_highlights(self, value):
        """Toggles highlight visibility depending on value (bool)"""
        self.display_options['highlights'] = value
        self.force_redraw = True
        self.last_img = None
        self.show()

    def toggle_counters(self, value):
        """Toggles counter visibility depending on value (bool)"""
        self.display_options['counters'] = value
        self.force_redraw = True
        self.last_img = None
        self.show()

    def toggle_lines(self, value):
        """Toggles line visibility depending on value (bool)"""
        self.display_options['lines'] = value
        self.force_redraw = True
        self.last_img = None
        self.show()

    def toggle_threshold_overlay(self, value):
        """Toggles threshold overlay visibility depending on value (bool)"""
        self.display_options['threshold'] = value
        self.force_redraw = True
        self.last_img = None
        self.show()

    def reset_tool(self):
        """Resets the current tool"""
        self.set_mode(self.mode)

    def add_to_undo(self, state):
        """Adds state to undo history"""
        if len(self.undo_history) == self.undo_history_len:
            self.undo_history = self.undo_history[1:self.undo_history_len]
        self.undo_history.append(state)
        self.check_undo_status()

    def add_to_redo(self, state):
        """Adds state to redo history"""
        if len(self.redo_history) == self.undo_history_len:
            self.redo_history = self.redo_history[1:self.undo_history_len]
        self.redo_history.append(state)
        self.check_undo_status()

    def undo(self):
        """Undo the most recent action"""
        if self.undo_history:
            cur_state = self.get_state()
            self.add_to_redo(cur_state)
            state = self.undo_history.pop(-1)
            self.load_state(state)
            self.redraw_contours = True
            self.show()
            self.reset_tool()
            self.check_undo_status()

    def clear_redo(self):
        """Clears the redo history"""
        self.redo_history = []
        self.check_undo_status()

    def redo(self):
        """Redo the most recently undone action"""
        if self.redo_history:
            cur_state = self.get_state()
            self.add_to_undo(cur_state)
            state = self.redo_history.pop(-1)
            self.load_state(state)
            self.redraw_contours = True
            self.show()
            self.reset_tool()
            self.check_undo_status()

    def check_undo_status(self):
        """Update the usability of the undo/redo menu buttons"""
        self.parent.set_undo_enabled(len(self.undo_history) > 0)
        self.parent.set_redo_enabled(len(self.redo_history) > 0)
        
    @staticmethod
    def line_intersect(A,B,C,D):
        """Returns true if line segments AB and CD intersect"""
        def ccw(A,B,C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

    @staticmethod
    def point_in_circle(point, circle_point, circle_radius):
        """Returns True if point is inside of the circle, inclusive"""
        distance = sqrt((point[0] - circle_point[0])**2 
                        + (point[1] - circle_point[1])**2)
        return distance <= circle_radius

    @staticmethod
    def line_circle_intersect(point_a, point_b, circle_point, circle_radius):
        """
        Returns True if the line ab intersects (inclusive) or has any point 
        inside of the circle (inclusive)
        """
        if (Axon_Editor.point_in_circle(point_a, circle_point, circle_radius) or
            Axon_Editor.point_in_circle(point_b, circle_point, circle_radius)):
            return True
        return False

        a = point_a[1] - point_b[1]
        b = point_b[0] - point_a[0]
        c = point_a[0]*point_b[1] - point_b[0]*point_a[1]
        x = circle_point[0]
        y = circle_point[1]

        if sqrt(a * a + b * b) == 0:
            return False

        distance = ((abs(a * x + b * y + c)) / sqrt(a * a + b * b))
        return distance <= circle_radius

    @staticmethod
    def polyline_circle_intersects(polyline, circle_point, circle_radius):
        """
        Returns the indices of any point on a polyline involved in an 
        intersection with a circle
        """
        indices = []
        for i in range(len(polyline)):
            if Axon_Editor.point_in_circle(polyline[i], circle_point, 
                                           circle_radius):
                indices.append(i)
        return indices

    @staticmethod
    def polyline_circle_nonintersects(polyline, circle_point, circle_radius):
        """
        Returns the indices of any point on a polyline not involved in an
        intersection with a circle
        """
        result = []
        indices = Axon_Editor.polyline_circle_intersects(polyline, circle_point, 
                                                         circle_radius)
        for i in range(len(polyline)):
            if not i in indices:
                result.append(i)
        return Axon_Editor.get_ranges(result)

    @staticmethod
    def get_ranges(unfiltered):
        """
        Converts a list into ranges
        e.g. [1,2,3,4,5,8,9,23] => [(1,5),(8,9),23]
        """
        if len(unfiltered) <= 1:
            return []
        result = []
        low = None
        high = None
        last = unfiltered[0]
        for i in range(len(unfiltered)):
            if i == 0:
                low = unfiltered[i]
                continue
            elif i == len(unfiltered)-1:
                high = unfiltered[i]
                if low is not None:
                    result.append((low, high))
                continue
            elif (unfiltered[i] != unfiltered[i-1] + 1 and 
                  unfiltered[i+1] == unfiltered[i] + 1):
                low = unfiltered[i]
                high = None
            elif (unfiltered[i] == unfiltered[i-1] + 1 and 
                  unfiltered[i+1] != unfiltered[i] + 1):
                high = unfiltered[i]
                if low is not None:
                    result.append((low, high))
                low = None
        return result

    def set_mode(self, new_mode):
        """Set the current mode to new_mode (ToolMode)"""
        self.mode = new_mode
        self.force_redraw = True
        self.first_point = None
        self.second_point = None
        self.last_img = None
        self.cur_point = None
        self.drawing = False
        self.show()

    def get_filename(self):
        """Returns the image filename without the extension"""
        file_name = self.filename.split('/')[-1]
        return '.'.join(file_name.split('.')[:-1])


    def find_pairs(self):
        """Pairs up contours in Axon, Inner Myelin, and Outer Myelin stacks"""
        seen = []
        self.contour_pairs = []
        self.contour_pairless = []
        self.contour_pairless_grouped = {
            self.mode_to_string(ToolMode.SEL_AXON): [],
            self.mode_to_string(ToolMode.SEL_MYELIN_IN): [],
            self.mode_to_string(ToolMode.SEL_MYELIN_OUT): []
        }

        # Go through axons in selection order
        axons = self.saved_contours[self.mode_to_string(ToolMode.SEL_AXON)]
        for a in axons:
            paired_up = [a]
            M = cv.moments(a)
            a_xy = (int(M["m10"] / M["m00"]),int(M["m01"] / M["m00"]))
            a_point = tuple(a[0][0])

            is_inner = False
            
            # look for overlapping inner myelin sheath
            inner = self.saved_contours[
                self.mode_to_string(ToolMode.SEL_MYELIN_IN)]
            for b in inner:
                if any(np.array_equal(b, s) for s in seen):
                    continue
                if (cv.pointPolygonTest(b, a_xy, False) > 0 or 
                    cv.pointPolygonTest(b, a_point, False) >= 0):
                    paired_up.append(b)
                    seen.append(b)
                    is_inner = True
                    break


            # and overlapping outer myelin sheath
            outer = self.saved_contours[
                self.mode_to_string(ToolMode.SEL_MYELIN_OUT)]
            for c in outer:
                if any(np.array_equal(c, s) for s in seen):
                    continue
                if (cv.pointPolygonTest(c, a_xy, False) > 0 or 
                    cv.pointPolygonTest(c, a_point, False) >= 0):
                    paired_up.append(c)
                    seen.append(c)
                    break

            # check for full stack
            if len(paired_up) == self.NUM_FEATURES:
                paired_up.sort(key=cv.contourArea, reverse=True)
                self.contour_pairs += paired_up
            else:
                group = self.contour_pairless_grouped[
                    self.mode_to_string(ToolMode.SEL_AXON)]
                group.append(paired_up[0])
                if len(paired_up) == 2:
                    if is_inner:
                        group = self.contour_pairless_grouped[
                            self.mode_to_string(ToolMode.SEL_MYELIN_IN)]
                        group.append(paired_up[1])
                    else:
                        group = self.contour_pairless_grouped[
                            self.mode_to_string(ToolMode.SEL_MYELIN_OUT)]
                        group.append(paired_up[1])

                self.contour_pairless += paired_up

        # Round up any lonely inner or outer
        inner = self.saved_contours[self.mode_to_string(ToolMode.SEL_MYELIN_IN)]
        for b in inner:
            if any(np.array_equal(b, s) for s in seen):
                continue
            self.contour_pairless.append(b)
            group = self.contour_pairless_grouped[
                self.mode_to_string(ToolMode.SEL_MYELIN_IN)]
            group.append(b)

        outer = self.saved_contours[
            self.mode_to_string(ToolMode.SEL_MYELIN_OUT)]
        for c in outer:
            if any(np.array_equal(c, s) for s in seen):
                continue
            self.contour_pairless.append(c)
            group = self.contour_pairless_grouped[
                self.mode_to_string(ToolMode.SEL_MYELIN_OUT)]
            group.append(c)


    def mode_to_string(self, mode):
        """Convert mode (ToolMode) to string, for storing in file"""
        if mode == ToolMode.SEL_AXON:
            return 'axon'
        if mode == ToolMode.SEL_MYELIN_IN:
            return 'inner myelin'
        if mode == ToolMode.SEL_MYELIN_OUT:
            return 'outer myelin'
        if mode == ToolMode.SEL_MISC:
            return 'misc'

    def erase(self, erase_point):
        """Erases any points within the eraser, with location erase_point"""
        removed_something = False
        new_points = []
        for point, group in self.counters:
            if not Axon_Editor.point_in_circle(point, erase_point, 
                                               self.eraser_size):
                new_points.append((point, group))
            else:
                removed_something = True
        self.counters = new_points

        new_lines = []
        for line_group in self.lines:
            thickness, color, points = line_group
            if len(points) == 1:
                if isinstance(points[0][0], tuple): # a straight line, 2 points
                    if not Axon_Editor.line_circle_intersect(points[0][0],
                                                             points[0][1],
                                                             erase_point,
                                                             self.eraser_size):
                        new_lines.append(line_group)
                    else:
                        removed_something = True
                else: # a single point
                    if not Axon_Editor.point_in_circle(points[0], 
                                                       erase_point,
                                                       self.eraser_size):
                        new_lines.append(line_group)
                    else:
                        removed_something = True
            else:
                to_keep = Axon_Editor.polyline_circle_nonintersects(
                    points, erase_point, self.eraser_size)
                for index_range in to_keep:
                    new_line_group = [thickness, color, 
                                      points[index_range[0]:index_range[1]+1]]
                    new_lines.append(new_line_group)
                removed_something = True
        self.lines = new_lines

        if removed_something:
            self.last_img = None
            self.show()

    def mouse_event(self, event, x, y, flags, param, modifiers = None):
        """
        OpenCV mouse event handler

        Arguments:
            event (cv.MouseEventTypes): the mouse event, e.g. left click
            x (int): the x coordinate of the event
            y (int): the y coordinate of the event
            flags: unused
            param: unused
            modifiers (qt.KeyboardModifiers): e.g. shift key is pressed
        """
        # Mouse is out of bounds
        if not (0 <= x < self.image.shape[0]  or 0 <= y < self.image.shape[1]):
            if len(self.highlight_contours) > 0:
                self.highlight_contours = []
            return

        # Left click
        if event == cv.EVENT_LBUTTONDOWN:
            cur_state = self.get_state()
            self.clear_redo()
            # Select: Save the starting point for now
            if self.mode in (ToolMode.SEL_AXON, ToolMode.SEL_MYELIN_IN, 
                             ToolMode.SEL_MYELIN_OUT, ToolMode.SEL_MISC): 
                self.first_point = (x, y)
                return

            # Deselect: Clear any contours that surround the click point
            if self.mode == ToolMode.DESELECT:
                for m in self.saved_contours:
                    new_contours = []
                    removed_contours = False
                    for i in range(len(self.saved_contours[m])):
                        c = self.saved_contours[m][i]
                        if cv.pointPolygonTest(c,(x,y), False) <= 0:
                            new_contours.append(c)
                        else:
                            True
                    if removed_contours:
                        self.add_to_undo(cur_state)
                    self.saved_contours[m] = new_contours
                self.redraw_contours = True
                self.show()
                return

            # Cut/Draw: Start or continue drawing lines
            if self.mode == ToolMode.CUT or self.mode == ToolMode.DRAW:
                if modifiers == Qt.ShiftModifier: # Straight line
                    if self.first_point is None:
                        self.hidden_first_point = (x, y)
                    else:
                        if self.second_point is not None:
                            if self.mode == ToolMode.CUT:
                                line_color = Colors.WHITE.value
                            else:
                                line_color = Colors.BLACK.value
                            self.lines.append([self.line_thickness, line_color,
                                 [(self.first_point, self.second_point)]])
                            self.add_to_undo(cur_state)
                            self.first_point = None
                            self.hidden_first_point = self.second_point
                            self.last_img = None
                else: # Freehand Line
                    self.drawing = True
                    self.first_point = None
                    if self.mode == ToolMode.CUT:
                        line_color = Colors.WHITE.value
                    else:
                        line_color = Colors.BLACK.value
                    self.lines.append([self.line_thickness, line_color, []])
                    self.add_to_undo(cur_state)

            # Counting: Add a counter to the click point
            if self.mode == ToolMode.COUNT:
                self.last_img = None
                self.counters.append(((x, y), self.cur_group))
                self.add_to_undo(cur_state)

            # Erase: Erase any points the current click point
            if self.mode == ToolMode.ERASE:
                self.add_to_undo(cur_state)
                self.drawing = True

            # Info: Check what is overlapping this selection
            if self.mode == ToolMode.INFO:
                selected = {}
                for mode in (ToolMode.SEL_AXON, ToolMode.SEL_MYELIN_IN, 
                             ToolMode.SEL_MYELIN_OUT):
                    selected[mode] = 0
                    contours = self.saved_contours[self.mode_to_string(mode)]
                    for i in range(len(contours)):
                        c = contours[i]
                        r = cv.pointPolygonTest(c, (x,y), False)
                        if r > 0:
                            selected[mode] += 1
                if (selected[ToolMode.SEL_AXON] == 1 and 
                    selected[ToolMode.SEL_MYELIN_IN] == 1 and 
                    selected[ToolMode.SEL_MYELIN_OUT] == 1):
                    self.parent.displayMessage('This selection is complete!',
                                               'Info')
                    return
                message = '<b>This selection is incomplete</b>:'
                too_many_msg = 'Too many: '
                if selected[ToolMode.SEL_AXON] > 1:
                    too_many_msg += 'axons ({}), '.format(
                        selected[ToolMode.SEL_AXON])
                if selected[ToolMode.SEL_MYELIN_IN] > 1:
                    too_many_msg += 'inner myelin sheaths ({}), '.format(
                        selected[ToolMode.SEL_MYELIN_IN])
                if selected[ToolMode.SEL_MYELIN_OUT] > 1:
                    too_many_msg += 'outer myelin sheaths ({}), '.format(
                        selected[ToolMode.SEL_MYELIN_OUT])
                if too_many_msg != 'Too many: ':
                    message += '<br>' + too_many_msg[:-2]
                missing_msg = 'Missing: '
                if selected[ToolMode.SEL_AXON] == 0:
                    missing_msg += 'axon, '
                if selected[ToolMode.SEL_MYELIN_IN] == 0:
                    missing_msg += 'inner myelin sheath, '
                if selected[ToolMode.SEL_MYELIN_OUT] == 0:
                    missing_msg += 'outer myelin sheath, '
                if missing_msg != 'Missing: ':
                    message += '<br>' + missing_msg[:-2]
                self.parent.displayMessage(message, 'Info')

        # Mouse moved in draw modes
        if self.mode == ToolMode.CUT or self.mode == ToolMode.DRAW:
            # Currently doing a straight line
            if self.first_point is not None and modifiers == Qt.ShiftModifier:
                self.second_point = (x, y)
                self.show()
                return

            if self.drawing: # Currently doing a freehand line
                if event == cv.EVENT_LBUTTONUP:
                    self.drawing = False
                    self.hidden_first_point = (x, y)
                    self.last_img = None
                    self.first_point = None
                    self.redraw_contours = True
                else:
                    self.lines[-1][-1].append((x,y))
            else: # Mouse moved, but not doing freehand
                if modifiers == Qt.ShiftModifier:
                    self.first_point = self.hidden_first_point
                else:
                    self.first_point = None
            self.show()
            return

        # Mouse move or release on selected features
        if self.mode in (ToolMode.SEL_AXON, ToolMode.SEL_MYELIN_IN, 
                         ToolMode.SEL_MYELIN_OUT, ToolMode.SEL_MISC):
            if event == cv.EVENT_LBUTTONUP: 
                self.first_point = None
                cur_state = self.get_state()
                if self.drawing:
                    new_contour = np.array(self.drawn_contour, dtype=np.int32)
                    if cv.contourArea(new_contour) > 0: # filter out lines
                        mode_string = self.mode_to_string(self.mode)
                        self.saved_contours[mode_string].append(new_contour)
                        self.add_to_undo(cur_state)
                    self.drawn_contour = []
                    self.display_options = self.prev_display_options
                    self.drawing = False
                    self.last_img = None
                    self.redraw_contours = True
                    self.show()
                    return
                contours = self.saved_contours[self.mode_to_string(self.mode)]
                for i in range(len(contours)):
                    r = cv.pointPolygonTest(contours[i],(x,y), False)
                    if r > 0: # remove already selected contour
                        old_contour = contours.pop(i)
                        self.add_to_undo(cur_state)
                        self.redraw_contours = True
                        self.show()
                        return
                enveloping_contours = [c for c in self.cur_contours 
                                      if cv.pointPolygonTest(c,(x,y),False) > 0]
                if enveloping_contours:
                    conts = self.saved_contours[self.mode_to_string(self.mode)]
                    conts.append(min(enveloping_contours, key=cv.contourArea))
                    self.add_to_undo(cur_state)
                    self.redraw_contours = True
                    self.show()
                    return
            if self.first_point and not self.drawing:
                distance = cv.norm(self.first_point, (x, y))
                if distance > 3: # Activation distance for the drawing mechanism
                    self.drawing = True
                    self.drawn_contour = [[self.first_point]]
                    self.prev_display_options = self.display_options
                    self.display_options = { # Hide the overlay
                        'outlines': False,
                        'highlights': False,
                        'counters': False,
                        'lines': True,
                        'threshold': False,
                    }
                    self.last_img = None
            if self.drawing:
                self.drawn_contour.append([(x, y)])
                self.first_point = (x, y)
                self.show()
                return

            # Apply highlights
            contours = self.saved_contours[self.mode_to_string(self.mode)]
            saved_highlights = [s for s in contours
                                if cv.pointPolygonTest(s, (x,y), False) > 0]
            if saved_highlights:
                self.highlight_contours = [(
                    min(saved_highlights, key=cv.contourArea),
                    Colors.RED_HIGHLIGHT.value)]
                self.show()
                return

            current_highlights = [c for c in self.cur_contours 
                                  if cv.pointPolygonTest(c, (x,y), False) > 0]
            if current_highlights:
                self.highlight_contours = [(
                    min(current_highlights, key=cv.contourArea),
                    Colors.GREEN_HIGHLIGHT.value)]
                self.show()
                return

        # Deselect: Highlight any contours hovered
        if self.mode == ToolMode.DESELECT:
            self.highlight_contours = []
            for m in self.saved_contours:
                for s in self.saved_contours[m]:
                    if cv.pointPolygonTest(s, (x, y), False) > 0:
                        self.highlight_contours.append((s, Colors.RED_HIGHLIGHT.value))
            if self.highlight_contours:
                self.show()
                return

        # Move the counter button
        if self.mode == ToolMode.COUNT:
            self.cur_point = (x, y)

        # Move the eraser tool
        if self.mode == ToolMode.ERASE:
            self.cur_point = (x, y)
            if event == cv.EVENT_LBUTTONUP:
                self.drawing = False
                self.redraw_contours = True
                self.last_img = None
            if self.drawing:
                self.erase((x,y))

        # If we get here, then no highlights were made in this tick
        if len(self.highlight_contours) > 0:
            self.highlight_contours = []
        
        self.show()

    def find_contours(self):
        """Extracts contours from the current screen"""
        # 1. Convert to grayscale
        imgray = cv.cvtColor(self.image_copy, cv.COLOR_BGR2GRAY)

        # 2. Apply blur kernel
        if self.blur == 0:
            blurred_image = imgray
        else:
            blurred_image = cv.bilateralFilter(imgray,1+self.blur, 75, 75)

        # 3. Apply thresholding filter
        _, thresholded = cv.threshold(blurred_image, self.threshold, 255, 
                                      cv.THRESH_TRUNC)
        _, thresholded = cv.threshold(thresholded, self.threshold*15/16, 255, 
                                      cv.THRESH_BINARY)

        # 4. Draw cut and draw lines on the image
        for points in self.lines:
            cv.polylines(thresholded,[np.array(points[-1])], False, points[1], 
                         points[0])

        # 5. Extract contours from the image
        contour_data = cv.findContours(thresholded, cv.RETR_TREE,
                                       cv.CHAIN_APPROX_SIMPLE)
        if len(contour_data) == 2:
            contours = contour_data[0]
        else:
            contours = contour_data[1]

        # 6. Filter out contours based on min and max size
        self.cur_contours = [c for c in contours 
            if (len(c) >= 5 and 
                self.min_size <= cv.contourArea(c) <= self.max_size)]

    def show(self, value=0):
        """Generates image to display, with all overlay features"""
        if self.force_redraw: # Draw everything again
            self.force_redraw = False
        # Line tools, draw and cut
        elif (not self.force_redraw and 
              self.first_point is not None and 
              self.last_img is not None):
            display_image = self.last_img.copy()
            if self.display_options['lines'] and self.second_point:
                display_image = cv.line(display_image, self.first_point,
                                        self.second_point, Colors.GREEN.value,
                                        self.line_thickness)
            if self.drawn_contour:
                cv.polylines(display_image, [np.array(self.drawn_contour)],
                             False, Colors.GREEN.value, 1)

            self.callback(display_image, self.first_draw)
            return
        # Point tools, counter and eraser
        elif (not self.force_redraw and 
              self.cur_point is not None and 
              self.last_img is not None):
            display_image = self.last_img.copy()
            if self.cur_point is not None:
                if self.mode == ToolMode.COUNT:
                    if self.cur_group == 'Unmyelinated Axons':
                        color = Colors.PURPLE.value
                    elif self.cur_group == 'Myelinated Axons':
                        color = Colors.LIME.value
                    else:
                        color = Colors.PINK.value
                    display_image = cv.circle(display_image, self.cur_point, 3, 
                                              color, -1)
                    display_image = cv.circle(display_image, self.cur_point, 3, 
                                              Colors.BLACK.value, 2)
                elif self.mode == ToolMode.ERASE:
                    display_image = cv.circle(display_image, self.cur_point, 
                                              self.eraser_size, 
                                              Colors.BLACK.value, 2)
            self.callback(display_image, self.first_draw)
            if not self.redraw_contours:
                return

        # Recalculate contours if necessary
        if self.redraw_contours:
            self.find_contours()
            self.find_pairs()
            self.redraw_contours = False

        # Show threshold as overlay
        if self.display_options['threshold']:
            imgray = cv.cvtColor(self.image_copy, cv.COLOR_BGR2GRAY)

            if self.blur == 0:
                blurred_image = imgray
            else:
                blurred_image = cv.bilateralFilter(imgray,1+self.blur, 75, 75)

            _, thresholded = cv.threshold(blurred_image, self.threshold, 255, 
                                          cv.THRESH_TRUNC)
            _, thresholded = cv.threshold(thresholded, self.threshold*15/16, 
                                          255, cv.THRESH_BINARY)

            base_image = cv.cvtColor(thresholded, cv.COLOR_GRAY2BGR)
            overlay_image = cv.cvtColor(thresholded, cv.COLOR_GRAY2BGR)
        else:
            base_image = self.image_copy.copy()
            overlay_image = self.image_copy.copy()

        # Draw contour outlines
        if self.display_options['outlines']:
            cv.drawContours(overlay_image, self.cur_contours, -1, 
                            Colors.YELLOW.value, self.outline_thickness)
            for c in self.saved_contours.values():
                cv.drawContours(overlay_image, c, -1, Colors.BLACK.value, 
                                self.outline_thickness)

        # Draw highlights
        if self.display_options['highlights']:
            cv.drawContours(overlay_image, self.contour_pairs, -1, 
                            Colors.CYAN_HIGHLIGHT.value, cv.FILLED)
            cv.drawContours(overlay_image, self.contour_pairless, -1, 
                            Colors.ORANGE_HIGHLIGHT.value, cv.FILLED)
            cv.drawContours(overlay_image, self.saved_contours[
                                        self.mode_to_string(ToolMode.SEL_MISC)],
                            -1, Colors.CYAN_HIGHLIGHT.value, cv.FILLED)
            if len(self.highlight_contours) > 0:
                for c_group in self.highlight_contours:
                    cv.drawContours(overlay_image, (c_group[0],), -1, 
                                    c_group[1], cv.FILLED)

        # Merge the overlay image to the base with alpha
        display_image = cv.addWeighted(overlay_image, self.alpha, base_image, 
                                       1-self.alpha, 0)

        # Add counter and number overlay
        if self.display_options['counters']:
            # Draw group indicators:
            for point, group in self.counters:
                if group == 'Unmyelinated Axons':
                    color = Colors.PURPLE.value
                elif group == 'Myelinated Axons':
                    color = Colors.LIME.value
                else:
                    color = Colors.PINK.value
                display_image = cv.circle(display_image, point, 3, color, -1)
                display_image = cv.circle(display_image, point, 3, 
                                          Colors.BLACK.value, 2)
                cv.putText(display_image, group[0], 
                           (point[0] - int(self.font_size * 8), point[1] + int(self.font_size * 4)),
                           cv.FONT_HERSHEY_SIMPLEX, self.font_size, color,
                           int(2*self.font_size))

            # Draw numbers for pairs
            for i in range(0,len(self.contour_pairs),self.NUM_FEATURES):
                c = self.contour_pairs[i]
                M = cv.moments(c)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                cv.putText(display_image, str(i//self.NUM_FEATURES+1), (cX - int(self.font_size * 8), cY + int(self.font_size * 4)),
                           cv.FONT_HERSHEY_SIMPLEX, self.font_size, Colors.WHITE.value,
                           int(2*self.font_size))

        # Add cut and draw lines
        if self.display_options['lines']:
            for points in self.lines:
                cv.polylines(display_image,[np.array(points[-1])],False,
                             points[1], points[0])


        # If we started drawing a line, capture this image to avoid redraw
        if ((self.first_point is not None or self.cur_point is not None) and 
            self.last_img is None):
            self.last_img = display_image.copy()

        # Pass the image back to the container
        self.callback(display_image, self.first_draw)

    def get_totals(self, count_selections=False, only_complete=False, 
                   include_counters=True):
        """
        Helper function for export, counts up the selections and counters

        Arguments:
            count_selections (bool): count feature selections or not
            only_complete (bool): only count complete selections
            include_counters (bool): count group counters as well

        Returns a string for csv
        """
        first_line, second_line = '', ''

        if count_selections:
            num_complete = len(self.contour_pairs) // 3
            if num_complete > 0:
                first_line += 'Complete,'
                second_line += '{},'.format(num_complete)
            num_incomplete = len(self.contour_pairless)
            if not only_complete and num_incomplete > 0:
                first_line += 'Incomplete,'
                second_line += '{},'.format(num_incomplete)

        if include_counters:
            counter_totals = {}
            for _, group in self.counters:
                cur_total = counter_totals.get(group, 0)
                counter_totals[group] = cur_total + 1
            for group in counter_totals:
                first_line += group + ','
                second_line += '{},'.format(counter_totals[group])
            total = (counter_totals.get('Myelinated Axons', 0) 
                     + counter_totals.get('Unmyelinated Axons', 0))
            if total == 0:
                total = 1
            dec_myelin = counter_totals.get('Myelinated Axons', 0) / total
            percent_myelinated = round(dec_myelin * 100, 2)
            first_line += 'Percent Myelinated'
            second_line += '{}%'.format(percent_myelinated)

        return first_line + '\n' + second_line


    def export(self, directory, export_selections):
        """Export data specified in export_selections to directory as csv"""
        file_path = directory + '/'

        file_name = self.filename.split('/')[-1]
        new_filename = (file_path + '.'.join(file_name.split('.')[:-1]) 
                        + '-overlay.' + file_name.split('.')[-1])

        overlay = self.image_copy.copy()

        text_to_add = []

        adjusted_calibration = self.calibration / self.quality

        text_filename = (file_path + '.'.join(file_name.split('.')[:-1])
                         + '-area_calculations.csv')
        with open(text_filename, 'w') as f:
            to_write = 'Number,'
            if export_selections['Axon Area']:
                to_write += 'Axon Area,'
            if export_selections['Inner Myelin Area']:
                to_write += 'Inner Area,'
            if export_selections['Outer Myelin Area']:
                to_write += 'Outer Area,'
            if export_selections['Axon Perimeter']:
                to_write += 'Axon Perimeter,'
            if export_selections['Inner Myelin Perimeter']:
                to_write += 'Inner Perimeter,'
            if export_selections['Outer Myelin Perimeter']:
                to_write += 'Outer Perimeter,'
            if export_selections['Axon Diameter']:
                to_write += 'Axon Diameter,'
            if export_selections['Inner Myelin Diameter']:
                to_write += 'Inner Diameter,'
            if export_selections['Outer Myelin Diameter']:
                to_write += 'Outer Diameter,'
            if export_selections['g-ratio']:
                to_write += 'g-ratio,'
            to_write += '\n'
            f.write(to_write)

            cur_index = 0
            for i in range(0,len(self.contour_pairs),self.NUM_FEATURES):
                sub_to_write = ''
                axon_a = (cv.contourArea(self.scale_contour(
                                            self.contour_pairs[i+2], 
                                            self.correction_scaling))
                          * adjusted_calibration ** 2)
                if export_selections['Axon Area']:
                    sub_to_write += (str(axon_a) + ',') 
                inner_a = (cv.contourArea(self.scale_contour(
                                            self.contour_pairs[i+1], 
                                            self.correction_scaling)) 
                           * adjusted_calibration ** 2)
                if export_selections['Inner Myelin Area']:
                    sub_to_write += (str(inner_a) + ',') 
                outer_a = (cv.contourArea(self.scale_contour(
                                            self.contour_pairs[i], 
                                            self.correction_scaling)) 
                           * adjusted_calibration ** 2)
                if export_selections['Outer Myelin Area']:
                    sub_to_write += (str(outer_a) + ',') 

                axon_p = (cv.arcLength(self.scale_contour(
                                        self.contour_pairs[i+2], 
                                        self.correction_scaling), True) 
                          * adjusted_calibration)
                if export_selections['Axon Perimeter']:
                    sub_to_write += (str(axon_p) + ',')
                inner_p = (cv.arcLength(self.scale_contour(
                                        self.contour_pairs[i+1], 
                                        self.correction_scaling), True) 
                          * adjusted_calibration)
                if export_selections['Inner Myelin Perimeter']:
                    sub_to_write += (str(inner_p) + ',')
                outer_p = (cv.arcLength(self.scale_contour(
                                        self.contour_pairs[i], 
                                        self.correction_scaling), True) 
                          * adjusted_calibration)
                if export_selections['Outer Myelin Perimeter']:
                    sub_to_write += (str(outer_p) + ',')

                axon_d = sqrt(axon_a/pi)*2
                if export_selections['Axon Diameter']:
                    sub_to_write += (str(axon_d) + ',')
                inner_d = sqrt(inner_a/pi)*2
                if export_selections['Inner Myelin Diameter']:
                    sub_to_write += (str(inner_d) + ',')
                outer_d = sqrt(outer_a/pi)*2
                if export_selections['Outer Myelin Diameter']:
                    sub_to_write += (str(outer_d) + ',')

                gratio = np.sqrt(inner_a / outer_a)
                if export_selections['g-ratio']:
                    sub_to_write += (str(gratio) + ',')
                if sub_to_write:
                    cur_index = i//self.NUM_FEATURES+1
                    to_write = str(cur_index) + ',' + sub_to_write + '\n'
                    f.write(to_write)

                if sub_to_write:
                    cv.drawContours(overlay, self.contour_pairs[i:i+3], -1, 
                                    Colors.CYAN_HIGHLIGHT.value, cv.FILLED)
                    cv.drawContours(overlay, self.contour_pairs[i:i+3], -1, 
                                    Colors.BLACK.value, 1)

                    c = self.contour_pairs[i]
                    M = cv.moments(c)
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    text_to_add.append((str(cur_index), (cX - int(self.font_size * 8), cY + int(self.font_size * 4))))

            mode_string = self.mode_to_string(ToolMode.SEL_AXON)
            for axon in self.contour_pairless_grouped[mode_string]:
                sub_to_write = ''

                a = (cv.contourArea(self.scale_contour(
                                        axon, self.correction_scaling)) 
                     * adjusted_calibration ** 2)
                if export_selections['Axon Area']:
                    sub_to_write += (str(a) + ',')

                if export_selections['Inner Myelin Area']:
                    sub_to_write += ','

                if export_selections['Outer Myelin Area']:
                    sub_to_write += ','

                p = (cv.arcLength(self.scale_contour(
                                      axon, self.correction_scaling), True) 
                     * adjusted_calibration)
                if export_selections['Axon Perimeter']:
                    sub_to_write += (str(p) + ',')

                if export_selections['Inner Myelin Perimeter']:
                    sub_to_write += ','

                if export_selections['Outer Myelin Perimeter']:
                    sub_to_write += ','

                d = sqrt(a/pi)*2
                if export_selections['Axon Diameter']:
                    sub_to_write += (str(d) + ',')

                if export_selections['Inner Myelin Diameter']:
                    sub_to_write += ','

                if export_selections['Outer Myelin Diameter']:
                    sub_to_write += ','

                if len(sub_to_write) != sub_to_write.count(','):
                    cur_index += 1
                    to_write = str(cur_index) + ',' + sub_to_write + '\n'
                    f.write(to_write)

                if len(sub_to_write) != sub_to_write.count(','):
                    cv.drawContours(overlay, [axon], -1, 
                                    Colors.ORANGE_HIGHLIGHT.value, 
                                    cv.FILLED)
                    cv.drawContours(overlay, [axon], -1, 
                                    Colors.BLACK.value, 1)

                    c = axon
                    M = cv.moments(c)
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    text_to_add.append((str(cur_index), (cX - int(self.font_size * 8), cY + int(self.font_size * 4))))

            mode_string = self.mode_to_string(ToolMode.SEL_MYELIN_IN)
            for inner in self.contour_pairless_grouped[mode_string]:
                to_write = str(cur_index) + ','

                sub_to_write = ''

                if export_selections['Axon Area']:
                    sub_to_write += ',' 

                a = (cv.contourArea(self.scale_contour(
                                        inner, self.correction_scaling)) 
                     * adjusted_calibration ** 2)
                if export_selections['Inner Myelin Area']:
                    sub_to_write += (str(a) + ',') 

                if export_selections['Outer Myelin Area']:
                    sub_to_write += ',' 

                if export_selections['Axon Perimeter']:
                    sub_to_write += ',' 

                p = (cv.arcLength(self.scale_contour(
                                      inner, self.correction_scaling), True) 
                     * adjusted_calibration)
                if export_selections['Inner Myelin Perimeter']:
                    sub_to_write += (str(p) + ',') 

                if export_selections['Outer Myelin Perimeter']:
                    sub_to_write += ',' 

                if export_selections['Axon Diameter']:
                    sub_to_write += ',' 

                d = sqrt(a/pi)*2
                if export_selections['Inner Myelin Diameter']:
                    sub_to_write += (str(d) + ',')

                if export_selections['Outer Myelin Diameter']:
                    sub_to_write += ','

                if len(sub_to_write) != sub_to_write.count(','):
                    cur_index += 1
                    to_write = str(cur_index) + ',' + sub_to_write + '\n'
                    f.write(to_write)

                if len(sub_to_write) != sub_to_write.count(','):
                    cv.drawContours(overlay, [inner], -1, 
                                    Colors.ORANGE_HIGHLIGHT.value, 
                                    cv.FILLED)
                    cv.drawContours(overlay, [inner], -1, 
                                    Colors.BLACK.value, 1)

                    c = inner
                    M = cv.moments(c)
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    text_to_add.append((str(cur_index), (cX - int(self.font_size * 8), cY + int(self.font_size * 4))))

            mode_string = self.mode_to_string(ToolMode.SEL_MYELIN_OUT)
            for outer in self.contour_pairless_grouped[mode_string]:
                to_write = str(cur_index) + ','

                sub_to_write = ''

                if export_selections['Axon Area']:
                    sub_to_write += ','

                if export_selections['Inner Myelin Area']:
                    sub_to_write += ','

                a = (cv.contourArea(self.scale_contour(
                                        outer, self.correction_scaling)) 
                     * adjusted_calibration ** 2)
                if export_selections['Outer Myelin Area']:
                    sub_to_write += (str(a) + ',')

                if export_selections['Axon Perimeter']:
                    sub_to_write += ','

                if export_selections['Inner Myelin Perimeter']:
                    sub_to_write += ','

                p = (cv.arcLength(self.scale_contour(
                                      outer, self.correction_scaling), True) 
                     * adjusted_calibration)
                if export_selections['Outer Myelin Perimeter']:
                    sub_to_write += (str(p) + ',')

                if export_selections['Axon Diameter']:
                    sub_to_write += ','

                if export_selections['Inner Myelin Diameter']:
                    sub_to_write += ','

                d = sqrt(a/pi)*2
                if export_selections['Outer Myelin Diameter']:
                    sub_to_write += (str(d) + ',')

                if len(sub_to_write) != sub_to_write.count(','):
                    cur_index += 1
                    to_write = str(cur_index) + ',' + sub_to_write + '\n'
                    f.write(to_write)

                if len(sub_to_write) != sub_to_write.count(','):
                    cv.drawContours(overlay, [outer], -1, 
                                    Colors.ORANGE_HIGHLIGHT.value,
                                    cv.FILLED)
                    cv.drawContours(overlay, [outer], -1,
                                    Colors.BLACK.value, 1)

                    c = outer
                    M = cv.moments(c)
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    text_to_add.append((str(cur_index), (cX - int(self.font_size * 8), cY + int(self.font_size * 4))))

            if (export_selections['Misc. Perimeter']
                    or export_selections['Misc. Area'] 
                    or export_selections['Misc. Diameter']):
                f.write('\nMiscellaneous\n')
                to_write = 'Number,'
                if export_selections['Misc. Area']:
                    to_write += 'Misc. Area,'
                if export_selections['Misc. Perimeter']:
                    to_write += 'Misc. Perimeter,'
                if export_selections['Misc. Diameter']:
                    to_write += 'Misc. Diameter,'
                to_write += '\n'
                f.write(to_write)

                mode_string = self.mode_to_string(ToolMode.SEL_MISC)
                for misc in self.saved_contours[mode_string]:
                    to_write = str(cur_index) + ','

                    sub_to_write = ''

                    a = (cv.contourArea(self.scale_contour(
                                            misc, self.correction_scaling)) 
                         * adjusted_calibration ** 2)
                    if export_selections['Misc. Area']:
                        sub_to_write += (str(a) + ',')

                    p = (cv.arcLength(self.scale_contour(
                                          misc, self.correction_scaling), True) 
                         * adjusted_calibration)
                    if export_selections['Misc. Perimeter']:
                        sub_to_write += (str(p) + ',')

                    d = sqrt(a/pi)*2
                    if export_selections['Misc. Diameter']:
                        sub_to_write += (str(d) + ',')

                    if len(sub_to_write) != sub_to_write.count(','):
                        cur_index += 1
                        to_write = str(cur_index) + ',' + sub_to_write + '\n'
                        f.write(to_write)

                    if len(sub_to_write) != sub_to_write.count(','):
                        cv.drawContours(overlay, [misc], -1, 
                                        Colors.CYAN_HIGHLIGHT.value,
                                        cv.FILLED)
                        cv.drawContours(overlay, [misc], -1,
                                        Colors.BLACK.value, 1)

                        c = misc
                        M = cv.moments(c)
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        text_to_add.append((str(cur_index), (cX - int(self.font_size * 8), cY + int(self.font_size * 4))))

            totals = self.get_totals()
            f.write('\n')
            f.write(totals)
        
        export_image = cv.addWeighted(overlay, self.alpha, self.image_copy, 
                                      1-self.alpha, 0)
        for t in text_to_add:
            cv.putText(export_image, t[0], t[1], cv.FONT_HERSHEY_SIMPLEX, self.font_size, 
                       Colors.WHITE.value, int(2*self.font_size))

        if export_selections['Counters']:
            for point, group in self.counters:
                if group == 'Unmyelinated Axons':
                    color = Colors.PURPLE.value
                elif group == 'Myelinated Axons':
                    color = Colors.LIME.value
                else:
                    color = Colors.PINK.value
                export_image = cv.circle(export_image, point, 3, color, -1)
                export_image = cv.circle(export_image, point, 3, 
                                         Colors.BLACK.value, 2)
                cv.putText(export_image, group[0], (point[0] + 4, point[1] - 4),
                           cv.FONT_HERSHEY_SIMPLEX, self.font_size, color, 
                           int(2*self.font_size))

        cv.imwrite(new_filename, export_image)

    def scale_contour(self, contour, scaling):
        """
        Scales contour to given scaling

        Arguments:
            contour (np.array): contour to scale
            scaling (float): scaling percent as decimal
        """
        M = cv.moments(contour)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])

        normalized = contour - [cx, cy]
        scaled = contour * scaling
        return scaled.astype(np.int32)

    def get_state(self):
        """
        Returns the current state as the current contours, lines, and counters
        as dictionary. For use with undo/redo.
        """
        cur_state = {}
        cur_state['contours'] = {}
        for group in self.saved_contours:
            cur_state['contours'][group] = self.saved_contours[group].copy()
        cur_state['lines'] = self.lines.copy()
        cur_state['counters'] = self.counters.copy()
        return cur_state

    def load_state(self, state):
        """Loads in contours, lines and counters from state (dict)."""
        self.saved_contours = state['contours']
        self.lines = state['lines']
        self.counters = state['counters']

    def save(self, filename, base_info):
        """
        Writes all of the current program data to filename (str) as literal
        dictionary, starting with base_info (dict).
        """
        export_data = base_info
        export_data['version'] = __version__
        export_data['contours'] = self.saved_contours
        export_data['threshold'] = self.threshold
        export_data['blur'] = self.blur
        export_data['min_size'] = self.min_size
        export_data['max_size'] = self.max_size
        export_data['alpha'] = self.alpha
        export_data['calibration'] = self.calibration
        export_data['quality'] = self.quality
        export_data['line_thickness'] = self.line_thickness
        export_data['outline_thickness'] = self.outline_thickness
        export_data['font_size'] = self.font_size
        export_data['eraser_size'] = self.eraser_size
        export_data['lines'] = self.lines
        export_data['counters'] = self.counters
        export_data['filename'] = self.filename
        with open(filename, 'w') as f:
            f.write(str(export_data))

    def open(self, import_data):
        if 'contours' in import_data:
            self.saved_contours = import_data['contours']
            if 'Axon' in self.saved_contours:
                mode_string = self.mode_to_string(ToolMode.SEL_AXON)
                axon = self.saved_contours.pop('Axon')
                self.saved_contours[mode_string] = axon
            if 'Myelin_In' in self.saved_contours:
                mode_string = self.mode_to_string(ToolMode.SEL_MYELIN_IN)
                inner = self.saved_contours.pop('Myelin_In')
                self.saved_contours[mode_string] = inner
            if 'Myelin_Out' in self.saved_contours:
                mode_string = self.mode_to_string(ToolMode.SEL_MYELIN_OUT)
                outer = self.saved_contours.pop('Myelin_Out')
                self.saved_contours[mode_string] = outer
        if 'threshold' in import_data:
            self.threshold = import_data['threshold'] 
        if 'blur' in import_data:
            self.blur = import_data['blur'] 
        if 'min_size' in import_data:
            self.min_size = import_data['min_size'] 
        if 'max_size' in import_data:
            self.max_size = import_data['max_size'] 
        if 'alpha' in import_data:
            self.alpha = import_data['alpha'] 
        if 'calibration' in import_data:
            self.calibration = import_data['calibration'] 
        if 'quality' in import_data:
            self.quality = import_data['quality'] 
        if 'outline_thickness' in import_data:
            self.outline_thickness = import_data['outline_thickness'] 
        if 'font_size' in import_data:
            self.font_size = import_data['font_size'] 
        if 'line_thickness' in import_data:
            self.line_thickness = import_data['line_thickness'] 
        if 'eraser_size' in import_data:
            self.eraser_size = import_data['eraser_size']
        if 'lines' in import_data:
            self.lines = import_data['lines']
        else:
            self.lines = []
        if 'counters' in import_data:
            self.counters = import_data['counters']
        else:
            self.counters = []

        self.check_undo_status()
        self.force_redraw = True
        self.redraw_contours = True
        self.show()
        return import_data

if __name__ == "__main__":
    appctxt = ApplicationContext()

    with np.printoptions(threshold=np.inf): # for storing giant strings
        app = QApplication([])
        win = MainWindow()
        exit_code = appctxt.app.exec_()
        sys.exit(exit_code)