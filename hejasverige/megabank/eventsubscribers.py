from five import grok

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

#@grok.subscribe(IUserLoggedInEvent)
#def printMessage(event):
#    print event.principal, "has logged in"

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

@grok.subscribe(IInvoice, IObjectAddedEvent)
def printMessage(obj, event):
    print 'TODO: Create invoice in megabank!'
    sendInvoice(obj, 'transfer', 'fail')


@grok.subscribe(IInvoice, IActionSucceededEvent)
def printMessage(obj, event):
    if event.action == 'retract':
        sendInvoice(obj, 'transfer', 'fail')



