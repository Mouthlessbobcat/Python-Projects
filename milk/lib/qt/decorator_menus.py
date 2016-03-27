import sys
from PySide import QtGui, QtCore

import menu


class CoolAppContextMenu(menu.BaseContextMenuTree):
    pass

class RightViewContextMenu(menu.BaseContextMenuTree):
    pass

class SelectionManager(object):
    """
    Holds reference to selected items in the main tree widget.
    """

    def __init__(self):
        self.selection = []


ToolSelectionManager = SelectionManager()


# TODO: Add class decorator to decorator Qt.QWidget classes; this would register the widget type to always have the context menu
# TODO: Add menu removal

class MyCoolApp(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MyCoolApp, self).__init__(parent=parent)
        self.selection_manager = ToolSelectionManager
        self.setWindowTitle("Cool App")

        self.root = QtGui.QWidget()
        self.root_layout = QtGui.QHBoxLayout()
        self.root.setLayout(self.root_layout)
        self.setCentralWidget(self.root)
        main_layout = self.centralWidget().layout()
        self.tree_view = QtGui.QTreeWidget()
        self.tree_view.setHeaderLabels(["Name", "File Path"])
        main_layout.addWidget(self.tree_view)

        self.tree_view.itemSelectionChanged.connect(self.on_tree_selection_changed)
        CoolAppContextMenu.add_widget(self.tree_view)

        # Add fake tree data
        item1 = QtGui.QTreeWidgetItem()
        item1.setData(0, QtCore.Qt.DisplayRole, "File1")
        item1.setData(1, QtCore.Qt.DisplayRole, "C:/Assets/File1.txt")
        item2 = QtGui.QTreeWidgetItem()
        item2.setData(0, QtCore.Qt.DisplayRole, "File2")
        item2.setData(1, QtCore.Qt.DisplayRole, "D:/Assets/File2.txt")

        self.tree_view.addTopLevelItems([item1, item2])


        self.tree_view_bottom = QtGui.QTreeWidget()
        self.tree_view_bottom.setHeaderLabels(["Name", "File Path"])
        main_layout.addWidget(self.tree_view_bottom)

        self.tree_view_bottom.itemSelectionChanged.connect(self.on_tree_selection_changed)
        RightViewContextMenu.add_widget(self.tree_view_bottom)

    def on_tree_selection_changed(self):
        self.selection_manager.selection = self.tree_view.selectedItems()


@CoolAppContextMenu.register_action("Version Control/Download", "Ctrl+D", priority=11)
def sync_current_widget():
    selection = ToolSelectionManager.selection
    if selection:
        file_path = selection[0].text(1)
        print "Syncing: {}!".format(file_path)


def has_any_selection():
    selection = ToolSelectionManager.selection
    if selection:
        file_path = selection[0].text(1)
        return "D:" in file_path
    return False


@CoolAppContextMenu.register_action("Version Control/Check Out", "Ctrl+C", priority=12, validator=has_any_selection)
def check_out_current_widget():
    selection = ToolSelectionManager.selection
    if selection:
        file_path = selection[0].text(1)
        print "Checking out: {}!".format(file_path)


@CoolAppContextMenu.register_action("Version Control/Submit", "Ctrl+S", priority=40)
def submit_current_widget():
    selection = ToolSelectionManager.selection
    if selection:
        file_path = selection[0].text(1)
        print "Submitting: {}!".format(file_path)


@RightViewContextMenu.register_action("Local Control/Submit", "Ctrl+S", priority=40)
def submit_current_widget():
    selection = ToolSelectionManager.selection
    if selection:
        file_path = selection[0].text(1)
        print "Submitting: {}!".format(file_path)

def main():
    app = QtGui.QApplication(sys.argv)
    window = MyCoolApp()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
