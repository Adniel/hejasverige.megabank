from five import grok
from Products.CMFCore.interfaces import ISiteRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class NewInvoiceNotification(grok.View):
    """View (called "@@newinvoicenotification"")
    """

    grok.context(ISiteRoot)
    grok.require('zope2.View')

    newinvoice = ViewPageTemplateFile("newinvoicenotification.pt")
    newinvoice_html = ViewPageTemplateFile("newinvoicenotification_html.pt")
    nouser = ViewPageTemplateFile("newinvoicenotification_nouser.pt")

    def render(self):
        if self.nottype == 'newinvoice':
            text = self.newinvoice(charset=self.charset, portal_url=self.portal_url, member=self.member, request=self.request)
            html = self.newinvoice_html(charset=self.charset, portal_url=self.portal_url, member=self.member, request=self.request)
        else:
            text = self.nouser(charset=self.charset, portal_url=self.portal_url, request=self.request)
            html = text

        import pdb; pdb.set_trace()
        text = text.encode('utf-8')
        html = html.encode('utf-8')
        #utf8_str = unicode(iso885915_str, 'iso-8859-15').encode('utf-8')
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart('alternative')
        msg.set_charset(self.charset)
        msg['Subject'] = "Link"
        msg['From'] = 'hej@hej.se'
        msg['To'] = self.member.getProperty('email')

        part1 = MIMEText(text, 'plain')
        part1.set_charset(self.charset)
        part2 = MIMEText(html, 'html')
        part2.set_charset(self.charset)
        
        msg.attach(part1)
        msg.attach(part2)

        return msg


    def __call__(self, member, charset, portal_url, request, nottype='newinvoice'):
        """Called before rendering the template for this view
        """
        self.member = member
        self.charset = charset
        self.portal_url = portal_url
        self.request = request
        self.email_from_name = 'Robert'
        self.email_from_address = 'rbe@adam.se'
        self.nottype = nottype
        import pdb; pdb.set_trace()
        return self.render()


    
