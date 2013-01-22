# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import Interface

from zope.i18nmessageid import MessageFactory
from hejasverige.megabank import _


class IMyAccountFolder(Interface):

    """ marker interface for the registration folder """


class IMegabankSettings(Interface):

    """Global Megabank settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    megabank_url = schema.TextLine(title=_(u'Megabank url'),
                                   description=_(u'help_megabank_url',
                                   default=u'Your Megabank url  for reading Megabank API.'
                                   ), required=False, default=u'')

    megabank_user = schema.TextLine(title=_(u'Megabank user name'),
                                    description=_(u'help_megabank_user',
                                    default=u'Your Megabank username for reading Megabank API.'
                                    ), required=False, default=u'')

    megabank_password = schema.TextLine(title=_(u'Megabank password'),
            description=_(u'help_megabank_password',
            default=u'Your Megabank password for reading Megabank API.'
            ), required=False, default=u'')
