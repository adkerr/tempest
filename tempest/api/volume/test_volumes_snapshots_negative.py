# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import uuid

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class VolumesSnapshotNegativeTest(base.BaseVolumeTest):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumesSnapshotNegativeTest, cls).setUpClass()
        cls.client = cls.volumes_client

    @attr(type=['negative', 'gate'])
    def test_create_snapshot_with_nonexistent_volume_id(self):
        # Create a snapshot with nonexistent volume id
        s_name = data_utils.rand_name('snap')
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.create_snapshot,
                          str(uuid.uuid4()), display_name=s_name)

    @attr(type=['negative', 'gate'])
    def test_create_snapshot_without_passing_volume_id(self):
        # Create a snapshot without passing volume id
        s_name = data_utils.rand_name('snap')
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.create_snapshot,
                          None, display_name=s_name)

    @attr(type=['negative', 'gate'])
    def test_delete_volume_with_dependent_snapshot(self):
        # Should not be able to delete volume with a child snapshot
        volume = {}
        v_name = data_utils.rand_name('Volume-')
        s_name = data_utils.rand_name('Snap-')
        # Create volume
        resp, volume = self.client.create_volume(size=1,
                                                 display_name=v_name)
        self.assertEqual(200, resp.status)
        self.assertIn('id', volume)
        self.addCleanup(self.client.delete_volume, volume['id'])
        self.client.wait_for_volume_status(volume['id'], 'available')
        # Create snapshot
        resp, snapshot = self.client.create_snapshot(volume['id'],
                                                     display_name=s_name)
        self.assertEqual(200, resp.status)
        self.assertIn('id', snapshot)
        self.addCleanup(self.client.delete_snapshot, snapshot['id'])
        self.assertRaises(exceptions.BadRequest, self.client.delete_volume, '')


class VolumesSnapshotNegativeTestXML(VolumesSnapshotNegativeTest):
    _interface = "xml"
