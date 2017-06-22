#
# Copyright 2017 the original author or authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Adapter abstract base class
"""

import structlog
from zope.interface import implementer
from twisted.internet import reactor

from voltha.protos.device_pb2 import DeviceType, DeviceTypes
from voltha.adapters.interface import IAdapterInterface
from voltha.protos.adapter_pb2 import Adapter
from voltha.protos.adapter_pb2 import AdapterConfig
from voltha.protos.common_pb2 import LogLevel
from voltha.protos.health_pb2 import HealthStatus

log = structlog.get_logger()

@implementer(IAdapterInterface)
class IAdapter(object):
    def __init__(self, adapter_agent, config, device_handler_class, name, vendor, version):
        log.debug('Initializing adapter: {} {} {}'.format(vendor, name, version))
        self.adapter_agent = adapter_agent
        self.config = config
        self.name = name
        self.supported_device_types = [
            DeviceType(
                id=name,
                adapter=name,
                accepts_bulk_flow_update=True
            )
        ]
        self.descriptor = Adapter(
            id=self.name,
            vendor=vendor,
            version=version,
            config=AdapterConfig(log_level=LogLevel.INFO)
        )
        self.devices_handlers = dict()  # device_id -> Olt/OnuHandler()
        self.device_handler_class = device_handler_class

    def start(self):
        log.info('Starting adapter: {}'.format(self.name))

    def stop(self):
        log.info('Stopping adapter: {}'.format(self.name))

    def adapter_descriptor(self):
        return self.descriptor

    def device_types(self):
        return DeviceTypes(items=self.supported_device_types)

    def health(self):
        return HealthStatus(state=HealthStatus.HealthState.HEALTHY)

    def change_master_state(self, master):
        raise NotImplementedError()

    def update_pm_config(self, device, pm_config):
        raise NotImplementedError()

    def adopt_device(self, device):
        self.devices_handlers[device.id] = self.device_handler_class(self, device.id)
        reactor.callLater(0, self.devices_handlers[device.id].activate, device)
        return device

    def reconcile_device(self, device):
        raise NotImplementedError()

    def abandon_device(self, device):
        raise NotImplementedError()

    def disable_device(self, device):
        log.info('disable-device', device_id=device.id)
        reactor.callLater(0, self.devices_handlers[device.id].disable)
        return device

    def reenable_device(self, device):
        log.info('reenable-device', device_id=device.id)
        reactor.callLater(0, self.devices_handlers[device.id].reenable)
        return device

    def reboot_device(self, device):
        log.info('reboot-device', device_id=device.id)
        reactor.callLater(0, self.devices_handlers[device.id].reboot)
        return device

    def delete_device(self, device):
        log.info('delete-device', device_id=device.id)
        #  TODO: Update the logical device mapping
        reactor.callLater(0, self.devices_handlers[device.id].delete)
        return device

    def get_device_details(self, device):
        raise NotImplementedError()

    def update_flows_bulk(self, device, flows, groups):
        log.info('bulk-flow-update', device_id=device.id,
                 flows=flows, groups=groups)
        assert len(groups.items) == 0
        handler = self.devices_handlers[device.id]
        return handler.update_flow_table(flows.items)

    def update_flows_incrementally(self, device, flow_changes, group_changes):
        raise NotImplementedError()

    def send_proxied_message(self, proxy_address, msg):
        log.info('send-proxied-message', proxy_address=proxy_address, msg=msg)
        handler = self.devices_handlers[proxy_address.device_id]
        handler.send_proxied_message(proxy_address, msg)

    def receive_proxied_message(self, proxy_address, msg):
        raise NotImplementedError()

    def receive_packet_out(self, logical_device_id, egress_port_no, msg):
        raise NotImplementedError()

    def receive_inter_adapter_message(self, msg):
        raise NotImplementedError()

    def suppress_alarm(self, filter):
        raise NotImplementedError()

    def unsuppress_alarm(self, filter):
        raise NotImplementedError()