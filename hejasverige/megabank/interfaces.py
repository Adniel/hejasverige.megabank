# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import Interface

from hejasverige.megabank import _


class IMyAccountFolder(Interface):

    """ marker interface for the registration folder """

class IMyCards(Interface):

    """ marker interface for the my cards portlet """


class IMegabankSettings(Interface):

    """Global Megabank settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    megabank_url = schema.TextLine(title=_(u'API Url'),
                                   description=_(u'help_megabank_url',
                                   default=u'Your Megabank url for reading Megabank API.'
                                   ), required=False, default=u'')

    megabank_onlinepayment_url = schema.TextLine(title=_(u'Online Payment Url'),
                                   description=_(u'help_megabank_onlinepayment_url',
                                   default=u'Your Megabank url for getting the online payment form.'
                                   ), required=False, default=u'')

    megabank_user = schema.TextLine(title=_(u'User name'),
                                    description=_(u'help_megabank_user',
                                    default=u'Your Megabank username for reading Megabank API.'
                                    ), required=False, default=u'')

    megabank_password = schema.TextLine(title=_(u'Password'),
                                        description=_(u'help_megabank_password',
                                        default=u'Your Megabank password for reading Megabank API.'
                                        ), required=False, default=u'')

    # TODO: Add validator (float)
    megabank_timeout = schema.TextLine(title=_(u'Timeout'),
                                       description=_(u'help_megabank_timeout',
                                       default=u'The timeout before stop try reading Megabank API.'
                                       ), required=False, default=u'5.000')
