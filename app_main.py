import argparse
import threading
import json
from logger import Logger
from hive_node import HiveNode
from message_queue import MessageQueue
from hive_node_manager import HiveNodeManager
from hive_receiver_service import HiveReceiverService
from hive_sender_client import HiveSenderClient
from cli_command_processor import CliCommandProcessor
from inbound_queue_command_processor import InboundQueueCommandProcessor
from gossip_protocol_command_manager import GossipProtocolCommandManager
from heartbeat_protocol_command_manager import HeartbeatProtocolCommandManager
from app_settings import AppSettings

class AppMain:
    """
    AppMain is the main entry point for the Hive network application.
    Initializes and manages various components based on the configuration loaded from a JSON file.
    """

    def __init__(self, node_name):
        """
        Initializes a new instance of AppMain.
        """
        self.logger = Logger()
        self.outbound_message_queue = MessageQueue("Outbound")
        self.inbound_message_queue = MessageQueue("Inbound")
        self.load_config(node_name)

    def load_config(self, node_name):
        """
        Load node configuration from a JSON file.
        """
        with open('hive_config.json', 'r') as file:
            config = json.load(file)
            node_config = next((item for item in config["nodes"] if item["friendly_name"] == node_name), None)
            if not node_config:
                raise ValueError(f"No configuration found for node {node_name}")
            self.local_node = HiveNode(node_config['friendly_name'], node_config['ip_address'], node_config['port'], is_local_node=True)
            self.hive_node_manager = HiveNodeManager(self.local_node)

    def run(self):
        """
        Starts the Hive network application by initializing various components.
        """
        log_file_name = f"app.{self.local_node.friendly_name.replace(' ', '_')}.log"
        self.logger.set_log_file(log_file_name)
        
        # Initialize network services
        hive_service = HiveReceiverService(self.local_node.friendly_name, self.local_node.ip_address, self.local_node.port_number, self.hive_node_manager, self.inbound_message_queue, self.outbound_message_queue)
        hive_service_thread = threading.Thread(target=hive_service.run, daemon=True)
        hive_service_thread.start()

        hive_client = HiveSenderClient(self.outbound_message_queue, self.inbound_message_queue)
        hive_client_thread = threading.Thread(target=hive_client.run, daemon=True)
        hive_client_thread.start()

        inbound_queue_command_processor = InboundQueueCommandProcessor(self.hive_node_manager, self.outbound_message_queue, self.inbound_message_queue)
        inbound_queue_command_processor_thread = threading.Thread(target=inbound_queue_command_processor.run, daemon=True)
        inbound_queue_command_processor_thread.start()

        gossip_protocol_command_manager = GossipProtocolCommandManager(self.hive_node_manager, self.outbound_message_queue)
        gossip_protocol_command_manager_thread = threading.Thread(target=gossip_protocol_command_manager.run, daemon=True)
        gossip_protocol_command_manager_thread.start()

        heartbeat_protocol_command_manager = HeartbeatProtocolCommandManager(self.hive_node_manager, self.outbound_message_queue)
        heartbeat_protocol_command_manager_thread = threading.Thread(target=heartbeat_protocol_command_manager.run, daemon=True)
        heartbeat_protocol_command_manager_thread.start()

        # CLI for interaction
        self.cli_command_processor = CliCommandProcessor(self.hive_node_manager, self.outbound_message_queue, self.inbound_message_queue)
        self.cli_command_processor.set_prompt(f"{self.local_node.friendly_name}> ")
        self.cli_command_processor.command_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a specific node of the Hive network.')
    parser.add_argument('-friendly_name', required=True, help='Friendly name of the node to run.')
    args = parser.parse_args()

    app = AppMain(args.friendly_name)
    app.run()
