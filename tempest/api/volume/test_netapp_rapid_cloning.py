# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import os.path
import subprocess

import netapp

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging
from tempest.test import attr

LOG = logging.getLogger(__name__)

class RapidCloningTest(base.BaseVolumeTest):

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(RapidCloningTest, cls).setUpClass()
        cls.client = cls.volumes_client
        cls.image_client = cls.os.image_client
        cls.mounts = []
        
        # Create a shared image
        vol_name = data_utils.rand_name(cls.__name__ + '-Volume')
        resp, cls.volume = cls.client.create_volume(size=1,
                                                    display_name=vol_name)
        cls.client.wait_for_volume_status(cls.volume['id'], 'available')
        
        image_name = data_utils.rand_name('Image')
        resp, cls.image = cls.client.upload_volume(cls.volume['id'],
                                               image_name,
                                               cls.config.volume.disk_format)
        cls.image_id = cls.image["image_id"]
        cls.image_client.wait_for_image_status(cls.image_id, 'active')
        cls.client.wait_for_volume_status(cls.volume['id'], 'available')
        
        # Grab mount locations
        mount = subprocess.check_output("mount | grep nfs | grep cinder")
        # subprocess.check_output returns byte string
        mount = mount.decode("utf-8")
        mountlines = mount.splitlines()
        for line in mountlines:
            cls.mounts.append(line.split()[2])
        
    @classmethod
    def tearDownClass(cls):
        # Delete the test image and volume
        cls.image_client.delete_image(cls.image_id)
        cls.image_client.wait_for_resource_deletion(cls.image_id)
        cls.client.delete_volume(cls.volume['id'])
        cls.client.wait_for_resource_deletion(cls.volume['id'])
        
        super(RapidCloningTest, cls).tearDownClass()

    def test_create_volume_from_image(self):
        # A local copy of the image should be created on NFS share
        vol_name = data_utils.rand_name('Volume')
        resp, body = self.client.create_volume(size=1,
                                               display_name=vol_name,
                                               image_id=self.image_id)
        self.assertEqual(202, resp.status)
        self.addCleanUp(self.client.delete_volume, body['id'])
        self.client.wait_for_volume_status(body['id'], 'available')
        # Search the nfs mounts for the cached image
        found = False
        for mount in self.mounts:
            if os.path.isfile(mount + '/img-cache-' + self.image_id):
                found = True
                break
        self.assertTrue(found)

class RapidCloningTestXML(RapidCloningTest):
    
    _interface = 'xml'