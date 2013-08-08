# -*- coding: utf-8 -*-

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout

from Products.CMFPlone.utils import safe_unicode
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from hejasverige.megabank.config import TRANSACTIONDETAILS_URL
from hejasverige.megabank.config import TRANSACTIONS_URL
from hejasverige.megabank.config import ACCOUNTS_URL
from hejasverige.megabank.config import CARDS_URL
from hejasverige.megabank.config import INVOICES_URL
from hejasverige.megabank.interfaces import IMegabankSettings

import json

import datetime
import time
import re
import sys


import logging
logger = logging.getLogger(__name__)

class Bank():

    def __init__(self):
        ''' settings is a RecordsProxy object retreived from megabank registry settings
        '''

        # read the settings for the connection to the bank
        settings = self.getSettings()

        #self.logger = logging.getLogger("bank.class")
        self.auth = HTTPBasicAuth(settings.megabank_user, settings.megabank_password)
        self.url = settings.megabank_url

        try:
            self.cachetimeout = int(settings.megabank_cachetimeout)
        except:
            self.cachetimeout = 600

        try:
            self.timeout = float(settings.megabank_timeout)
        except:
            self.timeout = 10.000

        #self.logger = logging.getLogger("hejasverige.megabank.bank.Bank")

        #logger.info('User: ' + settings.megabank_user)
        #logger.info('Password: ' + settings.megabank_password)
        logger.info('Url: ' + self.url)
        logger.info('Timeout: ' + str(self.timeout))

    def getSettings(self):
        ''' Helper function to get the settings provided by megabank registry

        '''
        try:
            registry = getUtility(IRegistry)
        except:
            logger.exception('Failed to get utility IRegistry')
            return

        settings = registry.forInterface(IMegabankSettings)

        return settings

    def convertJsonDictionaryDates(self, jsondictionary):
        #import pdp; pdb.trace()
        items = []
        try:
            for item in jsondictionary:
                for k in item.keys():

                    if isinstance(item[k], dict):
                        item[k] = self.convertJsonDictionaryDates(jsondictionary=[item[k]])[0]
                    else:
                        #\\/Date\((-?\d+)\)\\/

                        p = re.compile('/Date\(')
                        m = p.match(str(item[k]))
                        if m:
                            item[k] = datetime.datetime(1970, 1, 1) \
                                + datetime.timedelta(milliseconds=int(re.findall(r'\d+'
                                    , item[k])[0])) \
                                + datetime.timedelta(hours=int((re.findall(r'\d+'
                                    , item[k])[1])[:2]))
                items.append(item)
        except Exception, e:
            logger.exception('Exception occured: %s' % str(e))
        return items

    def getJsonDate(self, date):
        init_date = datetime.datetime(1970, 1, 1)

        if type(date) is not datetime.datetime:
            logger.warning('Invalid date! %s' % str(date))
            return None
        else:
            delta = date - init_date
            day_part = delta.days * 86400 * 1000
            second_part = delta.seconds * 1000
            microsecond_part = delta.microseconds / 1000

            total = day_part + second_part + microsecond_part
            jsondate = '/Date(' + str(total) + '+0200)/'

        return jsondate

    def setExpiration(self, secs):
        #expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=10000) # expires in 30 days
        #return expires.strftime("%a, %d %b %Y %H:%M:%S GMT")        

        from email.Utils import formatdate
        expiration_seconds = time.time() + secs # 5 hours from now
        expires = formatdate(expiration_seconds, usegmt=True) 
        return expires

    def getAccountFromMegabank(self, personalid):

        logger.debug('getAccountFromMegabank(self, %s)' % str(personalid))
        accounts_url = self.url + '/' + ACCOUNTS_URL + '/' + personalid + '/'
        logger.debug('Using url: %s ' % accounts_url)

        r = requests.get(accounts_url, auth=self.auth,
                         timeout=self.timeout)

        if r.text:
            payload = json.loads(r.text)
            logger.info('Account Info: ' + r.text)
            return payload

        return []

    def deleteAccount(self, personalid):
        logger.debug('deleteAccount(self, %s)' % str(personalid))
        accounts_url = self.url + '/' + ACCOUNTS_URL + '/' + personalid + '/'

        logger.debug('Using url: %s ' % accounts_url)

        r = requests.delete(accounts_url, auth=self.auth,
                         timeout=self.timeout)

        if r.text:
            payload = json.loads(r.text)
            self.logger.info('Delete account returned: ' + r.text)
            return payload

        return []

    def createAccount(self, personalid, name=None, temporary=False, context=None):
        logger.debug('createAccount(self, %s)' % str(personalid))
        accounts_url = self.url + '/' + ACCOUNTS_URL + '/' + personalid + '/'
        if name:
            # Zope.SiteErrorLog 1375955955.10.328894126255
            # names with unicode characters renders UnicodeError: Ordinal not in range...
            name = safe_unicode(name)
            print name
            accounts_url = accounts_url + '?name=' + name

        logger.debug('Using url: %s ' % accounts_url)

        r = requests.post(accounts_url, auth=self.auth,
                         timeout=self.timeout)

        if r.text:
            payload = json.loads(r.text)
            self.logger.info('Create account returned: ' + r.text)
            return payload

        return []

    def getAccount(self, personalid, context=None):

        #/accounts/<pid>
        #
        #{
        #    "AccountNumber":"String content",
        #    "AccountTypeID":2147483647,
        #    "AmountAvailable":12678967.543233,
        #    "AmountPending":12678967.543233,
        #    "AmountReserved":12678967.543233,
        #    "Balance":12678967.543233,
        #    "Cards":[{
        #        "AccountID":2147483647,
        #        "AccountPersonalID":"String content",
        #        "CardNumber":"String content",
        #        "Created":"\/Date(928142400000+0200)\/",
        #        "ID":2147483647,
        #        "PersonalID":"String content"
        #    }],
        #    "ID":2147483647,
        #    "Limit":12678967.543233,
        #    "Name":"String content",
        #    "PersonalID":"String content",
        #    "Temporary":true
        #}

        # If a context is provided. Try to return values from a cookie.
        # If no cookie is found collect new values
        if context:
            cookie = context.request.get('__myaccountinfo', None)
            if not cookie:
                logger.debug('__myaccountinfo cookie did not exist. Create new cookie')
                value = self.getAccountFromMegabank(personalid)
                context.request.response.setCookie('__myaccountinfo', value, path='/', expires=self.setExpiration(self.cachetimeout))        
                #cookie = context.request.response.cookies.get('__myaccountinfo', None)
                return value
            else:
                #import pdb; pdb.set_trace()
                import ast
                cookie = ast.literal_eval(cookie)
                logger.debug('__myaccountinfo cookie did exist. Checking cookie content.')
                if cookie.get('AccountNumber', None):
                    logger.debug('Cookie was ok. Returning paistry.')
                    return cookie
                else:
                    logger.debug('Cookie was corrupt. Calling bank again for new cookie.')
                    value = self.getAccountFromMegabank(personalid)
                    context.request.response.setCookie('__myaccountinfo', value, path='/', expires=self.setExpiration(self.cachetimeout))        
                    return value

                
        else:
            return self.getAccountFromMegabank(personalid)


    def getTransactions(self, personalid, transactionid=None, startdate=None, enddate=None):
        url = self.url + '/' + TRANSACTIONS_URL + '/' + personalid + '/'
        if transactionid:
            url = url + transactionid
        logger.debug('getTransactions url: %s' % url)

        r = requests.get(url, auth=self.auth,
                         timeout=self.timeout)

        logger.debug('Request returned: %s' % r.text[1:1000])

        if r.text:
            try:
                logger.debug('Loading returned data as JSON')
                payload = json.loads(r.text.encode('ascii', 'ignore'))

                logger.debug('Updating date format in JSON structure')                
                items = []
                p = re.compile('/Date\(')
                for item in payload:
                    for k in item.keys():
                        m = p.match(str(item[k]))
                        if m:
                            item[k] = datetime.datetime(1970, 1, 1) \
                                    + datetime.timedelta(milliseconds=int(re.findall(r'\d+'
                                    , item[k])[0])) \
                                    + datetime.timedelta(hours=int((re.findall(r'\d+'
                                    , item[k])[1])[:2]))

                    items.append(item)

                return items
            except Exception, e:
                logger.exception('Payload could not be loaded')
                logger.exception('Exception: %s' % str(e))
                return []
        else:
            logger.info('No transactions in payload')
            return []

    def getTransactionDetails(self, personalid, transactionid):
        url = self.url + '/' + TRANSACTIONDETAILS_URL + '/' + personalid + '/' + transactionid
        logger.debug('getTransactionDetails url: %s' % url)
        r = requests.get(url, auth=self.auth, timeout=self.timeout)
        if r.text:
            try:
                payload = json.loads(r.text.encode('ascii', 'ignore'))
                return self.convertJsonDictionaryDates(jsondictionary=[payload])
            except Exception, e:
                logger.exception("Exception occured: %s" % str(e))
                return []
        else:
            logger.info('No transaction details found for transaction id %s' % str(transactionid))
            return []

    def getInvoices(self, personalid, invoiceid=None, startdate=None, enddate=None, status=None, outgoing='false'):
        # Status
        # 0 = new
        # 1 = approved
        # 2 = rejected
        url = self.url + '/' + INVOICES_URL + '/' + personalid + '?'
        url = url + 'status=' + str(status)

        if invoiceid:
            url = url + '&invoiceid=' + str(invoiceid)

        if startdate:
            url = url + '&from=' + str(startdate)

        if enddate:
            url = url + '&to=' + str(enddate)

        if outgoing:
            url = url + '&outgoing=' + str(outgoing)

        logger.debug('getInvoices url: %s' % url)

        r = requests.get(url, auth=self.auth,
                         timeout=self.timeout)

        logger.debug('Request returned: %s' % r.text[1:1000])

        if r.text:
            try:
                logger.debug('Loading returned data as JSON')                
                payload = json.loads(r.text.encode('ascii', 'ignore'))
                #    import pdb; pdb.set_trace()

                logger.debug('Updating date format in JSON structure')                
                items = []
                p = re.compile('/Date\(')
                for item in payload:
                    for k in item.keys():
                        m = p.match(str(item[k]))
                        if m:
                            item[k] = datetime.datetime(1970, 1, 1) \
                                + datetime.timedelta(milliseconds=int(re.findall(r'\d+'
                                    , item[k])[0])) \
                                + datetime.timedelta(hours=int((re.findall(r'\d+'
                                    , item[k])[1])[:2]))

                    items.append(item)

                return items
            except Exception, e:
                logger.exception('Returned data is not JSON: %s' % str(e))
                return []
        else:
            logger.info('No invoces in payload')
            return []

    def getCards(self, personalid):
        if personalid:
            account = getAccount(personalid)
            cards = account.get('Cards', [])
            return cards

        logger.debug('No personal_id was provided to getCards')
        return []

    def updateInvoice(self, personalid, invoiceid, status, notes=None):
        '''
            Updates an invoice 
        '''

        # PUT
        # {
        #   'ID': invoiceid
        #   'Status': status
        #   'Notes': notes
        # }

        url = self.url + '/' + INVOICES_URL + '/' + personalid + '/'
        logger.debug('updateInvoice url: %s' % url)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if not notes:
            payload = json.dumps({'ID': int(invoiceid), 'Status': int(status),})
        else:
            payload = json.dumps({'ID': int(invoiceid), 'Status': int(status), 'Notes': notes,})
        logger.info('Headers: ' + str(json.dumps(headers)))
        logger.info('Posting: ' + str(payload))
        result = requests.put(url, data=payload, headers=headers, auth=self.auth,
                            timeout=self.timeout)
        logger.debug('Payload %s' % result.text)
        return result

    def createInvoice(self, obj):
        '''
            Creates an invoice 
        '''
        logger.info("Invoice with id %s will be sent to the bank" % str(obj.id))

        # POST
        #{
        #   "Amount":12678967.543233,
        #   "Created":"\/Date(928142400000+0200)\/",
        #    "Description":"String content",
        #    "ExternalID":"String content",
        #    "ID":2147483647,
        #    "OffsetPersonalID":"String content",
        #    "PersonalID":"String content",
        #    "Reference":"String content",
        #    "Status":2147483647,
        #    "Subject":"String content",
        #    "TransactionDate":"\/Date(928142400000+0200)\/"
        # }
        #{ 
        # "Amount":10000, 
        # "Description":"desco", 
        # "ExternalID":"extisdag",                  
        # "PersonalID":"7804246697", 
        # "Reference":"ref", 
        # "Subject":"subj", 
        #  "TransactionDate":"\/Date(928142400000+0200)\/" 
        #}
        
        #invoice_url = obj.absolute_url()
        invoice = {"Amount": obj.invoiceTotalAmount,
                   "ExternalID": obj.invoiceNo,
                   "PersonalID": obj.invoiceRecipient,
                   "Reference": obj.invoiceRecipientName,
                   "Subject": obj.description,
                   "TransactionDate": self.getJsonDate(obj.invoiceExpireDate)
                   }
        
        #import pdb; pdb.set_trace()

        url = self.url + '/' + INVOICES_URL + '/' + obj.invoiceSender + '/'
        logger.debug('createInvoice url: %s' % url)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        payload = json.dumps(invoice)

        logger.info('Headers: ' + str(headers))
        logger.info('Posting: ' + str(payload))

        try:
            result = requests.post(url,
                                   data=payload,
                                   headers=headers,
                                   auth=self.auth,
                                   timeout=self.timeout
                                   )
        except:
            raise
        #except Timeout, ex:
        #    stacktrace = sys.exc_info()[2]
        #    raise ValidationError(err.message), None, stacktrace
        #except ConnectionError, ex:
        #    stacktrace = sys.exc_info()[2]
        #    raise ValidationError(err.message), None, stacktrace


        #self.logger.info(result.text)
        #self.logger.info(result.text)
        logger.info(result.status_code)
        #import pdb; pdb.set_trace()
        try:
            returned_data = json.loads(result.text)
        except:
            returned_data = None

        return returned_data
