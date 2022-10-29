from __future__ import annotations
from typing import Dict, Generic, List, overload,  Optional

from .utils import debug
from .nodeWidget import NodeWidget, NodeVlayout
from .dataModel import DataGraph, DataItemAbstract, GraphNode, DataItemT, uidT
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget
from PyQt6 import QtCore

class CollapsibleCheckList(QWidget, Generic[DataItemT]):

    onCheckItem = QtCore.pyqtSignal(DataItemAbstract)
    onUnCheckItem = QtCore.pyqtSignal(DataItemAbstract)

    onHoverEnter = QtCore.pyqtSignal(DataItemAbstract)
    onHoverLeave = QtCore.pyqtSignal(DataItemAbstract)

    onCollapseNode = QtCore.pyqtSignal(GraphNode)
    onUnCollapseNode = QtCore.pyqtSignal(GraphNode)

    onHoverEnterNodeWidget = QtCore.pyqtSignal(NodeWidget)
    onHoverLeaveNodeWidget = QtCore.pyqtSignal(NodeWidget)

    onCollapseNodeWidget = QtCore.pyqtSignal(NodeWidget)
    onUnCollapseNodeWidget = QtCore.pyqtSignal(NodeWidget)

    def __init__(self, parent = None, init_items: List[DataItemT] = [], init_check_status : Optional[List[bool]] = None) -> None:
        super().__init__(parent)

        # attributes will be accessed by CheckItemWidget
        self.check_status: Dict[uidT, bool] = {}
        self.shown_item_wids: Dict[uidT, List[NodeWidget]] = {}
        self.root_node_wids: List[NodeWidget] = []
        self._hovering_wid: Optional[NodeWidget] = None

        self.initUI()
        self.initData(init_items, init_check_status)
    
    def initUI(self):
        layout = QVBoxLayout()
        container = QWidget(self)
        container.setLayout(layout)

        self.vlayout = NodeVlayout()
        layout.addLayout(self.vlayout)
        layout.addStretch()

        scroll = QScrollArea(self)
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        _lo = QVBoxLayout()
        _lo.addWidget(scroll)
        self.setLayout(_lo)
    
    def initData(self, init_items: List[DataItemT], init_check_status : Optional[List[bool]] = None):
        if init_check_status is None:
            init_check_status = [False for _ in init_items]
        assert len(init_items) == len(init_check_status)

        # maybe flush old data references
        # may not clean wid if it's not attached to root node
        if self.root_node_wids != []:
            _t = [wid for wid in self.root_node_wids]
            for _w in _t: 
                _w.removeSelf()
        self.check_status = {}
        self._hovering_wid = None

        self.graph = DataGraph(init_items)

        for d, status in zip(init_items, init_check_status):
            # import pdb;pdb.set_trace()
            self.check_status[d.dataitem_uid] = status
            self.shown_item_wids[d.dataitem_uid] = []

        for n in self.graph.nodes:
            if n.parents == []:
                wid = self._createNodeWid(n)
                self.root_node_wids.append(wid)
                self.vlayout.addWidget(wid)

    def _createNodeWid(self, node: GraphNode[DataItemT]) -> NodeWidget[DataItemT]:
        wid = NodeWidget(self, node)
        self.shown_item_wids[node.value.dataitem_uid].append(wid)
        return wid

    def addItem(self, i: DataItemT, check_status: bool = False):
        debug("Add item - {}".format(i))
        self.graph.add(i)

        self.check_status[i.dataitem_uid] = check_status
        self.shown_item_wids.setdefault(i.dataitem_uid, [])

        last_node = self.graph.nodes[-1]
        if last_node.parents == []:
            # root node
            wid = self._createNodeWid(last_node)
            self.root_node_wids.append(wid)
            self.vlayout.addWidget(wid)
        else:
            for wid in self.root_node_wids:
                wid.onNodeUpdate()

    def removeItem(self, i: DataItemT):
        pop_node = self.graph.remove(i)
        if pop_node is None:
            return
        for wid in self.root_node_wids:
            wid.onNodeUpdate()
        

    @property
    def item_hover(self) -> Optional[DataItemT]:
        if self._hovering_wid is None:
            return None
        else: return self._hovering_wid.node.value

    @property
    def items_all(self) -> List[DataItemT]:
        return [d for d in self.graph.data]

    @property
    def items_checked(self) -> List[DataItemT]:
        ret = []
        for i in self.graph.data:
            if self.check_status[i.dataitem_uid]:
                ret.append(i)
        return ret

    @property
    def items_unchecked(self) -> List[DataItemT]:
        ret = []
        for i in self.graph.data:
            if not self.check_status[i.dataitem_uid]:
                ret.append(i)
        return ret

    def setItemChecked(self, data: DataItemT, status: bool):
        assert data.dataitem_uid in self.shown_item_wids.keys(), "Invalid data"
        self.check_status[data.dataitem_uid] = status
        for wid in self.shown_item_wids[data.dataitem_uid]:
            wid.setChecked(status)
            break

    @overload
    def isItemChecked(self, a: int) -> bool: ...
    @overload
    def isItemChecked(self, a: DataItemT) -> bool: ...
    def isItemChecked(self, a) -> bool:
        if isinstance(a, int):
            data = self.graph.data[a]
        else:
            data = a
        return self.check_status[data.dataitem_uid]

