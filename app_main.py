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
    """

    def __init__(self, node_name):
        """
        Initializes a new instance of AppMain.
        """
        self.logger = Logger()
        self.outbound_message_queue = MessageQueue("Outbound")
        self.inbound_message_queue = MessageQueue("Inbound")
        self.hive_node_manager = None
        self.cli_command_processor = None
        self.local_node = self.load_config(node_name)

    def load_config(self, node_name):
        """
        Load configuration from a JSON file.
        """
        with open('hive_config.json', 'r') as file:
            config = json.load(file)
            for node_info in config['nodes']:
                if node_info['friendly_name'] == node_name:
                    return HiveNode(node_info['friendly_name'], node_info['ip_address'], node_info['port'], is_local_node=True)
            raise ValueError(f"No node found with friendly name: {node_name}")

    def run(self):
        """
        Starts the Hive network application by initializing components.
        """
        self.hive_node_manager = HiveNodeManager(self.local_node)

        log_file_name = f"app.{self.local_node.friendly_name.replace(' ', '_')}.log"
        self.logger.set_log_file(log_file_name)

        hive_service = HiveReceiverService(self.local_node.friendly_name, self.local_node.ip_address, self.local_node.port_number, self.hive_node_manager, self.inbound_message_queue, self.outbound_message_queue)
        hive_service_thread = threading.Thread(target=hive_service.run, daemon=True)
        hive_service_thread.start()

        # Initialize other services as needed...

        self.cli_command_processor = CliCommandProcessor(self.hive_node_manager, self.outbound_message_queue, self.inbound_message_queue)
        self.cli_command_processor.set_prompt(f"{self.local_node.friendly_name}> ")
        self.cli_command_processor.command_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start a specific node of the Hive network.')
    parser.add_argument('-friendly_name', required=True, help='Friendly name of the node to run as specified in the configuration file.')
    args = parser.parse_args()

    app = AppMain(args.friendly_name)
    app.run()
