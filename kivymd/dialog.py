# -*- coding: utf-8 -*-

from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivymd.theming import ThemableBehavior
from kivymd.elevationbehavior import RectangularElevationBehavior
from kivymd.button import MDFlatButton
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.event import EventDispatcher
Builder.load_string('''
<MDDialog>:
    canvas:
        Color:
            rgba: self.theme_cls.bg_light
        Rectangle:
            size: self.size
            pos: self.pos

    _container: container
    _action_area:action_area
    elevation: 12
    GridLayout:
        
        cols: 1
        GridLayout:
            cols: 1
            padding: dp(24), dp(24), dp(24), dp(24)
            spacing: dp(20)
            id: base_layout
            MDLabel:
                id: title_label
                text: root.title
                font_style: root.font_style
                theme_text_color: root.theme_text_color
                halign: root.halign
                valign: root.valign
                size_hint_y: None
                text_size: self.width, None
                height: self.texture_size[1]
            ScrollView:
                effect_cls: 'ScrollEffect'
                BoxLayout:
                    size_hint_y: None
                    height: self.minimum_height
                    id: container
        AnchorLayout:
            id: anchor_layout
            anchor_x: 'right'
            anchor_y: 'center'
            size_hint: 1, None
            height: dp(52) if len(root._action_buttons) > 0 else 0
            padding: dp(8), dp(8)
            GridLayout:
                id: action_area
                rows: 1
                size_hint: None, None if len(root._action_buttons) > 0 else 1
                height: dp(36) if len(root._action_buttons) > 0 else 0
                width: self.minimum_width
                spacing: dp(8)
''')


class MDDialog(ThemableBehavior, RectangularElevationBehavior, ModalView):
    title = StringProperty('')
    theme_text_color = StringProperty('Primary')
    font_style = StringProperty('Title Bold')
    halign = StringProperty('left')
    valign = StringProperty('middle')

    content = ObjectProperty(None)

    md_bg_color = ListProperty([0, 0, 0, .2])

    _container = ObjectProperty()
    _action_buttons = ListProperty([])
    _action_area = ObjectProperty()

    def __init__(self, **kwargs):
        super(MDDialog, self).__init__(**kwargs)
        self.bind(_action_buttons=self._update_action_buttons,
                  auto_dismiss=lambda *x: setattr(self.shadow, 'on_release',
                                                  self.shadow.dismiss if self.auto_dismiss else None))
        Clock.schedule_once(self._set_height)

    def _set_height(self, *args):
        if self._action_buttons:
            new_height = self.ids.base_layout.minimum_height + self.ids.container.height + dp(52)
        else:
            new_height = self.ids.base_layout.minimum_height + self.ids.container.height
        self.height = new_height if new_height < .8 * Window.size[1] else Window.size[1] * .8

    def add_action_button(self, text='', action=None,white_space=False, white_space_width=dp(88), repeat=1):
        """Add an :class:`FlatButton` to the right of the action area.

        :param icon: Unicode character for the icon
        :type icon: str or None
        :param action: Function set to trigger when on_release fires
        :type action: function or None
        """
        if not white_space:
            button = MDFlatButton(text=text,
                                  size_hint=(None, None),
                                  height=dp(36))
            button.text_color = self.theme_cls.primary_color
            button.md_bg_color = self.theme_cls.bg_light
            if action:
                button.bind(on_release=action)
        else:
            button = Widget(size_hint=(None, None),
                            size=(white_space_width*repeat, dp(36)))

        self._action_buttons.append(button)

    def add_widget(self, widget):
        if self._container:
            if self.content:
                raise PopupException(
                    'Popup can have only one widget as content')
            self.content = widget
        else:
            super(MDDialog, self).add_widget(widget)

    def open(self, *largs):
        '''Show the view window from the :attr:`attach_to` widget. If set, it
        will attach to the nearest window. If the widget is not attached to any
        window, the view will attach to the global
        :class:`~kivy.core.window.Window`.
        '''
        if self._window is not None:
            Logger.warning('ModalView: you can only open once.')
            return self
        # search window
        self._window = self._search_window()
        if not self._window:
            Logger.warning('ModalView: cannot open view, no window found.')
            return self
        self._window.add_widget(self)
        self._window.bind(on_resize=self._align_center,
                          on_keyboard=self._handle_keyboard)
        self.center = self._window.center
        self.bind(size=self._align_center)
        a = Animation(_anim_alpha=1., d=self._anim_duration)
        a.bind(on_complete=lambda *x: self.dispatch('on_open'))
        a.start(self)
        return self

    def dismiss(self, *largs, **kwargs):
        '''Close the view if it is open. If you really want to close the
        view, whatever the on_dismiss event returns, you can use the *force*
        argument:
        ::

            view = ModalView(...)
            view.dismiss(force=True)

        When the view is dismissed, it will be faded out before being
        removed from the parent. If you don't want animation, use::

            view.dismiss(animation=False)

        '''
        if self._window is None:
            return self
        if self.dispatch('on_dismiss') is True:
            if kwargs.get('force', False) is not True:
                return self
        if kwargs.get('animation', True):
            Animation(_anim_alpha=0., d=self._anim_duration).start(self)
        else:
            self._anim_alpha = 0
            self._real_remove_widget()
        return self

    def on_content(self, instance, value):
        if self._container:
            self._container.clear_widgets()
            self._container.add_widget(value)

    def on__container(self, instance, value):
        if value is None or self.content is None:
            return
        self._container.clear_widgets()
        self._container.add_widget(self.content)

    def on_touch_down(self, touch):
        if self.disabled and self.collide_point(*touch.pos):
            return True
        return super(MDDialog, self).on_touch_down(touch)

    def _update_action_buttons(self, *args):
        self._action_area.clear_widgets()
        for btn in self._action_buttons:
            try:
                btn.content.texture_update()
                btn.width = btn.content.texture_size[0] + dp(16)
            except AttributeError:
                pass
            self._action_area.add_widget(btn)
