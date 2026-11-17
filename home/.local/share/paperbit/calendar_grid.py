"""Monday-first calendar with individually styled weekday columns."""
import calendar as dates
import datetime
from gi.repository import Gtk,Gdk

class MonthGrid(Gtk.Box):
    MONTHS=('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre')
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=8)
        self.set_margin_start(8);self.set_margin_end(8)
        self.set_margin_top(10);self.set_margin_bottom(10)
        self.set_can_focus(True)
        self.selected=datetime.date.today()
        self.year,self.month=self.selected.year,self.selected.month
        nav=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=3)
        self.month_label=Gtk.Label()
        for symbol,delta,hint in [('«',-12,'Año anterior'),('‹',-1,'Mes anterior')]:
            nav.pack_start(self.nav_button(symbol,delta,hint),False,False,0)
        nav.pack_start(self.month_label,True,True,0)
        for symbol,delta,hint in [('›',1,'Mes siguiente'),('»',12,'Año siguiente')]:
            nav.pack_start(self.nav_button(symbol,delta,hint),False,False,0)
        self.pack_start(nav,False,False,0)
        self.grid=Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_spacing(2)
        self.pack_start(self.grid,False,False,0)
        self.connect('key-press-event',self.key)
        self.render()

    def nav_button(self,symbol,delta,hint):
        button=Gtk.Button(label=symbol)
        button.get_style_context().add_class('calendar-nav')
        button.set_tooltip_text(hint)
        button.set_can_focus(False)
        button.connect('clicked',lambda *_:self.shift(delta))
        return button

    def shift(self,delta):
        count=self.year*12+self.month-1+delta
        self.year,self.month=count//12,count%12+1
        self.render()

    @staticmethod
    def column_style(widget,column):
        widget.get_style_context().add_class('weekday' if column<4 else 'friday' if column==4 else 'weekend')

    def render(self):
        self.month_label.set_text(f'{self.MONTHS[self.month-1]} {self.year}')
        for widget in self.grid.get_children():self.grid.remove(widget)
        for column,name in enumerate(('lun','mar','mié','jue','vie','sáb','dom')):
            label=Gtk.Label(label=name)
            label.get_style_context().add_class('calendar-weekday')
            self.column_style(label,column)
            self.grid.attach(label,column,0,1,1)
        first=datetime.date(self.year,self.month,1)
        start=first-datetime.timedelta(days=first.weekday())
        for i in range(42):
            day=start+datetime.timedelta(days=i)
            column=i%7
            button=Gtk.Button(label=str(day.day))
            button.set_can_focus(False)
            style=button.get_style_context();style.add_class('calendar-day')
            self.column_style(button,column)
            if day.month!=self.month:style.add_class('other-month')
            if day==datetime.date.today():style.add_class('today')
            if day==self.selected:style.add_class('selected-day')
            button.set_tooltip_text(day.strftime('%A, %d de %B de %Y'))
            button.connect('clicked',lambda widget,chosen=day:self.choose(chosen))
            self.grid.attach(button,column,i//7+1,1,1)
        self.grid.show_all()

    def choose(self,date):
        self.selected=date
        self.year,self.month=date.year,date.month
        self.render()

    def go_today(self,*unused):self.choose(datetime.date.today())

    def key(self,widget,event):
        movement={Gdk.KEY_Left:-1,Gdk.KEY_Right:1,Gdk.KEY_Up:-7,Gdk.KEY_Down:7}
        if event.keyval in movement:
            self.choose(self.selected+datetime.timedelta(days=movement[event.keyval]));return True
        if event.keyval in (Gdk.KEY_Page_Up,Gdk.KEY_Page_Down):
            self.shift(-1 if event.keyval==Gdk.KEY_Page_Up else 1);return True
        if event.keyval==Gdk.KEY_Home:self.go_today();return True
        return False
