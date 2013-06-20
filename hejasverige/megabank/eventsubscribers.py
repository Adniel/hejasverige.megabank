from five import grok

from smtplib import SMTPRecipientsRefused
from zope.app.container.interfaces import IObjectAddedEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
from Products.CMFCore.interfaces import IContentish
from hejasverige.content.invoice import IInvoice
from hejasverige.megabank.bank import Bank
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
#from hejasverige.megabank.bank import CommunicationError


#@grok.subscribe(IContentish, IObjectAddedEvent)
#def printMessage(obj, event):
#    pass
#    print "Received event for", obj, "added to", event.newParent

@grok.subscribe(IUserLoggedInEvent)
def getAccount(event):
    print "Will make sure " + event.principal.getId() + " has an account."
    bank = Bank()
    #import pdb; pdb.set_trace()
    personal_id =  event.principal.getProperty('personal_id')
    fullname =  event.principal.getProperty('fullname')
    try:
        result = bank.getAccount(personal_id)
    except Exception, ex:
        # problems accessing the bank
        pass
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
    print "getToolByName says:", workflowTool

    result = None

    try:
        result = bank.createInvoice(obj)
    except Exception, ex:
        print 'Resultatet blir fel: ' + str(ex)

    if result:
        print 'CreateInvoice result: ' + str(result)
        print 'ID: ' + str(result.get('ID', None))
        #Update Invoice object with external id
        #import pdb; pdb.set_trace()
        obj.externalId = result.get('ID', None)
        obj.reindexObject()

        try:
            #import pdb; pdb.set_trace()
            workflowTool.doActionFor(obj, pos_transition, comment='All was fine')
            print "Object", obj.id, "changed state"
        except WorkflowException:
            print "Could not apply workflow transition", pos_transition, ".", obj.id, "state not changed"

        # Send mail about new to recipient
    else:
        if neg_transition:
            try:
                # TODO: set to variable comment, depending on what happened when communicated with the bank. (and
                # display comment when listing objects, or at least on details page.)
                workflowTool.doActionFor(obj, neg_transition, comment='Error error. Maybe time out.')
                print "Object", obj.id, "changed state"
            except WorkflowException, ex:
                print "Could not apply workflow transition", neg_transition, ".", obj.id, "state not changed"
                print str(ex)
            print "Bank did not receive the invoice with id", obj.id
    
    #import pdb; pdb.set_trace()
    # comments from transition can be read using
    # workflowTool.getStatusOf('hejasverige_invoice_workflow', obj).get('comments')

    return

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
    
    #try:
    #    self.context.MailHost.send(root.as_string(), immediate=True)
    #except Exception as e:
    #    log = logging.getLogger("MailDataManager")
    #    log.exception(e)
    #return

@grok.subscribe(IInvoice, IObjectAddedEvent)
def sendInvoiceEvent(obj, event):
    print 'Sending invoice to Megabank'
    import pdb; pdb.set_trace()

    sendInvoice(obj, 'transfer', 'fail')
    sendEmailNotification(obj)

@grok.subscribe(IInvoice, IActionSucceededEvent)
def resendInvoiceEvent(obj, event):
    if event.action == 'retract':
        sendInvoice(obj, 'transfer', 'fail')



