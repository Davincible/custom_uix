# -*- coding: utf-8 -*-
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import OptionProperty, NumericProperty, StringProperty, \
    BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout

Builder.load_string("""
#: import Window kivy.core.window.Window
<SlidingPanel>
    anim_alpha: (self.height / -self.y) if self.y else 0
    orientation: 'vertical'
    size_hint: None, None
    width: Window.width * (.8 if root.side in ('left', 'right') else 1)
    height: Window.height * (.8 if root.side == 'bottom' else 1)
    x:
        ((-1 if self.side in ('left', 'right') else 0) * self.width
        if self.side == 'left' else Window.width)
    y: (-1 if self.side == 'bottom' else 0) * self.height

<PanelShadow>
    canvas:
        Color:
            rgba: root.color
        Rectangle:
            size: root.size
""")


class PanelShadow(BoxLayout):
    color = ListProperty([0, 0, 0, 0])


class SlidingPanel(BoxLayout):
    anim_length_close = NumericProperty(0.3)
    anim_length_open = NumericProperty(0.3)
    animation_t_open = StringProperty('out_sine')
    animation_t_close = StringProperty('out_sine')
    side = OptionProperty('left', options=['left', 'right', 'bottom'])

    shadow = PanelShadow()
    _open = BooleanProperty(False)
    _sliding = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SlidingPanel, self).__init__(**kwargs)
        Clock.schedule_once(lambda x: Window.add_widget(self.shadow, 89), 0)
        Clock.schedule_once(lambda x: Window.add_widget(self, 90), 0)

    def toggle(self):
        self._sliding = True
        Animation.stop_all(self, 'x', 'y')
        Animation.stop_all(self.shadow, 'color')
        if self._open:
            if self.side == 'left':
                target_x = -1 * self.width
            else:
                target_x = Window.width

            Animation(duration=self.anim_length_open,
                      t=self.animation_t_open,
                      color=[0, 0, 0, 0]).start(self.shadow)
        else:
            if self.side == 'left':
                target_x = 0
            else:
                target_x = Window.width - self.width
            Animation(duration=self.anim_length_open,
                      t=self.animation_t_open,
                      color=[0, 0, 0, 0.5]).start(self.shadow)
        if self.side == 'bottom':
            kwargs = {'y': 0 if not self._open else (-1 * self.height)}
            self.x = 0
        else:
            kwargs = {'x': target_x}
        self._open = not self._open
        anim = Animation(duration=self.anim_length_close,
                         t=self.animation_t_close, **kwargs)
        anim.bind(on_complete=lambda *_: setattr(self, '_sliding', False))
        anim.start(self)


    def on_touch_down(self, touch):
        # Prevents touch events from propagating to anything below the widget.
        super(SlidingPanel, self).on_touch_down(touch)
        if self.collide_point(*touch.pos) or self._open:
            return True

    def on_touch_up(self, touch):
        if self._sliding:
            return True
        super(SlidingPanel, self).on_touch_up(touch)
        if not self.collide_point(touch.x, touch.y) and self._open:
            self.toggle()
        return True
