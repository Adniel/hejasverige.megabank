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

        # if timeout is missing, set a default timeout
        #try:
        #    settings.megabank_timeout = float(settings.megabank_timeout)
        #except:
        #    settings.megabank_timeout = "5.000"

        return settings
