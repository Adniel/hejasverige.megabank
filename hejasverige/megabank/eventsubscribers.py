from five import grok

from smtplib import SMTPRecipientsRefused
from zope.app.container.interfaces import IObjectAddedEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
#from Products.CMFCore.interfaces import IContentish
from hejasverige.content.invoice import IInvoice
from hejasverige.megabank.bank import Bank
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException

import logging

logger = logging.getLogger(__name__)
#from hejasverige.megabank.bank import CommunicationError


#@grok.subscribe(IContentish, IObjectAddedEvent)
#def printMessage(obj, event):
#    pass
#    print "Received event for", obj, "added to", event.newParent

@grok.subscribe(IUserLoggedInEvent)
def getAccount(event):
    logger.info("Will make sure %s has an account." % event.principal.getId())
    bank = Bank()
    #import pdb; pdb.set_trace()
    personal_id = event.principal.getProperty('personal_id')
    if type(personal_id).__name__ == 'object':
        personal_id = None

    fullname = event.principal.getProperty('fullname')
    if personal_id:
        try:
            result = bank.getAccount(personal_id)
        except Exception, ex:
            logger.exception('Unable to access the bank. User account could not be checked: %s' % (str(ex)))
            # problems accessing the bank
            #pass
        else:
            if not result:
                # user had no account in the bank
                # create account 
                result = bank.createAccount(personalid=personal_id, name=fullname)

    return
#@grok.subscribe(IInvoice, IObjectAddedEvent)
#def printMessage(obj, event):
#    print "Invoice", obj.id, "added..."

def sendInvoice(obj, pos_transition, neg_transition=None):
    
    # read invoice info

    bank = Bank()
    workflowTool = getToolByName(obj, 'portal_workflow')
    logger.debug("getToolByName says: %s" % workflowTool)

    result = None
    createInvoiceResult = ''
    try:
        result = bank.createInvoice(obj)
        createInvoiceResult = str(result)
    except Exception, ex:
        createInvoiceResult = 'Det gick inte att skapa en faktura i banken: %s' % str(ex)
        logger.error(createInvoiceResult)


    if result:
        logger.debug('CreateInvoice result: %s' % (str(result),))
        #logger.info('Created invoice with ID: %s' % ( str(result.get('ID', None), ) )
        ID = result.get('ID', None)
        logger.info('Created invoice with ID: %s' % str(ID))
        #Update Invoice object with external id
        obj.externalId = result.get('ID', None)
        obj.reindexObject()

        try:
            #import pdb; pdb.set_trace()
            workflowTool.doActionFor(obj, pos_transition, comment=createInvoiceResult)
            logger.debug("Object %s changed state to %s" % (obj.id, pos_transition))
        except WorkflowException, ex:
            logger.error("Could not apply workflow transition %s. %s state not changed: %s" % (pos_transition, obj.id, str(ex)))

        # Send mail about new to recipient
        sendEmailNotification(obj)

    else:
        if neg_transition:
            try:
                # TODO: set to variable comment, depending on what happened when communicated with the bank. (and
                # display comment when listing objects, or at least on details page.)
                workflowTool.doActionFor(obj, neg_transition, comment=createInvoiceResult)
                logger.debug("Object %s changed state to %s" % (obj.id, neg_transition))
            except WorkflowException, ex:
                logger.error("Could not apply workflow transition %s. %s state not changed: %s" % (neg_transition, obj.id, str(ex)))

            logger.info("Bank did not receive the invoice with id %s" % (obj.id))
    
    #import pdb; pdb.set_trace()
    # comments from transition can be read using
    # workflowTool.getStatusOf('hejasverige_invoice_workflow', obj).get('comments')


#@memoize
def getInvoiceRecipientFromId(self, personalid):
    from Products.CMFCore.utils import getToolByName

    membership_tool = getToolByName(self, 'portal_membership')
    matching_members = [member for member in membership_tool.listMembers()
        if member.getProperty('personal_id')==personalid]
    print matching_members
    if matching_members:
        return matching_members[0]
    else:
        return None

def sendEmailNotification(obj):

    #import pdb; pdb.set_trace()
    from zope.component.hooks import getSite
    from plone import api
    from Products.CMFPlone.utils import safe_unicode

    site = getSite()
    email_charset = getattr(obj, 'email_charset', 'utf-8')
    
    #member = api.user.get_current()
    #member = api.user.get(username='eva')

    member = getInvoiceRecipientFromId(site, obj.invoiceRecipient)
    if member:
        mail_template = site.unrestrictedTraverse('@@newinvoicenotification')
        mail_text = mail_template(member=member,
                                  portal_url=obj.absolute_url(),
                                  charset=email_charset,
                                  request=obj.REQUEST,
                                  nottype='newinvoice')
    else:
        mail_template = site.unrestrictedTraverse('@@newinvoicenotification')
        mail_text = mail_template(member=api.user.get_current(),
                                  portal_url=obj.absolute_url(),
                                  charset=email_charset,
                                  request=obj.REQUEST,
                                  nottype='nouser')

    try:
        host = getToolByName(obj, 'MailHost')
        # The ``immediate`` parameter causes an email to be sent immediately
        # (if any error is raised) rather than sent at the transaction
        # boundary or queued for later delivery.
        return host.send(safe_unicode(mail_text), immediate=True)
    except SMTPRecipientsRefused:
        # Don't disclose email address on failure
        raise SMTPRecipientsRefused('Recipient address rejected by server')
    except Exception as e:
        # Do not abort invoice creation process even if notification mail fails...
        logger.exception(e)

@grok.subscribe(IInvoice, IObjectAddedEvent)
def sendInvoiceEvent(obj, event):
    print 'Sending invoice to Megabank'
    #import pdb; pdb.set_trace()

    sendInvoice(obj, 'transfer', 'fail')

@grok.subscribe(IInvoice, IActionSucceededEvent)
def resendInvoiceEvent(obj, event):
    if event.action == 'retract':
        sendInvoice(obj, 'transfer', 'fail')



