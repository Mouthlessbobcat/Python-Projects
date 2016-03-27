from PySide import QtGui, QtCore

class BaseContextMenuTree(object):
    widgets = []

    func_map = {}
    sub_menu_map = {}

    _menu_root = None  # QtGui.QMenu instance holding the root menu

    @classmethod
    def _get_menu_root(cls):
        return cls._menu_root

    @classmethod
    def _set_menu_root(cls, val):
        cls._menu_root = val

    @classmethod
    def _get_func_map(cls):
        return cls.func_map

    @classmethod
    def _get_sub_menu_map(cls):
        return cls.sub_menu_map

    @classmethod
    def _set_sub_menu_map(cls, val):
        cls._menu_root = val


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
            cls._get_func_map()[action_name] = dict(func=func, shortcut=shortcut, priority=priority, validator=validator)

        return wrap

    @classmethod
    def add_widget(cls, widget):
        cls.widgets.append(widget)
        cls._build_menu(widget)
        widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        display_func = lambda point: cls.display(point, widget)  # Pass along the widget as a second argument
        widget.customContextMenuRequested.connect(display_func)

    @classmethod
    def _build_menu(cls, widget):
        cls._set_menu_root(QtGui.QMenu())

        cur_priority = 0
        for action_name, map in sorted(cls._get_func_map().iteritems(), key=lambda x: x[1]["priority"]):

            # If there's a validator, it must return true to show this action
            if map["validator"] and not map["validator"]():
                continue

            action, parent_menu = cls._add_action(action_name, parent_menu=cls._get_menu_root())
            action.triggered.connect(map["func"])

            # Add separators every 10 values
            new_priority = map["priority"]
            if (new_priority / 10) > (cur_priority / 10):
                parent_menu.insertSeparator(action)
                cur_priority = new_priority

            shortcut = map.get("shortcut", None)
            if shortcut:
                # Remove any existing actions; this allows you to override built in functionality, like Ctrl+S for save.
                for existing_action in widget.actions():
                    if existing_action.shortcut() == shortcut:
                        print "[WARNING] Removing Built-in Command for {}!".format(existing_action.text())
                        widget.removeAction(existing_action)
                action.setShortcutContext(QtCore.Qt.ApplicationShortcut)  # Must set context
                action.setShortcut(shortcut)
                widget.addAction(action)  # Add action to the widget for shortcuts to work!

    @classmethod
    def display(cls, point, widget):
        cls._set_sub_menu_map({})
        print "Displaying!", point, widget
        cls._build_menu(widget)
        # Build menus for all our registered commands
        display_pos = widget.mapToGlobal(point)
        cls._get_menu_root().exec_(display_pos)

    @classmethod
    def _add_action(cls, action_name, parent_menu):
        """
        Internal method for recursively building sub menus to place an action at the correct leaf.
        Args:
            action_name: (str) Name of action to add.
            parent_menu: (QtGui.QMenu) The curent parent menu.
        Returns: (QtGui.QAction) The created QAction instance.
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