# -*- coding: utf-8 -*-

from plone import api
import logging
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from hejasverige.megabank.bank import Bank
from five import grok
from hejasverige.megabank.settings import Settings
from hejasverige.megabank.interfaces import IMyAccountFolder

grok.templatedir("templates")

class Transactions2(grok.View):
    """ List the transactions available for the current users
    """
    grok.context(IMyAccountFolder)
    grok.name('transactions')
    grok.require('zope2.View')
    grok.template("transactions")

    def update(self):
        logger = logging.getLogger("transactions.view")

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
