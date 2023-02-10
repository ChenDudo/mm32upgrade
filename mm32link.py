# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :   mm32link.py
@Time    :   2023/02/10 15:33:30
@Author  :   Chen Do
@Version :   1.0
@Desc    :   None
"""
class mm32link():
    def __init__(self):
        self.volume = ''
        self.type = 'MM32LINK'
        self.uid = ''
        self.version = ''
        self.beep = ''
        self.power = ''
        self.oribeep = ''
        self.oripower = ''
    
    def setVolume(self, text):
        self.volume = text

    def getVolume(self):
        return self.volume

    def setType(self, text):
        self.type = text

    def getType(self):
        return self.type

    def setUID(self,text):
        self.uid = text
    
    def getUID(self):
        return self.uid

    def setBeep(self, value):
        self.beep = value

    def getBeep(self):
        return self.beep

    def setOriBeep(self, text):
        self.oribeep = text

    def getOriBeep(self):
        return self.oribeep

    def setPower(self, value):
        self.power = value
    
    def getPower(self):
        return self.power

    def setOriPower(self, value):
        self.oripower = value
    
    def getOriPower(self):
        return self.oripower

    def setVersion(self, text):
        self.version = text
    
    def getVersion(self):
        return self.version
