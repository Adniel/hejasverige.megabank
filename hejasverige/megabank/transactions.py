#from zope.interface import Interface
from hejasverige.megabank.interfaces import IMyAccountFolder
from five import grok
from plone import api
from DateTime import DateTime
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from hejasverige.megabank import _

#from StringIO import StringIO

# Add interface hejasverige.megabank.interfaces.IMyAccountFolder to folder
# http://belomor.zapto.org:9091/Plone/mitt-konto/manage_interfaces
# Add "layout" as string with value @@list-transactions
# http://belomor.zapto.org:9091/Plone/mitt-konto/manage_propertiesForm

class ListTransactionsView(grok.View):
    """ List the transactions available for the current users
    """
    grok.context(IMyAccountFolder)
    grok.name('list-transactions')
    grok.require('zope2.View')

    #template = ViewPageTemplateFile('transactions_templates/listtransactionsview.pt')

    def update(self):
        '''
        >>> from zope.component import getUtility
        >>> from plone.registry.interfaces import IRegistry

        >>> registry = getUtility(IRegistry)
        Now we fetch the HejaSverigeSetting registry

        >>> from hejasverige.settings.interfaces import IHejaSverigeSettings
        >>> settings = registry.forInterface(IHejaSverigeSettings)
        And now we can access the values

        >>> self.settings.megabank_url
        >>> ''
        >>> self.settings.megabank_user
        >>> ''        
        >>> self.settings.megabank_password
        >>> ''
        '''

        import requests
        import logging
        import re
        import json
        import datetime
        # from lxml import etree
        from requests.auth import HTTPBasicAuth
        from zope.component import getUtility
        from plone.registry.interfaces import IRegistry
        registry = getUtility(IRegistry)

        from hejasverige.megabank.interfaces import IMegabankSettings
        settings = registry.forInterface(IMegabankSettings)
        mburl = settings.megabank_url
        mbuser = settings.megabank_user
        mbpassword = settings.megabank_password

        user = api.user.get_current()
        pid = user.getProperty('personal_id')

        self.hasTransactions = True

        today = DateTime().strftime('%Y-%m-%d %H:%M:%S')
        self.now = today #api.portal.get_localized_time(datetime=today)

        if pid:

            url = mburl + '/transactions/' + str(pid)


            logger = logging.getLogger("@@list-transactions")
            logger.info('Check user account (' + str(user)+ ')')        
            logger.info('Calling MegaBank')
            logger.info('User: ' + mbuser)
            logger.info('Password: ' + mbpassword)
            logger.info('Url: ' + url)               

            auth = HTTPBasicAuth(mbuser, mbpassword)

            r = requests.get(url, auth=auth)
            #f = StringIO(r.text)
            #tree = etree.parse(f)
            if r.text:
                payload = json.loads(r.text)

                #dct = json.loads(r.json, object_hook=datetime_parser)
                print r.text

                items = []
                for item in payload:
                    for k in item.keys():
                        p = re.compile('/Date\(')
                        m = p.match(str(item[k]))
                        if m:
                            #item[k] = str(self.decode_json_date(item[k]))
                            item[k] = datetime.datetime(1970, 1, 1) + \
                                datetime.timedelta(milliseconds=int(re.findall(r'\d+', item[k])[0])) + \
                                datetime.timedelta(hours=int(re.findall(r'\d+', item[k])[1][:2]))

                    logger.info('Current item: ' + str(item['ID']))
                    items.append(item)


                self.transactions =  items
            else:
                self.hasTransactions = False
        else:
            self.hasTransactions = False

        #import pdb ; pdb.set_trace()

        #return self.template()
        #return tree 
