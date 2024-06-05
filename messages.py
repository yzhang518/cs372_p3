# messages.py

from base_message import BaseMessage

class UpdateConfigMessage(BaseMessage):
    def __init__(self, sender, recipient, new_config):
        super().__init__(sender, recipient, 'update_config')
        self.new_config = new_config

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({'new_config': self.new_config})
        return base_dict

    @staticmethod
    def from_dict(data):
        return UpdateConfigMessage(data['sender'], data['recipient'], data['new_config'])

class ServiceStatusMessage(BaseMessage):
    def __init__(self, sender, recipient, service_status):
        super().__init__(sender, recipient, 'service_status')
        self.service_status = service_status

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({'service_status': self.service_status})
        return base_dict

    @staticmethod
    def from_dict(data):
        return ServiceStatusMessage(data['sender'], data['recipient'], data['service_status'])
