# -*- coding: utf-8 -*-
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty, OptionProperty, ReferenceListProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.backgroundcolorbehavior import SpecificBackgroundColorBehavior
from kivymd.button import MDIconButton
from kivymd.theming import ThemableBehavior
from kivymd.elevationbehavior import RectangularElevationBehavior
from kivymd.theming import ThemeManager
from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.graphics.instructions import ContextInstruction
from kivy.graphics.texture import Texture


kv_file = '''
#:import m_res kivymd.material_resources
#:import Image kivy.uix.image

<Toolbar>:
    id: toolbar
    logo: self.logo
    logo_size: self.logo_size
    logo_height: self.logo_height
    size_hint_y: None
    height: root.theme_cls.standard_increment
    padding: [root.theme_cls.horizontal_margins - dp(12), 0]
    opposite_colors: True
    elevation: 6
    texture: self.texture
    
    
    BoxLayout:
        id: left_actions
        orientation: 'horizontal'
        size_hint_x: None
        padding: [0, (self.height - dp(48))/2]
        
    middle_content:
        id: logo_content
        texture: root.texture
        
        canvas:
            Rectangle:
                size: self.logo_size
                pos: (self.pos[0] + self.logo_offset_x, self.pos[1] + self.logo_offset_y)
                texture: self.texture
                
        MDLabel:
            font_style: 'Title'
            opposite_colors: root.opposite_colors
            theme_text_color: 'Custom'
            text_color: root.specific_text_color
            text: root.title if not root.texture_set else ''
            shorten: True
            shorten_from: 'right'
            
    BoxLayout:
        id: right_actions
        orientation: 'horizontal'
        size_hint_x: None
        padding: [0, (self.height - dp(48))/2]
'''
Builder.load_string(kv_file)


class middle_content(BoxLayout):
    logo_offset_x = NumericProperty('4dp')
    logo_offset_y = NumericProperty('3dp')
    logo_x = NumericProperty(0)
    logo_y = NumericProperty(0)
    logo_a = NumericProperty(0)
    logo_b = NumericProperty(0)
    logo_size = ReferenceListProperty(logo_x, logo_y)
    logo_pos = ReferenceListProperty(logo_a, logo_b)

    def _update_size(self, *args):
        try:
            new_maxwidth = (self.texture.size[0] * dp(48)) / self.texture.size[1], dp(48)
            new_minwidth = self.width, (self.texture.size[1]*self.width) / self.texture.size[0]
            self.logo_size = new_maxwidth if self.width >= new_maxwidth[0] else new_minwidth
            self.logo_offset_y = (self.height - self.logo_size[1]) / 2
        except AttributeError:
            pass

    def __init__(self, **kwargs):
        super(middle_content, self).__init__(**kwargs)
        Clock.schedule_once(self._update_size)
        self.bind(size=self._update_size)


class Toolbar(ThemableBehavior, RectangularElevationBehavior,
              SpecificBackgroundColorBehavior, BoxLayout):
    left_action_items = ListProperty()
    """The icons on the left of the Toolbar.

    To add one, append a list like the following:

        ['icon_name', callback]

    where 'icon_name' is a string that corresponds to an icon definition and
     callback is the function called on a touch release event.
    """

    right_action_items = ListProperty()
    """The icons on the left of the Toolbar.

    Works the same way as :attr:`left_action_items`
    """

    """The text displayed on the Toolbar."""
    title = StringProperty()

    """"The properties to set a logo on the Toolbar, when a logo is set, the title text is hidden"""
    logo = StringProperty()


    md_bg_color = ListProperty([0, 0, 0, 1])

    texture_set = BooleanProperty(False)

    def _update_texture(self, *args):
        if self.logo:
            self.ids.logo_content.texture = Image(source=self.logo).texture
            self.texture_set = True

    def __init__(self, **kwargs):
        super(Toolbar, self).__init__(**kwargs)
        self.bind(specific_text_color=self.update_action_bar_text_colors)
        Clock.schedule_once(
            lambda x: self.on_left_action_items(0, self.left_action_items))
        Clock.schedule_once(
            lambda x: self.on_right_action_items(0,
                                                 self.right_action_items))
        Clock.schedule_once(self._update_texture)

    def on_left_action_items(self, instance, value):
        self.update_action_bar(self.ids['left_actions'], value)

    def on_right_action_items(self, instance, value):
        self.update_action_bar(self.ids['right_actions'], value)

    def update_action_bar(self, action_bar, action_bar_items):
        action_bar.clear_widgets()
        new_width = 0
        for item in action_bar_items:
            new_width += dp(48)
            action_bar.add_widget(MDIconButton(icon=item[0],
                                               on_release=item[1],
                                               opposite_colors=True,
                                               text_color=self.specific_text_color,
                                               theme_text_color='Custom'))
        action_bar.width = new_width

    def update_action_bar_text_colors(self, instance, value):
        for child in self.ids['left_actions'].children:
            child.text_color = self.specific_text_color
        for child in self.ids['right_actions'].children:
            child.text_color = self.specific_text_color