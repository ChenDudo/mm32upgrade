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
        self.mscName = 'MM32LINK'
        self.uid = ''
        self.version = ''
        self.beep = False
        self.power = 0
    
    def setMscName(self, text):
        self.mscName = text

    def getMscName(self):
        return self.mscName

    def setUID(self,text):
        self.uid = text
    
    def getUID(self):
        return self.uid

    def setBeep(self, value):
        self.beep = value

    def getBeep(self):
        return self.beep

    def setPower(self, value):
        self.power = value
    
    def getPower(self):
        return self.power

    def setVersion(self, text):
        self.version = text
    
    def getVersion(self):
        return self.version
