# app_main.py

import argparse
import threading
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
import config  # Ensure this contains the initial service checks configuration

class AppMain:
    """
    AppMain is the main entry point for the Hive network application.
    """

    def __init__(self):
        """
        Initializes a new instance of AppMain.
        """
        self.logger = Logger()
        self.outbound_message_queue = MessageQueue("Outbound")
        self.inbound_message_queue = MessageQueue("Inbound")
        self.hive_node_manager = None

    def run(self):
        """
        Starts the Hive network application by parsing arguments, setting up the local node,
        and initializing various components.
        """
        parser = argparse.ArgumentParser(description='Start a TCP server.')
        parser.add_argument('-ip', type=str, default=AppSettings.DEFAULT_IP_ADDRESS, help='IP address to bind the server')
        parser.add_argument('-port', type=int, default=AppSettings.DEFAULT_PORT_NUMBER, help='Port to bind the server')
        parser.add_argument('-friendly_name', type=str, default=AppSettings.DEFAULT_FRIENDLY_NAME, help='Friendly name for the local node')
        args = parser.parse_args()

        # Set the log file name based on the friendly_name
        log_file_name = f"app.{args.friendly_name.replace(' ', '_')}.log"
        self.logger.set_log_file(log_file_name)

        # Load initial service checks from config.py
        initial_service_checks = config.server_configs.get(args.friendly_name, [])

        # Create a local node with service checks
        local_node = HiveNode(args.friendly_name, args.ip, args.port, is_local_node=True, service_checks=initial_service_checks)
        self.hive_node_manager = HiveNodeManager(local_node)

        # Start various services and threads
        self.start_services(local_node)

        # Start CLI Command Processor
        self.start_cli(local_node)

    def start_services(self, local_node):
        """
        Starts the network services required for the application.
        """
        hive_service = HiveReceiverService(local_node.friendly_name, local_node.ip_address, local_node.port_number, self.hive_node_manager, self.inbound_message_queue, self.outbound_message_queue)
        threading.Thread(target=hive_service.run, daemon=True).start()

        hive_client = HiveSenderClient(self.outbound_message_queue, self.inbound_message_queue)
        threading.Thread(target=hive_client.run, daemon=True).start()

        inbound_processor = InboundQueueCommandProcessor(self.hive_node_manager, self.outbound_message_queue, self.inbound_message_queue)
        threading.Thread(target=inbound_processor.run, daemon=True).start()

        gossip_manager = GossipProtocolCommandManager(self.hive_node_manager, self.outbound_message_queue)
        threading.Thread(target=gossip_manager.run, daemon=True).start()

        heartbeat_manager = HeartbeatProtocolCommandManager(self.hive_node_manager, self.outbound_message_queue)
        threading.Thread(target=heartbeat_manager.run, daemon=True).start()

    def start_cli(self, local_node):
        """
        Initializes and starts the CLI command processor.
        """
        self.cli_command_processor = CliCommandProcessor(self.hive_node_manager, self.outbound_message_queue, self.inbound_message_queue)
        self.cli_command_processor.set_prompt(f"{local_node.friendly_name}> ")
        self.cli_command_processor.command_loop()

if __name__ == "__main__":
    app = AppMain()
    app.run()
