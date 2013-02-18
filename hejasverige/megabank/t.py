from five import grok

from zope.app.container.interfaces import IObjectAddedEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
from Products.CMFCore.interfaces import IContentish

@grok.subscribe(IContentish, IObjectAddedEvent)
def printMessage(obj, event):
    print "Received event for", obj, "added to", event.newParent


@grok.subscribe(IUserLoggedInEvent)
def printMessage(event):
    print event.principal, "has logged in"
