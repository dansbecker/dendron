from .basic_types import NodeType, NodeStatus
from .tree_node import NodeConfig, TreeNode

class DecoratorNode(TreeNode):

    def __init__(self, name, cfg):
        super().__init__(name, cfg)

        self.child_node : TreeNode = Node 

    def set_child(self, child):
        self.child_node = child

    def get_child(self):
        return self.child_node

    def halt_child(self):
        pass # TODO

    def reset_child(self):
        pass # TODO