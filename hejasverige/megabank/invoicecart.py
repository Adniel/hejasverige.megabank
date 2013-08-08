# -*- coding: utf-8 -*-

from five import grok
from collective.beaker.interfaces import ISession
from plone.app.layout.navigation.interfaces import INavigationRoot


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
