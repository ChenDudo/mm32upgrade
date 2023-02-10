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
import shutil
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
    result = p.stdout.read().decode('gbk') #utf-8   'gb18030'
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
    disks = scanUSBDevice()
    usbMSC.clear()
    LINK_MINI.clear()
    LINK_MAX.clear()
    BootLoader.clear()
    for disk in disks:
        if ('Removable' in disk) or ('可移动磁盘' in disk):
            linkIFString = re.search(r'\w:\s+MM32-LINK\s?\w', disk)
            if linkIFString:
                string = linkIFString.group()
                if (string[:-1] == 'I'):
                    LINK_MINI.append(string)
                    print('MINI found')
                elif (string[:-1] == 'A'):
                    LINK_MAX.append(string)
                    print('Max found')
                usbMSC.append(string)
            linkBTString = re.search(r'\w:\s+BOOTLOADER', disk)
            if linkBTString:
                print("boot found")
                BootLoader.append(linkBTString.group())
                usbMSC.append(linkBTString.group())



class mainwindow(QMainWindow):
    def __init__(self):
        super(mainwindow, self).__init__()
        uic.loadUi(get_path()+"\\mm32upgrade.ui", self)
        self.show()
        self.initWindow()
        self.linker = mm32link.mm32link()
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
        analyseUSB()
        self.scanNum = len(usbMSC)
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
        if (self.cbbDevice.count() >= 1) and (self.linker.getVersion() == ''):
            self.parseLinktext(self.cbbDevice.currentIndex())
            

    def parseLinktext(self, index):
        volumeDir = usbMSC[index][:2]
        self.linker.setVolume(volumeDir)
        try:
            with open(volumeDir+'/details.txt', 'r') as f:
                details = f.read()
                # Interface Version: 220729
                # versionString = details.match(r'Interface Version: (\d+)') 
                version= re.search(r'Interface Version: (\d+)', details).group().split(':')
                self.linker.setVersion(version[1].strip())
                # Unique ID: 08811f11f1c004c75fd
                uid = re.search(r'Unique ID: [a-zA-Z0-9]+', details).group().split(':')
                self.linker.setUID(uid[1].strip())
                if (self.linker.getUID()[:3] == '088'):
                    self.linker.setType("MM32LINK-MINI")
                elif (self.linker.getUID()[:3] == '059'):
                    self.linker.setType("MM32LINK-MAX")
                else:
                    self.linker.setType("MM32LINK-OB")
                # Target Power output: OFF
                powerString = re.search(r'Target Power output: [a-zA-Z0-9\.]+', details).group().split(':')
                # if (powerString[1].strip() == '5V'):
                #     self.linker.setOriPower(1)
                # elif (powerString[1].strip() == '3.3V'):
                #     self.linker.setOriPower(2)
                # else:
                #     self.linker.setOriPower(0)
                self.linker.setOriPower(powerString[1].strip())
                # Beep Mode: ON
                beepString = re.search(r'Beep Mode: [a-zA-Z]+', details).group().split(':')
                # if (beepString[1].strip() == 'ON'):
                #     self.linker.setOriBeep(1)
                # else:
                #     self.linker.setOriBeep(0)
                self.linker.setOriBeep(beepString[1].strip())
                f.close()
                print("open OK")
        except Exception as e:
            print("error")
            pass
        self.log('Select Device details:\n- Type :\t'+self.linker.getType()+\
            '\n- Rev. :\t'+self.linker.getVersion()+'\n- UUID :\t'+\
            self.linker.getUID()+'\n- Dir  : \t'+self.linker.getVolume()+\
            '\n- Beep :\t'+self.linker.getOriBeep()+'\n- Power:\t'+\
            self.linker.getOriPower())


    def linkerConfig(self):
        fileNeed = []
        if (self.linker.getBeep() == self.linker.getOriBeep()):
            pass
        elif (self.linker.getBeep() == 'OFF'):
            fileNeed.append('BEEP_OFF.cfg')
        else:
            fileNeed.append('BEEP_ON.cfg')

        if (self.linker.getPower() == self.linker.getOriPower()):
            pass
        elif (self.linker.getPower() == '5V'):
            fileNeed.append('VT_5V.cfg')
        elif (self.linker.getPower() == 'OFF'):
            fileNeed.append('VT_OFF.cfg')
        else:
            fileNeed.append('VT_3V3.cfg')

        # srcFile = get_path()+'\\config\\'+fileNeed[0]
        # dirFile = self.linker.getVolume()
        # shutil.copy(srcFile, dirFile)
        shutil.copytree(get_path()+'//config//', self.linker.getVolume()+'//')

    @pyqtSlot()  
    def on_cbbDevice_Activated(self):
        print("on_cbbDevice_Activated")


    @pyqtSlot()
    def on_btnUpgrade_clicked(self):
        self.processBar.setVisible(True)
        print("on_btnUpgrade_clicked")
        pass

    @pyqtSlot()
    def on_btnRefresh_clicked(self):
        # self.log("Scan USB device ...")
        self.linker.__init__()
        analyseUSB()
        self.scanNum = len(usbMSC)
        self.log("Found Device Total: "+str(self.scanNum))
        # self.processBar.setValue(5)
        pass

    @pyqtSlot()
    def on_btnOK_clicked(self):
        self.processBar.setVisible(True)
        self.linkerConfig()
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
        if self.cboxBeep.isChecked():
            self.linker.setBeep('ON')
        else:
            self.linker.setBeep('OFF')
        print('Beep:'+str(self.linker.getBeep()))
        pass

    @pyqtSlot()
    def on_cboxPower_clicked(self):
        if self.cboxPower.isChecked():
            self.cbbPOut.setEnabled(True)
            self.cbbPOut.setCurrentIndex(1)
            self.linker.setPower('5V')
        else:
            self.cbbPOut.setEnabled(False)
            self.linker.setPower('OFF')
        print('Power:'+str(self.linker.getPower()))
        pass

    @pyqtSlot()
    def on_cbbPOut_currentIndexChanged(self):
        if (self.cbbPOut.getCurrentIndex == 0):
            self.linker.setPower('3.3V')
        elif (self.cbbPOut.getCurrentIndex == 1):
            self.linker.setPower('5V')
        print('on_cbbPOut_currentIndexChanged Power'+str(self.linker.getPower()))

    @pyqtSlot()
    def on_cbbPOut_activated(self):
        if (self.cbbPOut.getCurrentIndex == 0):
            self.linker.setPower(2)
        elif (self.cbbPOut.getCurrentIndex == 1):
            self.linker.setPower(1)
        print('on_cbbPOut_currentIndexChanged Power'+str(self.linker.getPower()))

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
