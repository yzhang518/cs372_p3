import random
from typing import List, Optional
from logger import Logger
from hive_node import HiveNode
from app_settings import AppSettings
import datetime


class HiveNodeManager:
    """
    HiveNodeManager is responsible for managing the list of nodes in the network.
    It provides methods to add, remove, and list nodes, as well as to get random live nodes.

    Attributes:
    ----------
    logger : Logger
        An instance of the Logger class for logging messages.
    hive_nodes : List[HiveNode]
        The list of nodes in the network.
    local_node : HiveNode
        The local node instance managed by this manager.
    """

    def __init__(self, local_node: HiveNode):
        """
        Initializes a new instance of HiveNodeManager.

        Parameters:
        ----------
        local_node : HiveNode
            The local node instance managed by this manager.
        """
        self.logger: Logger = Logger()
        self.hive_nodes: List[HiveNode] = []
        self.local_node: HiveNode = local_node
        self.add_node(local_node)

        # Load nodes from the configuration file
        self.load_config("hive_config.json")
        self.status_check()

        self.logger.debug("HiveNodeManager", "HiveNodeManager initialized...")

    def add_node(self, new_node: HiveNode) -> None:
        """
        Adds a new node to the list of nodes. If the node already exists, it updates the node's friendly name.

        Parameters:
        ----------
        new_node : HiveNode
            The node to be added to the list.
        """
        existing_node: Optional[HiveNode] = self.get_node_by_ip_address_and_port(new_node.ip_address, new_node.port_number)

        if existing_node:
            self.logger.info("HiveNodeManager", f"Node {new_node.friendly_name} already exists in the node list...")
            self.logger.debug("HiveNodeManager", f"Updating node {existing_node.ip_address}:{existing_node.port_number} from {existing_node.friendly_name} to {new_node.friendly_name}...")
            existing_node.friendly_name = new_node.friendly_name
        else:
            self.logger.info("HiveNodeManager", f"Node {new_node.friendly_name} does not exist in the node list...")
            self.hive_nodes.append(new_node)

    def remove_node(self, node_to_remove: HiveNode) -> None:
        """
        Removes a node from the list of nodes.

        Parameters:
        ----------
        node_to_remove : HiveNode
            The node to be removed from the list.
        """
        self.hive_nodes = [node for node in self.hive_nodes if not (node.ip_address == node_to_remove.ip_address and node.port_number == node_to_remove.port_number)]

    def list_nodes(self) -> None:
        """
        Logs the list of nodes in the network, including their details.
        """
        col_widths = {
            'friendly_name': max(len(HiveNode.headers['friendly_name']), max(len(node.friendly_name) for node in self.hive_nodes)) + 1, # +1 for * indicating local node
            'ip_address': max(len(HiveNode.headers['ip_address']), max(len(node.ip_address) for node in self.hive_nodes)),
            'port': max(len(HiveNode.headers['port']), max(len(str(node.port_number)) for node in self.hive_nodes)),
            'status': max(len(HiveNode.headers['status']), max(len(node.status) for node in self.hive_nodes)),
            'last_heartbeat': max(len(HiveNode.headers['last_heartbeat']), max(len(str(node.last_heartbeat_timestamp)) for node in self.hive_nodes)),
            'Failed Connections': max(len('Failed Connections'), max(len(str(node.failed_connection_count)) for node in self.hive_nodes)),
        }

        self.logger.info("HiveNodeManager", "-" * AppSettings.LOG_LINE_WIDTH)
        self.logger.info("HiveNodeManager", self.local_node.get_node_list_row_header_as_str(col_widths))
        self.logger.info("HiveNodeManager", self.local_node.get_node_list_row_separator_as_str(col_widths))

        for node in self.hive_nodes:
            self.logger.info("HiveNodeManager", node.get_node_list_row_as_str(col_widths))
        self.logger.info("HiveNodeManager", "-" * AppSettings.LOG_LINE_WIDTH)

    def get_random_live_node(self) -> Optional[HiveNode]:
        """
        Returns a random live node from the list of nodes, excluding the local node.

        Returns:
        -------
        Optional[HiveNode]
            A random live node, or None if no live nodes are available.
        """
        live_nodes: List[HiveNode] = [node for node in self.hive_nodes if node.status == "Live"]
        live_nodes = [node for node in live_nodes if node != self.local_node]

        if len(live_nodes) > 0:
            random_node_index = random.randint(0, len(live_nodes) - 1)
            return live_nodes[random_node_index]
        return None

    def get_node_by_ip_address_and_port(self, source_ip_address: str, source_port: int) -> Optional[HiveNode]:
        """
        Returns the node with the specified IP address and port, or None if no such node exists.

        Parameters:
        ----------
        source_ip_address : str
            The IP address of the node to be retrieved.
        source_port : int
            The port number of the node to be retrieved.

        Returns:
        -------
        Optional[HiveNode]
            The node with the specified IP address and port, or None if no such node exists.
        """
        source_node: HiveNode = HiveNode("temp", source_ip_address, source_port)

        for node in self.hive_nodes:
            if node == source_node:
                return node
        return None

    def get_all_live_nodes(self) -> List[HiveNode]:
        """
        Returns a list of all live nodes in the network.

        Returns:
        -------
        List[HiveNode]
            A list of all live nodes.
        """
        return [node for node in self.hive_nodes if node.status == "Live"]

    def load_config(self, config_file: str) -> None:
        import json
        try:
            with open(config_file, 'r') as file:
                nodes_config = json.load(file)
                for node_info in nodes_config:
                    if "services" not in node_info:
                        node_info["services"] = {}
                        self.logger.info("HiveNodeManager", "empty services.")
                    new_node = HiveNode(node_info["friendly_name"], node_info["ip_address"], node_info["port_number"], node_info["status"], node_info["services"])
                    self.logger.info("HiveNodeManager", "services here??")
                    self.add_node(new_node)
                    self.logger.info("HiveNodeManager", f"Loaded node {node_info['friendly_name']} with services: {node_info['services']}")
            self.logger.info("HiveNodeManager", "Configuration loaded successfully.")
        except Exception as e:
            self.logger.error("HiveNodeManager", f"Failed to load configuration: {str(e)}")


    def find_node_by_friendly_name(self, local_node):
        """Finds a node by its friendly name."""
        for node in self.hive_nodes:
            self.logger.debug("HiveNodeManager", f"Checking {node.friendly_name} against {local_node.friendly_name}")
            if node.friendly_name == local_node.friendly_name:
                return node
        return None

    def status_check(self):
        hive = self.find_node_by_friendly_name(self.local_node)
        if hive:
            self.logger.info("HiveNodeManager", f"Performing status check on {hive.friendly_name}.")
            if hive.services:
                for service_key, service_values in hive.services.items():
                    self.logger.info("HiveNodeManager", f"{hive.friendly_name} service {service_key}: {service_values}")
            else:
                self.logger.info("HiveNodeManager", f"No services configured for {hive.friendly_name}.")
        else:
            self.logger.error("HiveNodeManager", "Local node not found in the list.")

