# -*- coding: utf-8 -*-

from five import grok
from plone import api
from DateTime import DateTime
import logging
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
from hejasverige.megabank.bank import Bank
from hejasverige.megabank.settings import Settings
from hejasverige.megabank.interfaces import IMyAccountFolder
import urllib
from plone.memoize.instance import memoize
from z3c.form import form, field
from zope import interface, schema

# Add interface hejasverige.megabank.interfaces.IMyAccountFolder to folder
# http://belomor.zapto.org:9091/Plone/mitt-konto/manage_interfaces
# Add "layout" as string with value @@list-transactions
# http://belomor.zapto.org:9091/Plone/mitt-konto/manage_propertiesForm

grok.templatedir("templates")


class INote(interface.Interface):
    text = schema.TextLine(title=u"Text",
                           required=False)


class CommentForm(form.Form):
    fields = field.Fields(INote)
    ignoreContext = True  # don't use context to get widget data
    label = "Add a note"


def get_pid():
    user = api.user.get_current()
    pid = user.getProperty('personal_id')

    # if field is not defined as a personal property it becomes an object and the bank fails to load
    if type(pid).__name__ == 'object':
        pid = None
    return pid


def get_now():
    return DateTime().strftime('%Y-%m-%d %H:%M:%S')


def get_bank(logger=None):

    try:
        if logger:
            logger.info('Creating Bank')
        bank = Bank()
    except:
        bank = None
        if logger:
            logger.exception('Unable to create the Bank...')
    return bank


class MyAccountView(grok.View):
    """ List the transactions available for the current users
    """
    grok.context(IMyAccountFolder)
    grok.name('list-transactions')
    grok.require('zope2.View')
    grok.template('myaccount')

    #template = ViewPageTemplateFile('transactions_templates/listtransactionsview.pt')
    def prepareUrl(self, url):
        return urllib.quote(url)

    def get_url(self):
        context = self.context.aq_inner
        #import pdb ; pdb.set_trace()
        return self.prepareUrl(context.absolute_url())

    @memoize
    def getAccountHolderName(self, personalid):
        from Products.CMFCore.utils import getToolByName

        membership_tool = getToolByName(self, 'portal_membership')
        matching_members = [member for member in membership_tool.listMembers()
            if member.getProperty('personal_id')==personalid]
        print matching_members
        if matching_members:
            return matching_members[0].getProperty('fullname')
        else:
            return 'Unknown'

    def addAccountHolderNames(self, jsondictionary):
        #import pdp; pdb.trace()
        items = []
        try:
            for item in jsondictionary:
                item['Name'] = self.getAccountHolderName(item['OffsetPersonalID'])
                items.append(item)
        except Exception, e:
            self.logger.exception('Exception occured: %s' % str(e))
        return items

    def update(self):
        logger = logging.getLogger("@@my-account")

        #s = Settings()
        #settings = s.getSettings()

        #logger.debug("Settings: " + str(settings))

        #user = api.user.get_current()
        #pid = user.getProperty('personal_id')

        # if field is not defined as a personal property it becomes an object and the bank fails to load
        #if type(pid).__name__=='object':
        #    pid = None

        pid = get_pid()

        self.hasTransactions = False
        self.hasAccount = False
        self.hasInvoices = False
        self.hasConnectionError = False

        self.now = DateTime().strftime('%Y-%m-%d %H:%M:%S')
        user = api.user.get_current()

        if pid:
            logger.info('Check user account (' + str(user)+ ')')        

            # Create new bank
            bank = get_bank(logger)

            if bank:
                # Get Account
                try:
                    self.Account = bank.getAccount(personalid=pid)
                    if self.Account:
                        self.hasAccount = True
                except ConnectionError:
                    self.hasConnectionError = True
                    logger.info("Connection Error")
                except Timeout:
                    self.hasConnectionError = True
                    logger.info("Timeout")

                # Get Transactions
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

                # Get Invoices
                try:
                    self.Invoices = bank.getInvoices(personalid=pid, status=0)
                    if self.Invoices:
                        self.Invoices = self.addAccountHolderNames(self.Invoices)
                        self.hasInvoices = True
                except ConnectionError:
                    self.hasConnectionError = True
                    logger.info("Connection Error")
                except Timeout:
                    self.hasConnectionError = True
                    logger.info("Timeout")

        else:
            self.hasTransactions = False
            logger.info("User %s has no personal_id", str(user))

        #import pdb ; pdb.set_trace()


class TransactionDetailView(grok.View):
    grok.context(IMyAccountFolder)
    grok.name('transactions-detail')
    grok.require('zope2.View')
    grok.template('transactiondetails')

    def update(self):
        ''' show transaction details
        '''
        logger = logging.getLogger("@@transaction-details")

        self.now = get_now()
        self.transactionid = self.request.get('id', None)
        self.callback = self.request.get('callback', u'http%3A//localhost%3A8080/plon/my-pages/my-account')
        self.hasTransaction = False

        pid = get_pid()
        logger.info('No pid')
        if pid and self.transactionid:
            bank = get_bank(logger)
            if bank:
                try:
                    self.transactiondetails = bank.getTransactionDetails(personalid=pid, transactionid=self.transactionid)
                    if len(self.transactiondetails) > 0:
                        self.transactiondetails = self.transactiondetails[0]
                    self.hasTransaction = True
                except Timeout:
                    logger.exception('Timout! Unable to get transactiondetails for transaction %s' % (self.transactionid))
                except ConnectionError:
                    logger.exception('ConnectionError! Unable to get transactiondetails for transaction %s' % (self.transactionid))
                except:
                    logger.exception('Unable to get transactiondetails for transaction %s' % (self.transactionid))

class RejectInvoiceForm(grok.View):
    grok.context(IMyAccountFolder)
    grok.name('reject-invoice')
    grok.require('zope2.View')
    grok.template('rejectinvoice')

    def update(self):
        ''' Nothing
        '''
        self.invoiceid = self.request.get('id', None)
        self.status = self.request.get('status', None)



class UpdateInvoiceView(grok.View):
    grok.context(IMyAccountFolder)
    grok.name('update-invoice')
    grok.require('zope2.View')
    #grok.template('transactiondetails')

    def render(self):
        ''' update invoice
        '''
        logger = logging.getLogger("@@update-invoice")

        self.now = get_now()
        self.invoiceid = self.request.get('id', None)
        self.status = self.request.get('status', None)
        self.callback = self.request.get('callback', u'http%3A//localhost%3A8080/plon/my-pages/my-account')
        self.reason = self.request.get('reason', None)
        print self.reason

        pid = get_pid()
        result = "Inget personnummer tillgängligt för avsändare"
        if pid and self.invoiceid and self.status:
            bank = get_bank(logger)
            result = "Problem när anslutningen till banken skulle upprättas"
            if bank:
                try:
                    updated_invoice = bank.updateInvoice(personalid=pid, status=self.status, invoiceid=self.invoiceid, notes=self.reason)
                    logger.info(updated_invoice)
                    result = "Fakturan uppdaterad"
                except Timeout:
                    result = "Kunde inte uppdatera fakturan. Banken svarar inte."
                    logger.exception('Timout! Unable to update invoice with id %s' % (self.invoiceid))
                    return result
                except ConnectionError:
                    result = "Kunde inte uppdatera fakturan. Banken svarar inte."
                    logger.exception('ConnectionError! Unable to update invoice with id %s' % (self.invoiceid))
                    return result
                except:
                    result = "Kunde inte uppdatera fakturan. Obegripligt fel."
                    logger.exception('Unable to update invoice with id %s' % (self.invoiceid))
                    return result
        return result


