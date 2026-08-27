from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, Signal, Slot
from src.core.domain import DomainWorkItem
from typing import List

class WorkItemListModel(QAbstractListModel):
    """
    Native Qt Model acting as a bridge between pure DomainWorkItems 
    and the PySide6 UI. Ensures fast, lazy rendering of 10,000+ items.
    """
    
    # Custom roles for the UI to access data
    TitleRole = Qt.ItemDataRole.UserRole + 1
    StatusRole = Qt.ItemDataRole.UserRole + 2
    TypeRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, workitems: List[DomainWorkItem] = None, parent=None):
        super().__init__(parent)
        self._workitems = workitems or []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._workitems)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if not 0 <= index.row() < len(self._workitems):
            return None

        item = self._workitems[index.row()]

        if role == Qt.ItemDataRole.DisplayRole or role == self.TitleRole:
            return item.title
        elif role == self.StatusRole:
            return item.state
        elif role == self.TypeRole:
            return item.item_type
            
        return None

    def roleNames(self):
        roles = super().roleNames()
        roles[self.TitleRole] = b'title'
        roles[self.StatusRole] = b'status'
        roles[self.TypeRole] = b'item_type'
        return roles

    def update_data(self, new_workitems: List[DomainWorkItem]):
        """
        Safely swap data while notifying the view.
        """
        self.beginResetModel()
        self._workitems = new_workitems
        self.endResetModel()

    def get_item(self, index: int) -> DomainWorkItem:
        if 0 <= index < len(self._workitems):
            return self._workitems[index]
        return None
