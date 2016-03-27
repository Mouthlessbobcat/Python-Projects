import sys
from PySide import QtGui, QtCore
import milk.lib.qt.contextmenu as qt_contextmenu

# Declare context menus by subclassing BaseContextMenuTree
class LeftViewContextMenu(qt_contextmenu.BaseContextMenuTree):
    pass


class RightViewContextMenu(qt_contextmenu.BaseContextMenuTree):
    pass


class SelectionManager(object):
    """
    Holds reference to selected items in tree widgets.
    """

    def __init__(self):
        self.left_selection = []
        self.right_selection = []


@LeftViewContextMenu.register_widget
class SearchField(QtGui.QLineEdit):
    """
    A dummy subclass of a widget to demonstrate
    the class decorator for attaching a context menu.
    """

    def __init__(self, *args, **kwargs):
        super(SearchField, self).__init__(*args, **kwargs)
        self.setPlaceholderText("Type Here to Search")


class DemoMenuApp(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(DemoMenuApp, self).__init__(parent=parent)
        self.selection_manager = ToolSelectionManager
        self.setWindowTitle("Cool App")

        self.root = QtGui.QWidget()
        self.setCentralWidget(self.root)
        self.root_layout = QtGui.QVBoxLayout()
        self.search_field = SearchField()
        self.root_layout.addWidget(self.search_field)
        self.tree_layout = QtGui.QHBoxLayout()

        self.root_layout.addLayout(self.tree_layout)
        self.root.setLayout(self.root_layout)

        self.left_tree_view = QtGui.QTreeWidget()
        self.left_tree_view.setHeaderLabels(["Name", "File Path"])
        self.tree_layout.addWidget(self.left_tree_view)

        self.left_tree_view.itemSelectionChanged.connect(self.on_tree_selection_changed)
        LeftViewContextMenu.add_widget(self.left_tree_view)

        # Add fake tree data
        item1 = QtGui.QTreeWidgetItem()
        item1.setData(0, QtCore.Qt.DisplayRole, "File1")
        item1.setData(1, QtCore.Qt.DisplayRole, "C:/Assets/File1.txt")
        item2 = QtGui.QTreeWidgetItem()
        item2.setData(0, QtCore.Qt.DisplayRole, "File2")
        item2.setData(1, QtCore.Qt.DisplayRole, "D:/Assets/File2.txt")

        self.left_tree_view.addTopLevelItems([item1, item2])

        self.right_tree_view = QtGui.QTreeWidget()
        self.right_tree_view.setHeaderLabels(["Name", "File Path"])

        item3 = QtGui.QTreeWidgetItem()
        item3.setData(0, QtCore.Qt.DisplayRole, "File3")
        item3.setData(1, QtCore.Qt.DisplayRole, "D:/Assets/File3.txt")
        self.right_tree_view.addTopLevelItem(item3)
        self.tree_layout.addWidget(self.right_tree_view)

        self.right_tree_view.itemSelectionChanged.connect(self.on_tree_selection_changed)
        RightViewContextMenu.add_widget(self.right_tree_view)

        # NOTE: Uncomment these to test a dynamic removal of the menus
        # LeftViewContextMenu.remove_widget(self.left_tree_view)
        # RightViewContextMenu.remove_widget(self.right_tree_view)

    def on_tree_selection_changed(self):
        self.selection_manager.left_selection = self.left_tree_view.selectedItems()
        self.selection_manager.right_selection = self.right_tree_view.selectedItems()


@LeftViewContextMenu.register_action("Version Control/Download", "Ctrl+D", priority=11)
def sync_current_widget():
    selection = ToolSelectionManager.left_selection
    if selection:
        file_path = selection[0].text(1)
        print "Downloading: {}!".format(file_path)


# A silly validator that only returns true to files on the D: drive
def has_any_selection():
    selection = ToolSelectionManager.left_selection
    if selection:
        file_path = selection[0].text(1)
        return "D:" in file_path
    return False


# Demonstrates use of the validator to determine whether or not the action should appear
@LeftViewContextMenu.register_action("Version Control/Check Out", "Ctrl+C", priority=12, validator=has_any_selection)
def check_out_current_widget():
    selection = ToolSelectionManager.left_selection
    if selection:
        file_path = selection[0].text(1)
        print "Checking out: {}!".format(file_path)


@LeftViewContextMenu.register_action("Version Control/Submit", "Ctrl+S", priority=40)
def submit_current_widget():
    selection = ToolSelectionManager.left_selection
    if selection:
        file_path = selection[0].text(1)
        print " <- Submitting: {}!".format(file_path)


@RightViewContextMenu.register_action("Local Control/Submit", "Ctrl+S", priority=40)
def submit_current_widget():
    selection = ToolSelectionManager.right_selection
    if selection:
        file_path = selection[0].text(1)
        print " -> Submitting: {}!".format(file_path)


ToolSelectionManager = SelectionManager()  # Helper selection manager for this demo


def main():
    # Main point of entry for the Qt application
    app = QtGui.QApplication(sys.argv)
    window = DemoMenuApp()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
