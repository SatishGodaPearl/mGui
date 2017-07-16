"""
mGui.menus

Wrapper classes for Menus and MenuItems
"""

from mGui.core import Nested, Control, cmds, inspect


class Menu(Nested):
    CMD = cmds.menu
    _ATTRIBS = ['allowOptionBoxes', 'deleteAllItems', 'defineTemplate', 'docTag', 'enable', 'enableBackground',
                'exists', 'familyImage', 'helpMenu', 'label', 'mnemonic', 'parent', 'useTemplate', 'visible',
                'postMenuCommandOnce']
    _CALLBACKS = ['postMenuCommand']
    _READ_ONLY = ['numberOfItems']

    ACTIVE_MENU = None

    def __init__(self, key=None, **kwargs):
        super(Menu, self).__init__(key, **kwargs)
        self._cache_menu = None

    def __enter__(self):
        self._cache_menu = Menu.ACTIVE_MENU
        Menu.ACTIVE_MENU = self
        return self

    def __exit__(self, typ, value, tb):
        # see Nested.__exit___ for more details
        if typ and not self.ignore_exceptions:
            return False

        owning_scope = inspect.currentframe().f_back
        if owning_scope.f_back:
            owning_scope = owning_scope.f_back
        for key, value in owning_scope.f_locals.items():
            if type(value) in (Menu, MenuDivider, MenuItem, SubMenu, CheckBoxMenuItem, RadioMenuItem,
                               RadioMenuItemCollection):
                self.add(value, key)

        # restore the layout level
        Menu.ACTIVE_MENU = self._cache_menu
        self._cache_menu = None


class SubMenu(Menu):
    CMD = cmds.menu

    def __init__(self, key=None, **kwargs):
        # When creating a submenu, we use the menuItem command, however it returns a menu.
        # So we shadow the class attribute during initialization
        self.CMD = cmds.menuItem
        kwargs['subMenu'] = True
        super(SubMenu, self).__init__(key, **kwargs)
        # And remove the shadow once we've finished.
        del self.CMD
        self._cache_menu = None

    def __enter__(self):
        self._cache_menu = Menu.ACTIVE_MENU
        Menu.ACTIVE_MENU = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(SubMenu, self).__exit__(exc_type, exc_val, exc_tb)
        if Menu.ACTIVE_MENU:
            cmds.setParent(Menu.ACTIVE_MENU, menu=True)


class MenuItem(Control):
    CMD = cmds.menuItem
    _ATTRIBS = ["altModifier", "annotation", "allowOptionBoxes", "boldFont", "checkBox", "collection",
                "commandModifier", "ctrlModifier", "divider", "data", "defineTemplate", "docTag", "echoCommand",
                "enableCommandRepeat", "enable", "exists", "familyImage", "image", "insertAfter", "imageOverlayLabel",
                "italicized", "keyEquivalent", "label", "mnemonic", "optionBox", "optionBoxIcon", "optionModifier",
                "parent", "radioButton", "radialPosition", "shiftModifier", "subMenu", "sourceType", "tearOff",
                "useTemplate", "version", 'postMenuCommandOnce']
    _READ_ONLY = ['isCheckBox', 'isOptionBox', 'isRadioButton']
    _CALLBACKS = ['command', 'dragDoubleClickCommand', 'dragMenuCommand', 'postMenuCommand']

    def __init__(self, key=None, **kwargs):
        super(MenuItem, self).__init__(key, **kwargs)
        self.owner = None


class MenuDivider(MenuItem):
    def __init__(self, key=None, **kwargs):
        kwargs['divider'] = True
        super(MenuDivider, self).__init__(key, **kwargs)


class RadioMenuItemCollection(Control):
    CMD = cmds.radioMenuItemCollection
    _READ_ONLY = ['exists', 'defineTemplate', 'gl', 'parent', 'useTemplate']

    def __init__(self, key=None, **kwargs):
        super(RadioMenuItemCollection, self).__init__(key, **kwargs)
        self.owner = None

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        mGui_expand_stack = True
        # This closes out the collection, usually we'd do a setParent, but that doesn't seem to apply here.
        self.CMD()
        return False


class RadioMenuItem(MenuItem):
    def __init__(self, key=None, **kwargs):
        kwargs['radioButton'] = kwargs.get('radioButton', kwargs.get('rb', False))
        super(RadioMenuItem, self).__init__(key, **kwargs)


class CheckBoxMenuItem(MenuItem):
    def __init__(self, key=None, **kwargs):
        kwargs['checkBox'] = kwargs.get('checkBox', kwargs.get('cb', False))
        super(CheckBoxMenuItem, self).__init__(key, **kwargs)


class OptionMenu(Nested):
    CMD = cmds.optionMenu
    _ATTRIBS = ['alwaysCallChangeCommand', 'annotation', 'backgroundColor', 'docTag', 'enableBackground', 'exists',
                'height', 'label', 'manage', 'parent', 'preventOverride', 'select', 'value', 'visible', 'width']
    _READ_ONLY = ['fullPathName', 'itemListLong', 'itemListShort', 'isObscured', 'numberOfItems', 'numberOfPopupMenus',
                  'popupMenuArray']
    _CALLBACKS = ['changeCommand', 'dragCallback', 'dropCallback', 'visibleChangeCommand']
    _BIND_SRC = 'value'
    _BIND_TGT = 'items'
    _BIND_TRIGGER = 'changeCommand'

    @property
    def items(self):
        return [i.tag for i in self.controls]

    @items.setter
    def items(self, value):
        selected = self.select
        self.clear()
        self.controls[:] = [MenuItem(val, parent=self, tag=val) for val in value]
        if selected:
            self.select = selected

    def clear(self):
        for long_name in self.itemListLong or []:
            cmds.deleteUI(long_name)


class ActiveOptionMenu(OptionMenu):
    """
    A variant of the default OptionMenu which will call the command attached to
    the menuItem.  This allows for dropdown menus  which behave like regular
    menus rather than like pure dropdown selectors

    """

    def __init__(self, key=None, *args, **kwargs):
        super(ActiveOptionMenu, self).__init__(key, *args, **kwargs)
        self.changeCommand += self.fire_menu_callback

    def fire_menu_callback(self, *args, **kwargs):
        """
        this ensures that the command attached to the selected MenuItem is fired when that menu is selected
        """
        selected = self.controls[self.select - 1]
        selected.command()


class PopupMenu(Nested):
    CMD = cmds.popupMenu
    _ATTRIBS = ['altModifier', 'allowOptionBoxes', 'button', 'ctrlModifier', 'deleteAllItems', 'defineTemplate',
                'exists', 'markingMenu', 'parent', 'shiftModifier', 'useTemplate', 'visible', 'postMenuCommandOnce']
    _CALLBACKS = ['postMenuCommand']
    _READ_ONLY = ['numberOfItems']

    @property
    def itemArray(self):
        return [MenuItem.wrap(self.fullPathName + '|' + item) for item in
                self.CMD(self.widget, itemArray=True, q=True) or []]
