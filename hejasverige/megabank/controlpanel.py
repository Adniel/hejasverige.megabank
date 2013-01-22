from plone.app.registry.browser import controlpanel
from hejasverige.megabank.interfaces import IMegabankSettings
from hejasverige.megabank import _


class MegabankSettingsEditForm(controlpanel.RegistryEditForm):

    schema = IMegabankSettings
    label = _(u"Megabank settings")
    description = _(u"""Common settings for Megabank""")

    def updateFields(self):
        super(MegabankSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(MegabankSettingsEditForm, self).updateWidgets()
        self.widgets['megabank_url'].style = u'width: 50%;'


class MegabankSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = MegabankSettingsEditForm
