"""
This module implements a utility class BaseContextMenuTree that is used to easily create context menus in PySide.

The goal of this implementation is to mirror all of functionality
provided by the Unity game engine's MenuItem C# attribute.

Unity's API is simple and elegant, whereas PySide requires a significant amount of boiler plate
to correctly create context menus with working keyboard shortcuts.

More documentation on the referenced Unity API can be found here:
https://unity3d.com/learn/tutorials/modules/intermediate/editor/menu-items

"""
from PySide import QtGui, QtCore
import collections


class BaseContextMenuTree(object):
    @classmethod
    def _get_widget_callback_map(cls):
        if not hasattr(cls, "_widget_callback_map"):
            cls._widget_callback_map = {}
        return cls._widget_callback_map

    @classmethod
    def _get_widget_action_map(cls):
        if not hasattr(cls, "_widget_action_map"):
            cls._widget_action_map = collections.defaultdict(list)
        return cls._widget_action_map

    @classmethod
    def get_menu_root(cls):
        if not hasattr(cls, "_menu_root"):
            cls._menu_root = QtGui.QMenu()
        return cls._menu_root

    @classmethod
    def set_menu_root(cls, val):
        cls._menu_root = val

    @classmethod
    def _get_func_map(cls):
        if not hasattr(cls, "func_map"):
            cls.func_map = {}
        return cls.func_map

    @classmethod
    def _get_sub_menu_map(cls):
        if not hasattr(cls, "sub_menu_map"):
            cls.sub_menu_map = {}
        return cls.sub_menu_map

    @classmethod
    def _set_sub_menu_map(cls, val):
        cls.sub_menu_map = val

    @classmethod
    def _get_menu_bar_map(cls):
        if not hasattr(cls, "_menu_bar_map"):
            cls._menu_bar_map = collections.defaultdict(list)
        return cls._menu_bar_map

    @classmethod
    def register_action(cls, action_name, shortcut=None, priority=None, validator=None):
        """
        Decorator for registering a function into the internal action mapping.

        Sub-menus will be built for all actions that use the "/" separator.
        Args:
            action_name: (str) Complete
            shortcut:
        """
        if priority and not isinstance(priority, int):
            TypeError("Failed to register action. 'priorityp must be of type int, not {}.".format(type(priority)))

        def wrap(func):
            if action_name in cls._get_func_map():
                raise AttributeError("{} is already registered to the context menu.".format(action_name))

            # Store all the properties in a dictionary mapped to the action name for referencing later
            cls._get_func_map()[action_name] = dict(func=func, shortcut=shortcut, priority=priority,
                                                    validator=validator)

        return wrap

    @classmethod
    def register_widget(cls, widget_cls):
        """
        A decorator for registering a QWidget class type to always present this context menu.

        We need the widget to be constructed before adding ourselves to it.
        To accomplish this, the class's __init__ method is monkey patched to add itself to this menu.
        Args:
            widget_cls:

        Returns: (widget_cls)

        """
        if not issubclass(widget_cls, QtGui.QWidget):
            raise TypeError("Failed to register {} to context menu {}. "
                            "Decorated class must inherit from QtGui.QWidget.".format(widget_cls, cls))

        old_init = widget_cls.__init__  # Store original initializer

        def _menu__init__(self, *args, **kwargs):
            old_init(self, *args, **kwargs)  # Call original initializer
            cls.add_widget(self)  # Add the new widget instance to this menu

        widget_cls.__init__ = _menu__init__  # Apply the custom __init__ method
        return widget_cls

    @classmethod
    def add_widget(cls, widget):
        """
        Adds a widget that the user wants to display this context menu from.
        Args:
            widget: (QtGui.QWidget) A widget to attach this menu to.

        Returns: (None)
        """
        if not isinstance(widget, QtGui.QWidget):
            raise TypeError("Failed to add widget {} to context menu {}. "
                            "Added widget must inherit from QtGui.QWidget.".format((str(type(widget))), cls))
        cls._build_menu(widget=widget)
        widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        display_func = lambda point: cls.display(point, widget)  # Pass along the widget as a second argument
        widget.customContextMenuRequested.connect(display_func)  # Connect our self to be displayed on the widget
        cls._get_widget_callback_map()[widget] = display_func  # Store mapping of callback to widget for removal later

    @classmethod
    def remove_widget(cls, widget):
        """
        Removes a widget that was previously used to display this context menu.
        Args:
            widget: (QtGui.QWidget) A widget to remove the menu from.

        Returns: (bool) Whether or not the menu was actually removed.
        """
        callback_map = cls._get_widget_callback_map()
        action_map = cls._get_widget_action_map()

        did_removal = False

        # Unhook the callback
        if widget in callback_map:
            widget.customContextMenuRequested.disconnect(callback_map[widget])
            callback_map.pop(widget)
            did_removal = True

        # Remove all shortcut actions
        for action in action_map.get(widget, []):
            widget.removeAction(action)
            did_removal = True

        return did_removal

    @classmethod
    def display(cls, point, widget=None):
        """
        Presents the context menu tree at a specific point under parent context of the specified widget.

        It is not typically required to manually call this function.
        Args:
            point: (QtCore.QPoint) The point on screen to display the menu.
            widget: (QtGui.QWidget) The parent widget of the menu.

        Returns: (None)
        """
        if widget and not isinstance(widget, QtGui.QWidget):
            raise TypeError("Failed to display to context menu {}. "
                            "Parent widget must inherit from QtGui.QWidget.".format((str(type(widget))), cls))
        cls._build_menu(widget)
        # Build menus for all our registered commands

        # Use the widget's as a parent space if specified
        if widget:
            point = widget.mapToGlobal(point)
        cls.get_menu_root().exec_(point)

    @classmethod
    def add_actions_to_menu_bar(cls, menu_bar):
        for key, sub_menu in cls._get_sub_menu_map().iteritems():
            menu_bar.addMenu(sub_menu)
            cls._get_menu_bar_map()[menu_bar].append(sub_menu)

    @classmethod
    def _build_menu(cls, widget=None):
        """
        Internal method responsible for creating the menu and hooking up shortcuts to the parent widget.
        Args:
            widget: (QtGui.QWidget) The parent widget of the menu.
                                    Shortcut actions are automatically added to this widget's context.

        Returns: (None)
        """
        # Clear any existing widgets and reset our internal menu mapping
        cls._set_sub_menu_map({})
        cls.get_menu_root().clear()

        cur_priority = 0
        for action_name, map in sorted(cls._get_func_map().iteritems(), key=lambda x: x[1]["priority"]):

            # If there's a validator, its call must return true in order to display thie action in the menu
            if map["validator"] and not map["validator"]():
                continue

            action, parent_menu = cls._add_action(action_name, parent_menu=cls.get_menu_root())
            action.triggered.connect(map["func"])

            # Add separators every 10 values
            new_priority = map["priority"]
            if new_priority is not None and (new_priority / 10) > (cur_priority / 10):
                parent_menu.insertSeparator(action)
                cur_priority = new_priority

            shortcut = map.get("shortcut", None)
            # Action shortcuts live on parent widgets; we must have a widget to add them to
            if shortcut and widget:
                # Remove any existing actions; this allows you to override built in functionality, like Ctrl+S for save.
                for existing_action in widget.actions():
                    if existing_action.shortcut() == shortcut:
                        print "[WARNING] Removing Built-in Command for {}!".format(existing_action.text())
                        widget.removeAction(existing_action)

                # NOTE: QtCore.Qt.WidgetWithChildren seems like the correct context for now,
                #       but it provide the expected user interaction in all situations.
                #       Occasionally, QtCore.Qt.ApplicationShortcut may be needed.
                #       Perhaps this can be exposed long-term.
                # action.setShortcutContext(QtCore.Qt.ApplicationShortcut)
                action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
                action.setShortcut(shortcut)
                widget.addAction(action)  # Add action to the widget for shortcuts to work!
                cls._get_widget_action_map()[widget].append(action)

    @classmethod
    def _add_action(cls, action_name, parent_menu):
        """
        Internal method for recursively building sub menus to place an action at the correct leaf.

        Args:
            action_name: (str) Name of action to add.
            parent_menu: (QtGui.QMenu) The current parent menu.
        Returns:
            (QtGui.QAction, QtGui.QMenu) The created QAction instance and its parent menu as a tuple.
        """

        # Parse parent menus out recursively
        cur_action_name, token, remainder = action_name.partition('/')

        # If there's more path to parse, build sub menus as needed
        if remainder:
            if cur_action_name not in cls._get_sub_menu_map():
                new_parent = QtGui.QMenu(cur_action_name)
                parent_menu.addMenu(new_parent)
                parent_menu = new_parent  # Update current parent
                cls._get_sub_menu_map()[cur_action_name] = parent_menu
            parent_menu = cls._get_sub_menu_map()[cur_action_name]
            return cls._add_action(remainder, parent_menu)

        else:  # Otherwise, create the action as a leaf
            action = QtGui.QAction(parent_menu)
            action.setText(cur_action_name)
            parent_menu.addAction(action)
            return action, parent_menu
