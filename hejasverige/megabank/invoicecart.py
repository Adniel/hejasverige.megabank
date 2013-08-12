# -*- coding: utf-8 -*-

from five import grok
from collective.beaker.interfaces import ISession
from plone.app.layout.navigation.interfaces import INavigationRoot
from hejasverige.megabank.interfaces import IMyAccountFolder
from hejasverige.megabank.session import SessionKeys

import logging
logger = logging.getLogger(__name__)

class InvoiceCart(grok.View):
    grok.context(INavigationRoot)

    def render(self):
        session = ISession(self.request, None)

        if 'testsessionkey' in self.request:
            session['testsessionkey'] = dict(key1='Hey', key2='Boy')
            session.save()
            return 'Test key stored...'

        if 'remove' in self.request:
            session.delete()
            session.invalidate()
            return 'Session removed and destroyed...'

        if session is None:
            return 'No session initiatied'
        if 'testsessionkey' in session:
            return 'Found test key: ' + str(session['testsessionkey'])
        else:
            return 'Did not find testsessionkey in session...'



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

        if 'Amount' in self.request:
            logger.info('Amount value:' + self.request['amount'])
        # Update session dictionary
        #import pdb;pdb.set_trace()
        try:
            amount = float(self.request['amount'])
        except:
            amount = 0

        import pdb; pdb.set_trace()

        if self.request['checkboxvalue'] == 'true':
            session[SessionKeys.selected_amount] = session[SessionKeys.selected_amount] + amount

            if not any(self.request['checkboxid'] in l for l in session[SessionKeys.selected_invoices]):
                session[SessionKeys.selected_invoices].append(dict(id=self.request['checkboxid'], amount=amount))
        else:
            session[SessionKeys.selected_amount] = session[SessionKeys.selected_amount] - amount
            session[SessionKeys.selected_invoices] = [x for x in session[SessionKeys.selected_invoices] if x.get('id', None) != self.request['checkboxid']]

        import pdb; pdb.set_trace()

        session.save()

        #session['megabank.selectedamount'] =

        return 'Amount selected: ' + str(session[SessionKeys.selected_amount])
