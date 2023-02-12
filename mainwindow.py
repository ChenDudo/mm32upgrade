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
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, QBasicTimer


def get_path():
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def sh(command, print_msg=True):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('gbk') #utf-8
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

usbMSC      = []
LINK_MINI   = []
LINK_MAX    = []
BootLoader  = []

class mainwindow(QMainWindow):
    def __init__(self):
        super(mainwindow, self).__init__()
        uic.loadUi(get_path()+"\\mm32upgrade.ui", self)
        self.show()
        self.detectOnceEnable = False
        self.detectTwiceEnable = False
        self.linker = mm32link.mm32link()
        self.lastMscMum = 0
        self.CntForProcess = 0
        self.upgradeAction = False
        self.initWindow()
        self.analyseUSB()
        self.scanNum = len(usbMSC)
        self.log("Found Device Total: "+str(self.scanNum))
        self.scanDevice = QtCore.QTimer()
        self.scanDevice.setInterval(500)
        self.scanDevice.timeout.connect(self.scanDevice_timeout)
        self.scanDevice.start()
        self.timer1 = QBasicTimer()
    
    def initWindow(self):
        self.processBar.setRange(0,99)
        self.cbbPOut.setCurrentIndex(1)
        self.cbbPOut.setEnabled(False)
        self.btnUpgrade.setEnabled(False)
        self.textView.setText("- "*3+time.asctime()+" -"*3)
        self.textView.ensureCursorVisible()

    def log(self, text):
        self.textView.clear()
        self.textView.setText("["+time.asctime()+"]\n")
        self.textView.append(text)
        self.textView.ensureCursorVisible()
    
    def myTimerState(self, flag):
        if flag:
            self.CntForProcess = 0
            self.timer1.start(100, self)
        else:
            self.timer1.stop()
            # self.timer1.isActive()
    
    def timerEvent(self, e):
        if self.CntForProcess >= 90:
            self.analyseUSB()
            self.timer1.stop()
            
            if len(usbMSC) == self.lastMscMum:
                print("MSC Reload OK ...")
                self.processBar.setValue(99)
                for i in range(len(usbMSC)):
                    if usbMSC[i][:2] == self.linker.getVolume():
                        index = i
                        self.parseLinktext(index)
                        self.timerEvent(False)
        else:
            self.CntForProcess += 1
            self.processBar.setValue(self.CntForProcess)
            print("cnt +++++++++++++++++++")

    def scanDevice_timeout(self):
        if not self.isEnabled():
            return
        if (self.cbbDevice.count() >= 1) and (self.linker.getVersion() == ''):
            self.parseLinktext(self.cbbDevice.currentIndex())
        if self.detectOnceEnable:
            self.analyseUSB()
            if len(usbMSC) == self.lastMscMum:
                # self.log("MSC Reload OK ...")
                self.timerEvent(False)
                self.processBar.setValue(99)
                for i in range(len(usbMSC)):
                    if usbMSC[i][:2] == self.linker.getVolume():
                        index = i
                        self.parseLinktext(index)
                        self.detectOnceEnable = False
        else:
            if len(usbMSC) != self.cbbDevice.count():
                self.cbbDevice.clear()
                for item in usbMSC:
                    showString = item
                    indexstring = showString.replace(' ','')
                    self.cbbDevice.addItem(indexstring)

    def parseLinktext(self, index):
        volumeDir = usbMSC[index][:2]
        self.linker.setVolume(volumeDir)
        try:
            with open(volumeDir+'/details.txt', 'r') as f:
                details = f.read()
                # Interface Version: 220729
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
                self.linker.setOriPower(powerString[1].strip())
                # Beep Mode: ON
                beepString = re.search(r'Beep Mode: [a-zA-Z]+', details).group().split(':')
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
        self.updateVersion()

    def updateVersion(self):
        self.cbbVersion.clear()
        if (self.linker.getType() == 'MM32LINK-MINI'):
            versionstring = ['220520', '220729', '221130']
        elif (self.linker.getType() == 'MM32LINK-MAX'):
            versionstring = ['220520']
        elif (self.linker.getType() == 'MM32LINK-OB'):
            versionstring = ['220729', '221130']
        selfVersion = self.linker.getVersion()
        self.cbbVersion.addItems(versionstring)
        self.cbbVersion.setCurrentText(selfVersion)
        self.btnUpgrade.setEnabled(True)
        

    def analyseUSB(self):
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

    def linkerConfig(self):
        fileNeed = []
        noNeed = 0
        if (self.linker.getBeep() == self.linker.getOriBeep()):
            noNeed = noNeed + 1
            pass
        elif (self.linker.getBeep() == 'OFF'):
            fileNeed.append('BEEP_OFF.cfg')
        else:
            fileNeed.append('BEEP_ON.cfg')
        
        if (self.linker.getPower() == self.linker.getOriPower()):
            noNeed = noNeed + 1
            pass
        elif (self.linker.getPower() == '5V'):
            fileNeed.append('VT_5V.cfg')
        elif (self.linker.getPower() == 'OFF'):
            fileNeed.append('VT_OFF.cfg')
        else:
            fileNeed.append('VT_3V3.cfg')

        if noNeed >= 2:
            self.log("NO change to config ...")
            self.myTimerState(False)
            self.processBar.reset()

        if len(fileNeed):
            tmpPath = get_path()+"\\config\\"
            if not os.path.exists(tmpPath):
                os.makedirs(tmpPath)
            else:
                shutil.rmtree(tmpPath)
                os.mkdir(tmpPath)
            for file in fileNeed:
                f = open(tmpPath+file, "a")
            try:
                for i in range(len(fileNeed)):
                    shutil.copy(tmpPath+fileNeed[i], self.linker.getVolume())
            except Exception as e:
                print("Files copy error")
                pass
            self.detectOnceEnable = True
            
    @pyqtSlot()  
    def on_cbbDevice_Activated(self):
        print("on_cbbDevice_Activated")


    @pyqtSlot()
    def on_btnUpgrade_clicked(self):
        self.processBar.reset()
        self.myTimerState(True)
        print("Now Update Version: "+self.cbbVersion.currentText())
        self.upgradeAction = True
        pass

    @pyqtSlot()
    def on_btnRefresh_clicked(self):
        self.processBar.reset()
        self.linker.__init__()
        self.analyseUSB()
        self.scanNum = len(usbMSC)
        self.log("Found Device Total: "+str(self.scanNum))
        pass

    @pyqtSlot()
    def on_btnOK_clicked(self):
        self.processBar.reset()
        self.myTimerState(True)
        self.lastMscMum = len(usbMSC)
        if self.cboxBeep.isChecked():
            self.linker.setBeep('ON')
        else:
            self.linker.setBeep('OFF')
        if self.cboxPower.isChecked():
            if (self.cbbPOut.currentIndex() == 0):
                self.linker.setPower('3.3V')
            elif (self.cbbPOut.currentIndex() == 1):
                self.linker.setPower('5V')
        else:
            self.linker.setPower('OFF')
        self.linkerConfig()
        pass

    @pyqtSlot()
    def on_btnClearLog_clicked(self):
        self.processBar.reset()
        pass

    @pyqtSlot()
    def on_cboxBeep_clicked(self):
        pass

    @pyqtSlot()
    def on_cboxPower_clicked(self):
        if self.cboxPower.isChecked():
            self.cbbPOut.setEnabled(True)
            self.cbbPOut.setCurrentIndex(1)
        else:
            self.cbbPOut.setEnabled(False)
        pass

    @pyqtSlot()
    def on_cbbVersion_clicked(self):
        # print("on_cbbVersion_clicked")
        pass

    @pyqtSlot()
    def on_cbbDevice_clicked(self):
        print("on_cbbDevice_clicked")
        pass

if __name__=="__main__":
    app=QApplication(sys.argv)
    window=mainwindow()
    sys.exit(app.exec_())
