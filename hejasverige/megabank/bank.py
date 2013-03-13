# -*- coding: utf-8 -*-

from requests.auth import HTTPBasicAuth

from hejasverige.megabank.config import TRANSACTIONDETAILS_URL
from hejasverige.megabank.config import TRANSACTIONS_URL
from hejasverige.megabank.config import ACCOUNTS_URL
from hejasverige.megabank.config import CARDS_URL
from hejasverige.megabank.config import INVOICES_URL

import json
import requests
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout

import datetime
import logging
import re

import hejasverige.megabank.bank

class Bank():

    def __init__(self, settings):
        ''' settings is a RecordsProxy object retreived from megabank registry settings
        '''
        self.logger = logging.getLogger("bank.class")
        self.auth = HTTPBasicAuth(settings.megabank_user, settings.megabank_password)
        self.url = settings.megabank_url
        try:
            self.timeout = float(settings.megabank_timeout)
        except:
            self.timeout = 10.000

        self.logger = logging.getLogger("hejasverige.megabank.bank.Bank")

        self.logger.info('User: ' + settings.megabank_user)
        self.logger.info('Password: ' + settings.megabank_password)
        self.logger.info('Url: ' + self.url)               
        self.logger.info('Timeout: ' + str(self.timeout))

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
            self.logger.exception('Exception occured: %s' % str(e))
        return items

    def getAccount(self, personalid):

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

        print personalid
        accounts_url = self.url + '/' + ACCOUNTS_URL + '/' + personalid + '/'
        print accounts_url

        r = requests.get(accounts_url, auth=self.auth,
                         timeout=self.timeout)
        if r.text:
            payload = json.loads(r.text)
            self.logger.info('Account Info: ' + r.text)
            return payload

        return []

    def getTransactions(self, personalid, transactionid=None, startdate=None, enddate=None):
        url = self.url + '/' + TRANSACTIONS_URL + '/' + personalid + '/'
        if transactionid:
            url = url + transactionid
        print url

        r = requests.get(url, auth=self.auth,
                         timeout=self.timeout)

        if r.text:
            try:
                payload = json.loads(r.text)

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
                self.logger.exception('Payload could not be loaded')
                self.logger.exception('Exception: %s' % str(e))
                return []
        else:
            self.logger.info('No transactions in payload')
            return []

    def getTransactionDetails(self, personalid, transactionid):
        url = self.url + '/' + TRANSACTIONDETAILS_URL + '/' + personalid + '/' + transactionid
        print url
        r = requests.get(url, auth=self.auth, timeout=self.timeout)

        if r.text:
            try:
                payload = json.loads(r.text)
                return self.convertJsonDictionaryDates(jsondictionary=[payload])
            except Exception, e:
                self.logger.exception("Exception occured: %s" % str(e))
                return []
        else:
            self.logger.info('No transaction details found for transaction id %s' % str(transactionid))
            return []

    def getInvoices(self, personalid, invoiceid=None, startdate=None, enddate=None, status=None):
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

        print url

        r = requests.get(url, auth=self.auth,
                         timeout=self.timeout)

        if r.text:
            try:
                payload = json.loads(r.text)
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
                self.logger.warning('Returned data is not JSON: %s' % str(e))
                return []
        else:
            self.logger.info('No invoces in payload')
            return []

    def getCards(self, personalid):
        if personalid:
            account = getAccount(personalid)
            cards = account.get('Cards', [])
            return cards

        self.logger.debug('No personal_id was provided to getCards')
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
        print url
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        if not notes:
            payload = json.dumps({'ID': int(invoiceid), 'Status': int(status),})
        else:
            payload = json.dumps({'ID': int(invoiceid), 'Status': int(status), 'Notes': notes,})
        self.logger.info('Headers: ' + str(json.dumps(headers)))
        self.logger.info('Posting: ' + str(payload))
        result = requests.put(url, data=payload, headers=headers, auth=self.auth,
                            timeout=self.timeout)
        self.logger.info(result.text)
        return result

    def createInvoice(self, invoice):
        '''
            Creates an invoice 
        '''

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
        return 'Not implemented'

