"""Small, randomly falling squares, painted as part of the background only."""
import random
from gi.repository import Gtk

class PixelRain(Gtk.DrawingArea):
    def __init__(self,settings):
        super().__init__()
        self.particles=[]
        self.last_frame=0
        self.dimensions=None
        self.settings=None
        self.configure(settings)
        self.connect('draw',self.draw)
        self.add_tick_callback(self.tick)

    def configure(self,settings):
        if self.settings==settings:return
        self.settings=dict(settings)
        self.particles=[]
        self.last_frame=0
        self.queue_draw()

    def particle(self,width,height,initial=False):
        sizes=self.settings.get('sizes',[2,3,4])
        size=max(1,min(8,int(random.choice(sizes or [3]))))
        low=max(5,float(self.settings.get('min_speed',35)))
        high=max(low,float(self.settings.get('max_speed',95)))
        y=random.uniform(-height,height) if initial else -random.uniform(8,180)
        return [random.uniform(0,max(1,width-size)),y,random.uniform(low,high),size]

    def tick(self,widget,clock):
        if not self.settings.get('enabled',True):return True
        now=clock.get_frame_time()/1000000
        fps=max(10,min(60,int(self.settings.get('fps',30))))
        if self.last_frame and now-self.last_frame<1/fps:return True
        dt=min(.1,now-self.last_frame) if self.last_frame else 1/fps
        self.last_frame=now
        width,height=self.get_allocated_width(),self.get_allocated_height()
        if width<2 or height<2:return True
        if self.dimensions!=(width,height):
            self.dimensions=(width,height)
            count=max(0,min(300,int(self.settings.get('count',90))))
            count=round(count*width*height/(1920*1080))
            self.particles=[self.particle(width,height,True) for _ in range(count)]
        if not self.particles:
            count=max(0,min(300,int(self.settings.get('count',90))))
            self.particles=[self.particle(width,height,True) for _ in range(round(count*width*height/(1920*1080)))]
        for index,p in enumerate(self.particles):
            p[1]+=p[2]*dt
            if p[1]>height+p[3]: self.particles[index]=self.particle(width,height)
        self.queue_draw()
        return True

    def draw(self,widget,cr):
        if not self.settings.get('enabled',True):return False
        cr.set_source_rgb(0,0,0)
        for x,y,speed,size in self.particles:
            # Whole-pixel coordinates keep the retro edges sharp.
            cr.rectangle(int(x),int(y),size,size)
        cr.fill()
        return False
