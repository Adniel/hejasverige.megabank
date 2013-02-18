# -*- coding: utf-8 -*-

from plone import api
import logging
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from hejasverige.megabank.bank import Bank
from five import grok
from zope.interface import Interface
from hejasverige.megabank.settings import Settings
import urllib

# Viewlets are on all content by default.
grok.context(Interface)
grok.templatedir("templates")


class MainViewletManager(grok.ViewletManager):
    """ This viewlet manager is responsible for all hejasverige.megabank viewlet registrations.
        Viewlets are directly referred in templates dir by viewlet name.
    """
    grok.name('hejasverige.megabank.viewletmanager')

# Set viewlet manager default to all following viewlets
grok.viewletmanager(MainViewletManager)

class ExtraViewletManager(grok.ViewletManager):
    """ This viewlet manager is responsible for all hejasverige.megabank viewlet registrations.
        Viewlets are directly referred in templates dir by viewlet name.
    """
    grok.name('hejasverige.megabank.extraviewletmanager')


class TransactionsViewlet(grok.Viewlet):
    """ Create a viewlet for transactions

    """
    grok.name('transactionsviewlet')

    def prepareUrl(self, url):
        return urllib.quote(url)


    def get_url(self):
        context = self.context.aq_inner
        #import pdb ; pdb.set_trace()
        return self.prepareUrl(context.absolute_url())


    def update(self):
        logger = logging.getLogger("transactionsviewlet")

        s = Settings()
        settings = s.getSettings()

        user = api.user.get_current()
        pid = user.getProperty('personal_id')

        # if field is not defined as a personal property it becomes an object and the bank fails to load
        if type(pid).__name__=='object':
            pid = None

        self.hasTransactions = False
        self.hasAccount = False
        self.hasConnectionError = False

        if pid:
            logger.info('List transactions for ' + str(user))

            # verify that the megabank settings are made before requesting...
            # Create new bank
            try:
                logger.info('Creating Bank')
                bank = Bank(settings=settings)
            except:
                logger.exception('Unable to create the Bank...')

            if bank:
                try:
                    self.transactions = bank.getTransactions(personalid=pid)
                    if self.transactions:
                        self.hasTransactions = True
                except ConnectionError:
                    self.hasConnectionError = True
                    logger.info("Connection Error")
                except Timeout:
                    self.hasConnectionError = True
                    logger.info("Timeout")

        else:
            self.hasTransactions = False
            logger.info("User %s has no personal_id", str(user))

class InvoicesViewlet(grok.Viewlet):
    """ Create a viewlet for invoices

    """
    grok.name('invoicesviewlet')
    grok.template('invoicesviewlet')
    grok.viewletmanager(ExtraViewletManager)

    def update(self):
        logger = logging.getLogger("invoicesviewlet")

        logger.debug("Running update for invoices viewlet")
        s = Settings()
        settings = s.getSettings()

        user = api.user.get_current()
        pid = user.getProperty('personal_id')

        self.hasInvoices = False
        self.hasAccount = False
        self.hasConnectionError = False


        if pid:
            logger.info('List invoices for ' + str(user))

            # verify that the megabank settings are made before requesting...
            # Create new bank
            try:
                logger.info('Creating Bank')
                bank = Bank(settings=settings)
            except:
                logger.exception('Unable to create the Bank...')

            if bank:
                try:
                    self.invoices = bank.getInvoices(personalid=pid)
                    if self.invoices:
                        self.hasInvoices = True
                except ConnectionError:
                    self.hasConnectionError = True
                    logger.info("Connection Error")
                except Timeout:
                    self.hasConnectionError = True
                    logger.info("Timeout")

        else:
            self.hasInvoices = False
            logger.info("User %s has no personal_id", str(user))



