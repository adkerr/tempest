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

import time
import urllib

from lxml import etree

from tempest.common.rest_client import RestClientXML
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.services.compute.xml.common import Document
from tempest.services.compute.xml.common import Element
from tempest.services.compute.xml.common import xml_to_json
from tempest.services.compute.xml.common import XMLNS_11

LOG = logging.getLogger(__name__)


class BackupsClientXML(RestClientXML):
    """Client class to send CRUD Volume API requests."""

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(BackupsClientXML, self).__init__(config, username, password,
                                                 auth_url, tenant_name)

        self.service = self.config.volume.catalog_type
        self.build_interval = self.config.volume.build_interval
        self.build_timeout = self.config.volume.build_timeout

    def create_snapshot(self, volume_id, **kwargs):
        """Creates a new backup.
        volume_id(Required): id of the volume.
        container: Optional backup container name.
        name: Optional backup name.
        description: Optional backup description.
        """
        backup = Element("backup", xmlns=XMLNS_11, volume_id=volume_id)
        for key, value in kwargs.items():
            backup.add_attr(key, value)
        resp, body = self.post('backups', str(Document(backup)),
                               self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def list_backups(self):
        """List all backups."""
        url = 'backups'
        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        backups = []
        for back in body:
            backups.append(xml_to_json(back))
        return resp, backups

    def list_backups_with_detail(self):
        """List details of all the backups created."""
        url = 'backups/detail'
        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        backups = []
        for back in body:
            backups.append(xml_to_json(back))
        return resp, backups

    def get_backup(self, backup_id):
        """Returns the details of a single backup."""
        url = "backups/%s" % str(backup_id)
        resp, body = self.get(url, self.headers)
        body = etree.fromstring(body)
        return resp, xml_to_json(body)

    def restore_backup(self, backup_id, **kwargs):
        """
        Restores a backup.
        backup_id(Required): Backup to be restored.
        Following optional keyword argument is accepted:
        volume_id: Optional volume to restore to.
        """
        restore = Element("restore", xmlns=XMLNS_11)
        for key, value in kwargs.items():
            restore.add_attr(key, value)
        resp, body = self.post('backups/%s/restore' % str(backup_id),
                               str(Document(restore)),
                               self.headers)
        body = xml_to_json(etree.fromstring(body))
        return resp, body

    def delete_backup(self, backup_id):
        """Delete Backup."""
        return self.delete("backups/%s" % str(backup_id))

    def _get_backup_status(self, backup_id):
        resp, body = self.get_backup(backup_id)
        status = body['status']
        if (status == 'error'):
            raise exceptions.BackupBuildErrorException(
                backup_id=backup_id)

        return status

    def wait_for_backup_status(self, backup_id, status):
        """Waits for a Backup to reach a given status."""
        start_time = time.time()
        old_value = value = self._get_backup_status(backup_id)
        while True:
            dtime = time.time() - start_time
            time.sleep(self.build_interval)
            if value != old_value:
                LOG.info('Value transition from "%s" to "%s"'
                         'in %d second(s).', old_value,
                         value, dtime)
            if (value == status):
                return value

            if dtime > self.build_timeout:
                message = ('Time Limit Exceeded! (%ds)'
                           'while waiting for %s, '
                           'but we got %s.' %
                           (self.build_timeout, status, value))
                raise exceptions.TimeoutException(message)
            time.sleep(self.build_interval)
            old_value = value
            value = self._get_backup_status(backup_id)

    def is_resource_deleted(self, id):
        try:
            self.get_backup(id)
        except exceptions.NotFound:
            return True
        return False