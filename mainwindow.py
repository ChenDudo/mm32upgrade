# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :   mainwindow.py
@Time    :   2023/02/10 12:22:42
@Author  :   Chen Do
@Version :   1.0
@Desc    :   None
"""

import os
import sys
import time
import subprocess
import re
import mm32link

from PyQt5.QtWidgets import QApplication,QMainWindow,QMessageBox,QFileDialog,QWidget
from PyQt5 import QtCore,uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread


def get_path():
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def sh(command, print_msg=True):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('gb18030') #utf-8
    if print_msg:
        print(result)
    return result

def scanUSBDevice():
    if os.name == 'nt':
        disks = sh("wmic logicaldisk get deviceid, description, VolumeName", print_msg=False).split('\n')
        return disks
    elif os.name == 'posix':
        return sh('ll -a /media')[-1].strip()
    else:
        return sh('ls /Volumes')[-1].strip()

usbMSC = []
LINK_MINI = []
LINK_MAX = []
BootLoader = []

def analyseUSB():
    num = 0
    disks = scanUSBDevice()
    for disk in disks:
        if 'Removable' in disk:
            linkIFString = re.search(r'\w:\s+MM32-LINK\s?\w', disk)
            if linkIFString:
                string = linkIFString.group()
                if (string[:-1] == 'I'):
                    LINK_MINI.append(string)
                    num += 1
                    print('MINI found')
                elif (string[:-1] == 'A'):
                    LINK_MAX.append(string)
                    num += 1
                    print('Max found')
                usbMSC.append(string)
            linkBTString = re.search(r'\w:\s+BOOTLOADER', disk)
            if linkBTString:
                print("boot found")
                BootLoader.append(linkBTString.group())
                usbMSC.append(linkBTString.group())
                num += 1
        else:
            print('No Udisk found')
    return num
        




class mainwindow(QMainWindow):
    def __init__(self):
        super(mainwindow, self).__init__()
        uic.loadUi(get_path()+"\\mm32upgrade.ui", self)
        self.show()
        self.initWindow()

        self.scanDevice = QtCore.QTimer()
        self.scanDevice.setInterval(2000)
        self.scanDevice.timeout.connect(self.scanDevice_timeout)
        self.scanDevice.start()
    
    def initWindow(self):
        self.cbbPOut.setCurrentIndex(1)
        self.cbbPOut.setEnabled(False)
        self.btnUpgrade.setEnabled(False)
        self.textView.setText("- "*3+time.asctime()+" -"*3)
        self.textView.ensureCursorVisible()
        self.processBar.setRange(0,99)
        # self.processBar.setVisible(False)
        self.scanNum = analyseUSB()
        self.log("Found Device Total: "+str(self.scanNum))

    def log(self, text):
        self.textView.append(text)
        self.textView.ensureCursorVisible()
        
    def scanDevice_timeout(self):
        if not self.isEnabled():    # link working
            return
        if len(usbMSC) != self.cbbDevice.count():
            self.cbbDevice.clear()
            for item in usbMSC:
                showString = item
                indexstring = showString.replace(' ','')
                self.cbbDevice.addItem(indexstring)
                # self.log("Scan: "+indexstring)
        

    @pyqtSlot()
    def on_btnUpgrade_clicked(self):
        self.processBar.setVisible(True)
        print("on_btnUpgrade_clicked")
        pass

    @pyqtSlot()
    def on_btnRefresh_clicked(self):
        # self.log("Scan USB device ...")
        self.scanNum = analyseUSB()
        self.log("Found Device Total: "+str(self.scanNum))
        # self.processBar.setValue(5)
        pass

    @pyqtSlot()
    def on_btnOK_clicked(self):
        self.processBar.setVisible(True)
        print("on_btnOK_clicked")
        pass

    @pyqtSlot()
    def on_btnCancel_clicked(self):
        self.processBar.reset()
        # self.processBar.setVisible(False)
        print("on_btnCancel_clicked")
        pass

    @pyqtSlot()
    def on_cboxBeep_clicked(self):
        print("on_cboxBeep_clicked")
        pass

    @pyqtSlot()
    def on_cboxPower_clicked(self):
        if self.cboxPower.isChecked():
            self.cbbPOut.setEnabled(True)
        else:
            self.cbbPOut.setEnabled(False)
        print("on_cboxPower_clicked")
        pass

    @pyqtSlot()
    def on_cbbPOut_currentIndexChanged(self):
        if (self.cbbPOut.getCurrentIndex == 0):
            self.cboxPower.setEnabled(false)

    @pyqtSlot()
    def on_cbbVersion_clicked(self):
        print("on_cbbVersion_clicked")
        pass

    @pyqtSlot()
    def on_cbbDevice_clicked(self):
        print("on_cbbDevice_clicked")
        pass

if __name__=="__main__":
    app=QApplication(sys.argv)
    window=mainwindow()
    sys.exit(app.exec_())
