import socket
import time

from PyQt5.QtCore import QThread, pyqtSignal
from p2pnetwork.node import Node
from p2pnetwork.nodeconnection import NodeConnection

from misc import gen_uuid


class TTT_Node(Node):
    def __init__(self, host: str = '', port: int = 1234, _id=None, msg_callback=None):
        super(TTT_Node, self).__init__(host, port, _id)
        self.msg_callback = msg_callback
        self.debug = True

    def create_new_connection(self, connection, _id, host, port):
        return TTT_Connection(self, connection, _id, host, port)

    def node_message(self, node, data):
        # print(f"<{self.id}> received \"{str(data)}\" from <{node.id}>")
        if self.msg_callback is not None and callable(self.msg_callback):
            self.msg_callback(node, data)

    def outbound_node_connected(self, node):
        print(f"<{self.id}> connected with <{node.id}>")

    def inbound_node_connected(self, node):
        print(f"<{self.id}> received connection from <{node.id}>")


class TTT_Connection(NodeConnection):
    def __init__(self, main_node, sock, _id, host, port):
        super(TTT_Connection, self).__init__(main_node, sock, _id, host, port)


class TTT_Message:
    @classmethod
    def SET(cls, row: int, col: int) -> str | None:
        if isinstance(row, int) and isinstance(col, int):
            return f"SET {row} {col}"

    GREET = "Hello from TTT"


class TTT_Conn(QThread):
    # todo!! :: change send_to_nodes to send_to_node
    msg_received = pyqtSignal(str)
    new_connection = pyqtSignal()
    set_received = pyqtSignal(str, str)

    def __init__(self, port=2222):
        super(TTT_Conn, self).__init__()
        self.node = Node('', port, callback=self.conn_callback, id=gen_uuid())
        self.node.debug = False
        self.start_conn()

    def conn_callback(self, event: str, node: Node | None, connected_node: Node, data: dict):
        match event:
            case 'node_message':
                msg = str(data)
                self.msg_received.emit(msg)
                if msg.startswith("SET"):
                    _, row, col = msg.split(" ")
                    self.set_received.emit(row, col)
            case 'outbound_node_connected':
                pass
            case 'inbound_node_connected':
                self.new_connection.emit()
            case 'outbound_node_disconnected':
                pass
            case 'inbound_node_disconnected':
                pass
            case _:
                pass

    def start_conn(self): self.node.start()
    def stop_conn(self): self.node.stop()
    def greet(self): self.node.send_to_nodes(TTT_Message.GREET)
    def send_set(self, row, col): self.node.send_to_nodes(TTT_Message.SET(row, col))


if __name__ == '__main__':
    conn1 = TTT_Conn(2222)
    conn2 = TTT_Conn(3333)

    conn1.node.connect_with_node("127.0.0.1", 3333)
    conn1.node.send_to_nodes("hello!")

    time.sleep(5)

    conn1.node.stop()
    conn2.node.stop()
