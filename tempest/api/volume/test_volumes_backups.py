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

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging
from tempest.test import attr

LOG = logging.getLogger(__name__)


class VolumesBackupTest(base.BaseVolumeTest):
    _interface = "json"
    
    @classmethod
    def setUpClass(cls):
        super(VolumesBackupTest, cls).setUpClass()
        cls.client = cls.backups_client
        try:
            cls.volume_origin = cls.create_volume()
        except Exception:
            LOG.exception("setup failed")
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        super(VolumesBackupTest, cls).tearDownClass()

    @attr(type='gate')
    def test_backup_create(self):
        # Create a backup
        b_name = data_utils.rand_name('backup')
        resp, backup = self.client.create_backup(self.volume_origin['id'],
                                        name=b_name)
        self.assertEqual(202, resp.status)
        self.assertIn('id', backup)
        self.addCleanup(self.client.delete_backup, backup['id'])
        self.client.wait_for_backup_status(backup['id'], 'available')

    @attr(type='gate')
    def test_backup_list(self):
        # Create a backup
        b_name = data_utils.rand_name('backup')
        resp, backup = self.client.create_backup(self.volume_origin['id'],
                                        name=b_name)
        self.assertEqual(202, resp.status)
        self.assertIn('id', backup)
        self.addCleanup(self.client.delete_backup, backup['id'])
        self.client.wait_for_backup_status(backup['id'], 'available')

        # Compare with the output from the list action
        tracking_data = (backup['id'], backup['name'])
        resp, backs_list = self.client.list_backups()
        self.assertEqual(200, resp.status)
        backs_data = [(f['id'], f['name']) for f in backs_list]
        self.assertIn(tracking_data, backs_data)

    @attr(type='gate')
    def test_backup_get(self):
        # Create a backup
        b_name = data_utils.rand_name('backup')
        resp, backup = self.client.create_backup(self.volume_origin['id'],
                                        name=b_name)
        self.assertEqual(202, resp.status)
        self.assertIn('id', backup)
        self.addCleanup(self.client.delete_backup, backup['id'])
        self.client.wait_for_backup_status(backup['id'], 'available')

        # Get the backup and check for some of its details
        resp, back_get = self.client.get_backup(backup['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(self.volume_origin['id'],
                         back_get['volume_id'],
                         "Referred volume origin mismatch")

    @attr(type='gate')
    def test_backup_delete(self):
        # Create a backup
        b_name = data_utils.rand_name('backup')
        resp, backup = self.client.create_backup(self.volume_origin['id'],
                                        name=b_name)
        self.assertEqual(202, resp.status)
        self.assertIn('id', backup)
        self.client.wait_for_backup_status(backup['id'], 'available')
        
        # Delete backup
        self.client.delete_backup(backup['id'])
        self.client.wait_for_resource_deletion(backup['id'])

    @attr(type='gate')
    def test_backup_restore(self):
        # Create a backup
        b_name = data_utils.rand_name('backup')
        resp, backup = self.client.create_backup(self.volume_origin['id'],
                                        name=b_name)
        self.assertEqual(202, resp.status)
        self.assertIn('id', backup)
        self.addCleanup(self.client.delete_backup, backup['id'])
        self.client.wait_for_backup_status(backup['id'], 'available')
        
        # Restore backup to new volume
        vol_client = self.volumes_client
        resp, restore = self.client.backup_restore(backup['id'])
        self.assertEqual(202, resp.status)
        self.assertIn('volume_id', restore)
        self.addCleanup(vol_client.delete_volume,
                        restore['volume_id'])
        vol_client.wait_for_volume_status(restore['volume_id'],
                                                  'available')

    @attr(type='gate')
    def test_backup_restore_to_volume(self):
        # Create a backup
        b_name = data_utils.rand_name('backup')
        resp, backup = self.client.create_backup(self.volume_origin['id'],
                                        name=b_name)
        self.assertEqual(202, resp.status)
        self.assertIn('id', backup)
        self.addCleanup(self.client.delete_backup, backup['id'])
        self.client.wait_for_backup_status(backup['id'], 'available')

        # Create target volume
        vol_client = self.volumes_client
        t_name = data_utils.rand_name('volume')
        resp, target = vol_client.create_volume(size=1, display_name=t_name)
        self.assertEqual(200, resp.status)
        self.assertIn('id', target)
        self.addCleanup(vol_client.delete_volume, target['id'])
        vol_client.wait_for_volume_status(target['id'], 'available')
        
        # Restore backup to target volume
        resp, restore = self.client.backup_restore(backup['id'],
                                                   volume_id=target['id'])
        self.assertEqual(202, resp.status)
        self.assertIn('volume_id', restore)
        self.assertEqual(target['id'], restore['volume_id'])
        vol_client.wait_for_volume_status(restore['volume_id'],
                                                  'available')

class VolumesBackupTestXML(VolumesBackupTest):
    _interface = "xml"
