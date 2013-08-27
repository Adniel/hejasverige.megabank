# -*- coding: utf-8 -*-

from five import grok
from collective.beaker.interfaces import ISession
from plone.app.layout.navigation.interfaces import INavigationRoot
from hejasverige.megabank.interfaces import IMyAccountFolder
from hejasverige.megabank.session import SessionKeys
from hejasverige.content.interfaces import IMyPages
from hejasverige.megabank.bank import Bank
from plone import api
from plone.memoize.instance import memoize
from Products.CMFCore.utils import getToolByName
from hejasverige.megabank import _
from zExceptions import Forbidden
from zope.component import getMultiAdapter
from hejasverige.megabank.config import MEGABANKVIEW_URL

import logging
logger = logging.getLogger(__name__)

grok.templatedir("templates")


class InvoiceCart(grok.View):
    grok.context(INavigationRoot)

    def render(self):
        session = ISession(self.request, None)

        if session is None:
            return None

        if 'testsessionkey' in self.request:
            session['testsessionkey'] = dict(key1='Hey', key2='Boy')
            session.save()
            return 'Test key stored...'

        if 'testsessionkey2' in self.request:
            session['testsessionkey2'] = dict(key1='Hey', key2='Boy')
            session.save()
            return 'Test key2 stored...'


        if 'remove' in self.request:
            session.delete()
            session.invalidate()
            return 'Session removed and destroyed...'

        if session is None:
            return 'No session initiatied'
        if 'testsessionkey' in session:
            return 'Found session: ' + str(session)
        else:
            return 'Did not find testsessionkey in session...'

class CheckOut(grok.View):
    grok.context(INavigationRoot)
    grok.require('hejasverige.ViewMyAccount')
    grok.implements((IMyPages, IMyAccountFolder))


    @memoize
    def session(self):
        return ISession(self.request)

    @memoize
    def myinfo(self):
        info = {}

        pid = api.user.get_current().getProperty('personal_id')
        #import pdb; pdb.set_trace()
        try:
            accountinfo = Bank().getAccount(personalid=pid, context=self)
            info['pid'] = pid
            info['balance'] = accountinfo.get('Balance', None)
            info['amount_pending'] = accountinfo.get('AmountPending', None)
            info['amount_to_pay'] = self.session()[SessionKeys.selected_amount]
        except:
            pass 

        return info

    def update(self):
        """ Renders the view """
        session = ISession(self.request, None)

        if session is None:
            return None

        if 'form.button.Submit' in self.request:
            #import pdb; pdb.set_trace()

            authenticator = getMultiAdapter((self.context, self.request), name=u"authenticator")
            if not authenticator.verify():
                raise Forbidden()

            utils = getToolByName(self, "plone_utils")
            url = self.url()


            if float(self.request['points_amount']) > float(self.myinfo().get('balance')):
                utils.addPortalMessage(_('Angivna poäng är fler än du har.'), 'error')
                return self.request.response.redirect(url)

            if float(self.request['points_amount']) + float(self.request['card_amount']) != float(self.myinfo().get('amount_to_pay')):
                utils.addPortalMessage(_('Totalbeloppet är inte korrekt.'), 'error')
                return self.request.response.redirect(url)

            if float(self.request['points_amount']) < 0:
                utils.addPortalMessage(_('Antalet poäng får ej vara mindre än 0'), 'error')
                return self.request.response.redirect(url)

            if float(self.request['card_amount']) < 0:
                utils.addPortalMessage(_('Kortbelopp får ej vara mindre än 0'), 'error')
                return self.request.response.redirect(url)
            
            bank = Bank()
            obj = dict()
            obj['amount'] = float(self.request['card_amount'])
            if len(session[SessionKeys.selected_invoices]) > 1:
                invoiceword = 'fakturor'
            else:
                invoiceword = 'faktura'

            obj['description'] = "Onlinebetalning av %s (%s) " % (invoiceword, ", ".join([x.get('invoiceno') for x in session[SessionKeys.selected_invoices]]))
            obj['invoices'] = [int(x.get('id')) for x in session[SessionKeys.selected_invoices]]
            obj['url'] = self.context.absolute_url() + '/@@psplandingpage'
            pid = self.myinfo().get('pid')

            try:
                result = bank.registerOnlineTransaction(obj, pid)
                #import pdb; pdb.set_trace()
            except Exception, ex:
                error_message = u'Kunde inte kontakta banken. Betalningen kunde inte registreras.'
                logger.error(error_message + ' Ex: %s' % (str(ex)))
                utils.addPortalMessage(_(result.get(error_message)), 'error')
                return self.request.response.redirect(url)
                pass
            else:
                if result:
                    try:
                        redir_url = result.get('Url', None)
                        if redir_url:
                            return self.request.response.redirect(redir_url)
                    except:
                        pass
                
                utils.addPortalMessage(_(u'Banken svarade dåligt. Ingen betalning kan genomföras.'), 'error')
                return self.request.response.redirect(url)


class PspLandingPage(grok.View):
    grok.context(INavigationRoot)
    grok.require('hejasverige.ViewMyAccount')

    def render(self):
        session = ISession(self.request, None)

        if session is None:
            return None
        utils = getToolByName(self, "plone_utils")
        url = self.context.absolute_url() + '/' + MEGABANKVIEW_URL

        responseCode = self.request['responseCode']
        transactionId = self.request['transactionId']
        bank = Bank()

        if responseCode == 'Cancel':
            # the person pressed Cacel or error occured
            # TODO: Kontrollera att Megabank lyckas med cancel, lägg till i meddeelande
            result = bank.cancelOnlineTransaction(transactionId)
            utils.addPortalMessage(_(u'Betalningen avbröts'), 'info')
            return self.request.response.redirect(url)

        if responseCode == 'OK':
            # The PSP performed payment
            # TODO: Kontrollera att Megabank lyckas med commit, lägg till i meddeelande
            # Remove payed invoices from session's selected_invoices
            session[SessionKeys.selected_invoices] = []
            result = bank.commitOnlineTransaction(transactionId)
            utils.addPortalMessage(_(u'Betalningen genomfördes'), 'info')
            return self.request.response.redirect(url)



class StoreMarkedInvoices(grok.View):
    grok.context(IMyAccountFolder)
    grok.require('hejasverige.ViewMyAccount')

    def render(self):
        session = ISession(self.request, None)

        if session is None:
            return None

        if SessionKeys.selected_amount not in session:
            logger.info('SessionKey %s not present in session. Initating with 0...' % SessionKeys.selected_amount)
            session[SessionKeys.selected_amount] = 0
            session.save()

        if SessionKeys.selected_invoices not in session:
            logger.info('SessionKey %s not present in session. Initating empty list...' % SessionKeys.selected_invoices)
            session[SessionKeys.selected_invoices] = []
            session.save()

        logger.info('Hey, I received a call...')
        if 'checkboxid' in self.request:
            logger.info('Checkbox id:' + self.request['checkboxid'])

        if 'checkboxvalue' in self.request:
            logger.info('Checkbox value:' + self.request['checkboxvalue'])

        if 'invoiceno' in self.request:
            logger.info('Invoiceno value:' + self.request['invoiceno'])

        if 'Amount' in self.request:
            logger.info('Amount value:' + self.request['amount'])
        # Update session dictionary
        #import pdb;pdb.set_trace()
        try:
            amount = float(self.request['amount'])
        except:
            amount = 0

        #import pdb; pdb.set_trace()

        if self.request['checkboxvalue'] == 'true':
            session[SessionKeys.selected_amount] = session[SessionKeys.selected_amount] + amount

            if not self.request['checkboxid'] in [l.get('id') for l in session[SessionKeys.selected_invoices]]:
                session[SessionKeys.selected_invoices].append(dict(id=self.request['checkboxid'], amount=amount, invoiceno=self.request['invoiceno']))
                logger.debug(session[SessionKeys.selected_invoices])
        else:
            session[SessionKeys.selected_amount] = session[SessionKeys.selected_amount] - amount
            session[SessionKeys.selected_invoices] = [x for x in session[SessionKeys.selected_invoices] if x.get('id', None) != self.request['checkboxid']]

        #import pdb; pdb.set_trace()
        try:
            session.save()
            logger.debug("Session saved...")
        except:
            logger.exception("Session not saved!")
        #session['megabank.selectedamount'] =

        return str(session[SessionKeys.selected_amount])
