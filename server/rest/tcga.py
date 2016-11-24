#!/usr/bin/env python
"""
Endpoints providing a simplified interface for handling TCGA datasets.
"""

from __future__ import print_function
from girder.api import access
from girder.api.describe import describeRoute, Description
from girder.api.rest import Resource, RestException, loadmodel
from girder.constants import TokenScope, AccessType
from girder.utility import setting_utilities
from girder.models.model_base import ValidationException
from ..constants import TCGACollectionSettingKey


class TCGAResource(Resource):

    def __init__(self):
        super(TCGAResource, self).__init__()

        @setting_utilities.validator({
            TCGACollectionSettingKey
        })
        def validateTCGACollection(doc):
            model = self.model('collection').load(
                doc['value'], force=True
            )
            if model is None:
                raise ValidationException(
                    'Invalid collection id', 'value'
                )

        self.resourceName = 'tcga'
        self.route('GET', (), self.getCollection)
        self.route('POST', (), self.setCollection)

        self.route('GET', ('cancer',), self.findCancer)
        self.route('GET', ('cancer', ':id'), self.getCancer)
        self.route('POST', ('cancer',), self.importCancer)

        self.route('GET', ('case',), self.findCase)
        self.route('GET', ('case', ':id',), self.getCase)
        self.route('POST', ('case',), self.importCase)

        self.route('GET', ('slide',), self.findSlide)
        self.route('GET', ('slide', ':id'), self.getSlide)
        self.route('POST', ('slide',), self.importSlide)

        self.route('GET', ('image',), self.findImage)
        self.route('GET', ('image', ':id'), self.getImage)
        self.route('POST', ('image',), self.importImage)

    def getTCGACollection(self, level=AccessType.READ):
        tcga = self.model('setting').get(
            TCGACollectionSettingKey
        )
        if tcga is None:
            raise RestException(
                'TCGA collection id not initialized in settings',
                code=404
            )
        return self.model('collection').load(
            tcga, level=AccessType.READ, user=self.getCurrentUser()
        )

    @access.public(scope=TokenScope.DATA_READ)
    @describeRoute(
        Description('Get the TCGA collection')
    )
    def getCollection(self, params):
        return self.getTCGACollection()

    @access.admin
    @describeRoute(
        Description('Set the TCGA collection')
        .param('collectionId', 'The id of the collection')
    )
    def setCollection(self, params):
        user = self.getCurrentUser()
        self.requireParams('collectionId', params)

        # this is to ensure the collection exists
        collection = self.model('collection').load(
            id=params['collectionId'], user=user,
            level=AccessType.WRITE, exc=True
        )
        return self.model('setting').set(
            TCGACollectionSettingKey,
            collection['_id']
        )

    @access.public(scope=TokenScope.DATA_READ)
    @describeRoute(
        Description('List cancers in the TCGA dataset')
        .pagingParams(defaultSort='name')
    )
    def findCancer(self, params):
        user = self.getCurrentUser()
        tcga = self.getTCGACollection()
        limit, offset, sort = self.getPagingParameters(params, 'name')

        return list(self.model('cancer', 'digital_slide_archive').childFolders(
            parentType='collection', parent=tcga,
            user=user, offset=offset, limit=limit, sort=sort
        ))

    @access.public(scope=TokenScope.DATA_READ)
    @loadmodel(model='cancer', plugin='digital_slide_archive',
               level=AccessType.READ)
    @describeRoute(
        Description('Get a cancer document from an id')
        .param('id', 'The id of the cancer', paramType='path')
    )
    def getCancer(self, cancer, params):
        return cancer

    @access.admin
    @describeRoute(
        Description('Import a folder as a TCGA cancer type')
        .param('folderId', 'The id of the folder to import')
    )
    def importCancer(self, params):
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        self.requireParams('folderId', params)

        folder = self.model('folder').load(
            id=params['folderId'], user=user,
            level=AccessType.WRITE, exc=True
        )

        cancer = self.model('cancer', 'digital_slide_archive').importDocument(
            folder, user=user, token=token
        )
        return cancer

    @access.public(scope=TokenScope.DATA_READ)
    @describeRoute(
        Description('List cases in the TCGA dataset')
        .param('cancer', 'The id of the cancer document', required=True)
        .pagingParams(defaultSort='name')
    )
    def findCase(self, params):
        user = self.getCurrentUser()
        limit, offset, sort = self.getPagingParameters(params, 'name')
        cancer = self.model('cancer', 'digital_slide_archive').load(
            id=params['cancer'], user=user, level=AccessType.READ,
            exc=True
        )

        return list(self.model('case', 'digital_slide_archive').childFolders(
            parentType='folder', parent=cancer,
            user=user, offset=offset, limit=limit, sort=sort
        ))

    @access.public(scope=TokenScope.DATA_READ)
    @loadmodel(model='case', plugin='digital_slide_archive',
               level=AccessType.READ)
    @describeRoute(
        Description('Get a case document from an id')
        .param('id', 'The id of the case', paramType='path')
    )
    def getCase(self, case, params):
        return case

    @access.admin
    @describeRoute(
        Description('Import a folder as a TCGA case')
        .param('folderId', 'The id of the folder to import')
    )
    def importCase(self, params):
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        self.requireParams('folderId', params)

        folder = self.model('folder').load(
            id=params['folderId'], user=user,
            level=AccessType.WRITE, exc=True
        )

        case = self.model('case', 'digital_slide_archive').importDocument(
            folder, user=user, token=token
        )
        return case

    @access.public(scope=TokenScope.DATA_READ)
    @describeRoute(
        Description('Find slides for a case')
        .param('case', 'The id of case document', required=True)
        .pagingParams(defaultSort='name')
    )
    def findSlide(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'name')
        user = self.getCurrentUser()
        case = self.model('case', 'digital_slide_archive').load(
            id=params['case'], user=user, level=AccessType.READ,
            exc=True
        )
        return list(self.model('slide', 'digital_slide_archive').childFolders(
            parentType='folder', parent=case, user=user,
            offset=offset, limit=limit, sort=sort
        ))

    @access.public(scope=TokenScope.DATA_READ)
    @loadmodel(model='slide', plugin='digital_slide_archive',
               level=AccessType.READ)
    @describeRoute(
        Description('Get a slide document by id')
        .param('id', 'The id of the slide', paramType='path')
    )
    def getSlide(self, slide, params):
        return slide

    @access.admin
    @describeRoute(
        Description('Import a folder as a TCGA slide')
        .param('folderId', 'The id of the folder to import')
    )
    def importSlide(self, params):
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        self.requireParams('folderId', params)

        folder = self.model('folder').load(
            id=params['folderId'], user=user,
            level=AccessType.WRITE, exc=True
        )

        slide = self.model('slide', 'digital_slide_archive').importDocument(
            folder, user=user, token=token
        )
        return slide

    @access.public(scope=TokenScope.DATA_READ)
    @describeRoute(
        Description('Find images for a slide')
        .param('slide', 'The id of slide document', required=True)
        .pagingParams(defaultSort='name')
    )
    def findImage(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'name')
        user = self.getCurrentUser()
        slide = self.model('slide', 'digital_slide_archive').load(
            id=params['slide'], user=user, level=AccessType.READ,
            exc=True
        )
        return list(self.model('image', 'digital_slide_archive').find(
            {'folderId': slide['_id']},
            offset=offset, limit=limit, sort=sort
        ))

    @access.public(scope=TokenScope.DATA_READ)
    @loadmodel(model='image', plugin='digital_slide_archive',
               level=AccessType.READ)
    @describeRoute(
        Description('Get an image document by id')
        .param('id', 'The id of the image', paramType='path')
    )
    def getImage(self, image, params):
        return image

    @access.admin
    @describeRoute(
        Description('Import an item as a TCGA slide image')
        .param('itemId', 'The id of the item to import')
    )
    def importImage(self, params):
        user = self.getCurrentUser()
        token = self.getCurrentToken()
        self.requireParams('itemId', params)

        item = self.model('item').load(
            id=params['itemId'], user=user,
            level=AccessType.WRITE, exc=True
        )

        image = self.model('image', 'digital_slide_archive').importDocument(
            item, user=user, token=token
        )
        return image
