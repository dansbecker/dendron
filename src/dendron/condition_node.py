from .basic_types import NodeType, NodeStatus
from .tree_node import TreeNode

from typing import Optional

import logging

class ConditionNode(TreeNode):
    def __init__(self, name) -> None:
        super().__init__(name)

    def set_logger(self, new_logger) -> None:
        self.logger = new_logger

    def set_log_level(self, new_level) -> None:
        self.log_level = new_level

    def node_type(self) -> NodeType:
        return NodeType.CONDITION

    def get_node_by_name(self, name : str) -> Optional[TreeNode]:
        if self.name == name:
            return self
        else:
            return None

    def pretty_repr(self, depth = 0) -> str:
        tabs = '\t'*depth
        repr = f"{tabs}Condition {self.name}"
        return repr
