# -*- coding: utf-8 -*-

# (c) 2017
# This is an example plugin


import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import ecu
import options
import elm

plugin_name = "Clio III / Megane II ph 2 Mileage correction"
category = "Cluster Tools"
need_hw = True
ecu_file = "UCH_84_J84_03_60"

class Virginizer(gui.QDialog):
    def __init__(self):
        super(Virginizer, self).__init__()
        self.megane_uch = ecu.Ecu_file(ecu_file, True)
        layout = gui.QVBoxLayout()
        infos = gui.QLabel("MEGANE II ph2 / Clio III Cluster mileage correction")
        infos.setAlignment(core.Qt.AlignHCenter)
        check_button = gui.QPushButton("Check UCH Virgin")
        self.status_check = gui.QLabel("Waiting")
        self.status_check.setAlignment(core.Qt.AlignHCenter)
        self.virginize_button = gui.QPushButton("Virginize UCH")
        layout.addWidget(infos)
        layout.addWidget(check_button)
        layout.addWidget(self.status_check)
        layout.addWidget(self.virginize_button)
        self.setLayout(layout)
        self.virginize_button.setEnabled(False)
        self.virginize_button.clicked.connect(self.reset_ecu)
        check_button.clicked.connect(self.check_virgin_status)
        self.ecu_connect()

    def ecu_connect(self):
        connection = self.megane_uch.connect_to_hardware()
        if not connection:
            options.main_window.logview.append("Cannot connect to ECU")
            self.finished()

    def check_virgin_status(self):
        virgin_data_name = u"VSC UCH vierge (NbBadgeAppris=0)"
        virigin_check_request = self.megane_uch.requests[u'Status général des opérations badges Bits']
        virgin_data_bit = virigin_check_request.dataitems[virgin_data_name]
        virgin_ecu_data = self.megane_uch.data[virgin_data_name]

        request_stream = virigin_check_request.build_data_stream({})
        request_stream = " ".join(request_stream)

        self.start_diag_session_aftersales()
        if options.simulation_mode:
            # Simulate coded ECU
            elmstream = "61 06 00 00 00 00 00 00 00 00 00 00 00 00 00"
            print "Send request stream", request_stream
        else:
            elmstream = options.elm.request(request_stream)

        if elmstream == "WRONG RESPONSE":
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='red'>Communication problem</font>")
            return

        virgin = virgin_ecu_data.getIntValue(elmstream, virgin_data_bit, self.megane_uch.endianness) == 1

        if virgin:
            self.virginize_button.setEnabled(False)
            self.status_check.setText("<font color='green'>UCH virgin</font>")
            return
        else:
            self.virginize_button.setEnabled(True)
            self.status_check.setText("<font color='red'>UCH coded</font>")
            return

    def start_diag_session_study(self):
        sds_request = self.megane_uch.requests[u"StartDiagSession Etude"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdSA stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def start_diag_session_aftersales(self):
        sds_request = self.megane_uch.requests[u"Start Diagnostic Session"]
        sds_stream = " ".join(sds_request.build_data_stream({}))
        if options.simulation_mode:
            print "SdSS stream", sds_stream
            return
        options.elm.start_session_can(sds_stream)

    def reset_ecu(self):
        reset_request = self.megane_uch.requests[u"RAZ EEPROM"]
        reset_stream = " ".join(reset_request.build_data_stream({}))
        self.start_diag_session_study()
        if options.simulation_mode:
            print "Reset stream", reset_stream
            return
        # Reset can only be done in study diag session
        options.elm.request(reset_stream)


def plugin_entry():
    v = Virginizer()
    v.exec_()
