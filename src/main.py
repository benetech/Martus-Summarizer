# $Id: main.py 3550 2012-07-12 02:42:29Z jeffk $
#
# Authors:     Jeff Klingner
# Maintainers: Jeff Klingner
# Copyright:   2011, Benetech, GPL v2 or later
# ============================================

# This is a GUI for the flattener/summarizer packaged
# for use by our partners.

import wx
import logging
import traceback
import threading

# Local import of icon (in python source format for easy packaging)
import martus_icon

# Single point of import for the main functionality of the tool.
from flattener_and_summarizer_wrapper import go, UserCorrectableError

VERSION = "1.1.1"


myEVT_LOG_MESSAGE = wx.NewEventType()
EVT_LOG_MESSAGE = wx.PyEventBinder(myEVT_LOG_MESSAGE, 1)
class LogMessageEvent(wx.PyCommandEvent):
    """Event to signal a log message (progress message) in a thread safe way."""
    def __init__(self, etype, eid, message=None):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._message = message
    
    def GetMessage(self):
        return self._message


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        
        self.main_panel = wx.Panel(parent=self)
        
        # Warning
        unencrypted_warning = wx.StaticText(parent=self.main_panel, label="Please be aware that any Martus bulletin data will appear in the Summarizer output files without any encryption.", style=wx.ALIGN_LEFT)
        unencrypted_warning.Wrap(400)
        
        # High-level Layout of the window.
        output_sizer = wx.StaticBoxSizer(box=wx.StaticBox(parent=self.main_panel, label="Output"), orient=wx.HORIZONTAL)        
        input_sizer  = wx.StaticBoxSizer(box=wx.StaticBox(parent=self.main_panel, label="Input"), orient=wx.HORIZONTAL)
        button_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        main_sizer = wx.BoxSizer(orient=wx.VERTICAL)
        main_sizer.Add((1,10))
        main_sizer.Add(unencrypted_warning, proportion=0, flag=wx.EXPAND|wx.LEFT|wx.ALIGN_CENTER, border=25)
        main_sizer.Add(input_sizer,  proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        main_sizer.Add(output_sizer, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        main_sizer.Add(button_sizer, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        self.main_panel.SetSizer(main_sizer)


        # Input section
        input_label = wx.StaticText(parent=self.main_panel, label="Martus Data Input (XML)", style=wx.ALIGN_RIGHT)
        self.input_picker = wx.FilePickerCtrl(parent=self.main_panel,
                                              message="Select an XML file exported by Martus.", 
                                              wildcard="XML files (*.xml;*.XML)|*.xml;*.XML",
                                              style=wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST)
        self.input_picker.SetTextCtrlProportion(3)
        
        # Output section
        html_output_label = wx.StaticText(parent=self.main_panel, label="HTML Summary Output Directory",
                                     style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.html_output_picker = wx.DirPickerCtrl(parent=self.main_panel, style=wx.DIRP_USE_TEXTCTRL)
        self.html_output_picker.SetTextCtrlProportion(3)

        
        # How many example rows to include in summary
        num_example_row_label = wx.StaticText(parent=self.main_panel, label="Number of example values from individual bulletins to include", style=wx.ALIGN_RIGHT)
        self.show_all_radio = wx.RadioButton(parent=self.main_panel, label="values from all bulletins.", style=wx.RB_GROUP)
        self.show_limited_radio = wx.RadioButton(parent=self.main_panel, label="values from up to")
        self.show_limited_radio.SetValue(True)
        show_limited_trailer_label = wx.StaticText(parent=self.main_panel, label="bulletins (recommended).")
        self.num_example_row_spinner = wx.SpinCtrl(parent=self.main_panel, min=0, max=100, initial=10)
        self.num_example_row_spinner.SetValue(10)  # Needed to force initial draw on Mac.
        num_values_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        num_values_sizer.Add(self.show_limited_radio, flag=wx.ALIGN_CENTER_VERTICAL)
        num_values_sizer.Add(self.num_example_row_spinner, flag=wx.ALIGN_CENTER_VERTICAL)
        num_values_sizer.Add(show_limited_trailer_label, flag=wx.ALIGN_CENTER_VERTICAL)
        
        # Whether to also output CSV data
        self.csv_output_checkbox = wx.CheckBox(parent=self.main_panel, label="Also output data as CSV")
        self.csv_output_label = wx.StaticText(parent=self.main_panel, label="CSV Output Directory",
                                         style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.csv_output_picker = wx.DirPickerCtrl(parent=self.main_panel, style=wx.DIRP_USE_TEXTCTRL)
        self.csv_output_picker.SetTextCtrlProportion(2)

        # Main Go and Exit Buttons
        go_button = wx.Button(parent=self.main_panel, label="Summarize Data")
        exit_button = wx.Button(parent=self.main_panel, label="Exit")
        
        # Event bindings
        self.Bind(wx.EVT_BUTTON, self.go_button_clicked, go_button)
        self.Bind(wx.EVT_BUTTON, self.exit_button_clicked, exit_button)
        self.Bind(wx.EVT_CHECKBOX, self.csv_checkbox_flipped, self.csv_output_checkbox)
        self.Bind(wx.EVT_RADIOBUTTON, self.num_values_radio_flipped, self.show_limited_radio)
        self.Bind(wx.EVT_RADIOBUTTON, self.num_values_radio_flipped, self.show_all_radio    )
        # Call ot initialize checkbox-dependent fields to disabled state
        self.csv_output_checkbox.SetValue(False)
        self.csv_checkbox_flipped(None)
    

        # Detailed layout of GUI

        input_sizer.Add(input_label, 0, wx.ALIGN_CENTER_VERTICAL)
        input_sizer.Add(self.input_picker, 0, wx.EXPAND)
        
        picker_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        picker_sizer.AddGrowableCol(2, proportion=1)
        # pos is (row, col), zero indexed from top left    span is (rowspan, colspan)
        picker_sizer.Add(html_output_label, pos=(0,0), span=(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        picker_sizer.Add(self.html_output_picker, pos=(0,2))
        picker_sizer.Add((1,10), pos=(1,0), span=(1,3))
        picker_sizer.Add(num_example_row_label, pos=(2,0), span=(1,3), flag=wx.ALIGN_CENTER_VERTICAL)
        picker_sizer.Add((30,1), pos=(3,0))
        picker_sizer.Add(num_values_sizer, pos=(3,1), span=(1,2))
        picker_sizer.Add((30,1), pos=(4,0))
        picker_sizer.Add(self.show_all_radio, pos=(4,1), span=(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        picker_sizer.Add((1,10), pos=(5,0), span=(1,3))
        picker_sizer.Add(self.csv_output_checkbox, pos=(6,0), span=(1,3))
        picker_sizer.Add((30,1), pos=(7,0))
        picker_sizer.Add(self.csv_output_label, pos=(7,1), flag=wx.ALIGN_CENTER_VERTICAL)
        picker_sizer.Add(self.csv_output_picker, pos=(7,2))
        output_sizer.Add(picker_sizer)

        button_sizer.Add((20,1), proportion=4)
        button_sizer.Add(go_button, flag=wx.ALIGN_LEFT)
        button_sizer.Add((20,1), proportion=1)
        button_sizer.Add(exit_button, flag=wx.ALIGN_RIGHT)
        button_sizer.Add((20,1), proportion=4)        

        main_sizer.Fit(self)

        self.SetIcon(martus_icon.martus.getIcon())
        self.SetSize((500,-1))
        self.CenterOnScreen()


    def csv_checkbox_flipped(self, event):
        self.csv_output_label.Enable(self.csv_output_checkbox.IsChecked())
        self.csv_output_picker.Enable(self.csv_output_checkbox.IsChecked())


    def num_values_radio_flipped(self, event):
        self.num_example_row_spinner.Enable(self.show_limited_radio.GetValue())
        
    def exit_button_clicked(self, event):
        self.Destroy()

        
    def go_button_clicked(self, event):
        """ Fire off the main event."""

        self.progress_dialog = wx.ProgressDialog(
            title="Running Martus Data Summarizer",
            message="Starting data summarizer....",
            maximum = 100,
            parent=self,
            style = wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_AUTO_HIDE
        )
        self.progress_dialog.SetIcon(martus_icon.martus.getIcon())
        self.progress_dialog.SetSize((700,-1))
        self.progress_dialog.CenterOnScreen()

        self.warnings_and_errors = list()

        class EchoLogToProgressDialog(logging.Handler):
            def __init__(self, target):
                logging.Handler.__init__(self)
                self.target = target
            def emit(self, log_record):
                # This gets called from the worker thread, so it can't
                # access the progress dialog directly.  Instead, it
                # posts an event that will be recieved by the main
                # thread to do the update.
                log_event = LogMessageEvent(myEVT_LOG_MESSAGE, -1, log_record.message)
                wx.PostEvent(self.target, log_event)

                # Save warnings and erros for display at the end or
                # in case of a crash
                if log_record.levelno >= logging.WARNING:
                    self.target.warnings_and_errors.append(log_record)

        handler = EchoLogToProgressDialog(target=self)
        logging.getLogger().addHandler(handler)
        self.Bind(EVT_LOG_MESSAGE, self.update_progress_bar)

        # A little timer to keep the progress gauge flowing even
        # when the flattener is slow
        class GaugePokingTimer(wx.Timer):
            def __init__(self, target):
                wx.Timer.__init__(self, owner=target)
                self.target = target
            def Notify(self):
                # Called from UI thread, so this is thread safe
                self.target.progress_dialog.Pulse()
        self.timer = GaugePokingTimer(target=self)
        self.timer.Start(milliseconds=100, oneShot=False)

        # Start off the main worker thread, then return control to the UI loop
        main_worker_thread = MainWorker(owner=self)
        main_worker_thread.start()

    
    def update_progress_bar(self, event):
        message = event.GetMessage()
        if message:
            self.progress_dialog.Pulse(newmsg=message)
        else:
            self.progress_dialog.Pulse()


    def OnError(self, error_message, include_log_details=False):
        if include_log_details:
            # Full details to aid diagnosis.  Meant for copy-pasting in an email to us.
            dialog_text = 'An error has occurred during summarization.\n' + \
                          'Details:\n' + \
                          'Martus Data Summarizer v' + VERSION + '\n\n'
                          
            for log_message in self.warnings_and_errors:
                dialog_text += (log_message.levelname + ": " + log_message.getMessage() + '\n')

            dialog_text += '\n\n'
            dialog_text += error_message
        else:
            # Simple errors that are correctable by users (e.g. input file is not XML)
            dialog_text = error_message

        error_dialog = wx.MessageDialog(
            parent=self,
            message=dialog_text,
            caption='Error',
            style=wx.OK | wx.ICON_ERROR
        )
        error_dialog.SetIcon(martus_icon.martus.getIcon())
        error_dialog.ShowModal()
        error_dialog.Destroy()


    def OnCompletion(self):
        dialog_message = 'Data Summarization Complete.'
        # for log_message in self.warnings_and_errors:
            # dialog_text += (log_message.levelname + ": " + log_message.getMessage() + '\n')

        finished_dialog = wx.MessageDialog(
            parent=self,
            message=dialog_message,
            caption='Done',
            style=wx.OK
        )
        finished_dialog.SetIcon(martus_icon.martus.getIcon())
        finished_dialog.ShowModal()
        finished_dialog.Destroy()

    def cleanup(self):
        self.timer.Stop()
        self.progress_dialog.Destroy()
        self.warnings_and_errors = list()


class MainWorker(threading.Thread):
    def __init__(self, owner):
        threading.Thread.__init__(self)
        self.owner = owner
        self.daemon = True # In case of a hang, so main process can exit

    def run(self):
        try:
            if self.owner.show_limited_radio.GetValue():
                num_values = self.owner.num_example_row_spinner.GetValue()
            else:
                num_values = None  # signal to show all values

            go(input_xml_filename=self.owner.input_picker.GetPath(),
               output_html_directory=self.owner.html_output_picker.GetPath(),
               include_csv_output=self.owner.csv_output_checkbox.IsChecked(),
               output_csv_directory=self.owner.csv_output_picker.GetPath(),
               num_example_values=num_values)
        except UserCorrectableError as uce:
            self.owner.OnError(uce.descrip, include_log_details=False)
        except:
            error_message = traceback.format_exc(limit=4)
            self.owner.OnError(error_message, include_log_details=True)
        else:
            self.owner.OnCompletion()
        finally:
            self.owner.cleanup()


if __name__ == '__main__':
    # app = wx.App(redirect=False) # redirect=False causes stderr and stdout to be readable
    app = wx.App(redirect=False) # redirect=False causes stderr and stdout to be readable
    frame = MainFrame(parent=None, title='Martus Data Summarizer v' + VERSION)
    frame.Center()
    frame.Show()
    app.MainLoop()
