# -*- coding: utf-8 -*-

import logging
from Products.CMFPlone.utils import _createObjectByType
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.interface import alsoProvides
from hejasverige.megabank import _
from hejasverige.megabank.interfaces import IMyAccountFolder

def _my_account():
    return [{
        'id': 'my-account',
        'title': 'Mitt konto',
        'description': 'Mitt konto i Heja Sverige',
        'type': 'Folder',
        'workflow_transition': 'internally_published ',
        'exclude_from_nav': False,
        'layout': '@@list-transactions',
        'interface': ['hejasverige.megabank.interfaces.IMyAccountFolder'],
        }]


def _createObjects(parent, children):
    """This will create new objects, or modify existing ones if id's and type
    match.

    This takes two arguments: the parent to create the content in, and the
    children to create.

    Children is a list of dictionaries defined as follows:

    new_objects = [
        {   'id': 'some-id', 
            'title': 'Some Title',
            'description': 'Some Description',
            'type': 'Folder',
            'layout': 'folder_contents',
            'workflow_transition': 'retract',
            'exclude_from_nav': True,
            'children': profile_children,
            'interface': interface
            },
        ]
    
    * layout:               optional, it sets a different default layout
    * workflow_transition:  optional, it tries to start that state transition
        after the object is created. (You cannot directly set the workflow to 
        any state, but you must push it through legal state transitions.)
    * exclude_from_nav:     optional, excludes item from navigation
    * children:             optional, is a list of dictionaries (like this one)
    * interface:            optional, additional marker interface to add to the folder

    """

    parent.plone_log('Creating %s in %s' % (children, parent))

    workflowTool = getToolByName(parent, 'portal_workflow')

    existing = parent.objectIds()
    for new_object in children:
        if new_object['id'] in existing:
            parent.plone_log('%s exists, skipping' % new_object['id'])
        else:
            _createObjectByType(new_object['type'], parent, id=new_object['id'
                                ], title=new_object['title'],
                                description=new_object['description'])
        parent.plone_log('Now to modify the new_object...')
        obj = parent.get(new_object['id'], None)
        if obj is None:
            parent.plone_log("can't get new_object %s to modify it!"
                             % new_object['id'])
        else:
            if obj.Type() != new_object['type']:
                parent.plone_log("types don't match!")
            else:
                if new_object.has_key('interface'):
                    for mi in new_object['interface']:
                        try:
                            alsoProvides(obj, mi)
                        except:
                            parent.plone_log("WARNING: couldn't add interface to object")
                if 1==2:
                    pass
                if new_object.has_key('layout'):
                    obj.setLayout(new_object['layout'])
                if new_object.has_key('workflow_transition'):
                    try:
                        workflowTool.doActionFor(obj,
                                new_object['workflow_transition'])
                    except WorkflowException:
                        parent.plone_log("WARNING: couldn't do workflow transition"
                                )
                if new_object.has_key('exclude_from_nav'):
                    obj.setExcludeFromNav(new_object['exclude_from_nav'])
                obj.reindexObject()
                children = new_object.get('children', [])
                if len(children) > 0:
                    _createObjects(obj, children)


def setupMyAccountFolder(portal, logger=None):
    if logger:
        logger.info('')
    #_createObjects(portal, _my_account())
    folder_id = 'my-account'
    folder_title = u'Mitt konto'
    object_type = 'Folder'
    view = '@@list-transactions'

    existing_objects = portal.objectIds()

    if folder_id in existing_objects:
        logger.info("Object exists in folder")
    else:
        _createObjectByType(object_type, portal, id=folder_id,
                            title=_(folder_title))

    obj = portal.get(folder_id, None)
    if obj:
        if obj.Type() == object_type:
            try:
                alsoProvides(obj, IMyAccountFolder)
            except:
                logger.info("Could not apply marker interface...")

            try:
                obj.setLayout(view)
            except:
                logger.info("Could not apply marker interface...")

            try:
                workflowTool = getToolByName(portal, 'portal_workflow')
                workflowTool.doActionFor(obj, 'publish_internally')
            except WorkflowException:
                logger.info("Could not apply workflow publish_internally transition. Trying publish...")
                try:                
                    workflowTool.doActionFor(obj, 'publish')
                except WorkflowException:
                    logger.info("Workflow transition 'publish' failed...")



def importVarious(context):
    """Miscellanous steps import handle
    """
    if context.readDataFile('hejasverige.megabank-various.txt') is None:
        return
    logger = logging.getLogger('hejasverige.megabank')
    portal = context.getSite()
    logger.info('Creating My Account Folder')
    setupMyAccountFolder(portal, logger)
