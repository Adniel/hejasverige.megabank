from zope.i18nmessageid import MessageFactory

_ = MessageFactory('hejasverige.megabank')

  # -*- extra stuff goes here -*- 
print "Initializing MegaBank Views..."

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
