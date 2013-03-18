# -*- coding: utf-8 -*-

from plone.registry.interfaces import IRegistry
from hejasverige.megabank.interfaces import IMegabankSettings
from zope.component import getUtility


class Settings:
    def getSettings(self):
        ''' Helper function to get the settings provided by megabank registry

        '''
        try:
            registry = getUtility(IRegistry)
        except:
            print 'Failed to get utility IRegistry'
            return

        settings = registry.forInterface(IMegabankSettings)

        return settings
