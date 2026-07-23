#!/usr/bin/env python3
"""Genera máscaras geométricas originales inspiradas en descripciones públicas.

No copia píxeles ni imágenes de Gamerch/CPM. Produce geometría genérica propia.
"""
from pathlib import Path
import math
import cv2
import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parents[1]/'src/main/resources/shapes'
S=2048

def canvas(): return np.zeros((S,S),np.uint8)
def pts(seq): return np.round(np.array(seq,np.float32)*S).astype(np.int32)
def poly(a,p): cv2.fillPoly(a,[pts(p)],255,lineType=cv2.LINE_AA)
def line(a,p,th=.075,closed=False): cv2.polylines(a,[pts(p)],closed,255,round(S*th),lineType=cv2.LINE_AA)
def save(name,a):
    ys,xs=np.where(a>0)
    if not len(xs): return
    pad=round(S*.045);x0=max(0,xs.min()-pad);x1=min(S,xs.max()+pad+1);y0=max(0,ys.min()-pad);y1=min(S,ys.max()+pad+1)
    m=a[y0:y1,x0:x1];rgba=np.full((*m.shape,4),255,np.uint8);rgba[:,:,3]=m
    Image.fromarray(rgba,'RGBA').save(OUT/f'{name}.png',optimize=True)

def regular(n,r=.42,c=(.5,.5),offset=-math.pi/2):
    return [(c[0]+r*math.cos(offset+2*math.pi*i/n),c[1]+r*math.sin(offset+2*math.pi*i/n)) for i in range(n)]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    shapes={}
    a=canvas();poly(a,[(.16,.25),(.82,.25),(.68,.75),(.02,.75)]);shapes['14_parallelogram']=a
    a=canvas();poly(a,[(.5,.06),(.94,.5),(.5,.94),(.06,.5)]);shapes['15_diamond']=a
    a=canvas();poly(a,[(.08,.18),(.65,.18),(.94,.5),(.65,.82),(.08,.82)]);shapes['16_directional_pentagon']=a
    a=canvas();poly(a,[(.06,.22),(.67,.22),(.92,.5),(.67,.78),(.06,.78),(.29,.5)]);shapes['17_chevron']=a
    a=canvas();poly(a,[(.04,.18),(.28,.18),(.56,.5),(.28,.82),(.04,.82),(.32,.5)]);poly(a,[(.40,.18),(.64,.18),(.92,.5),(.64,.82),(.40,.82),(.68,.5)]);shapes['18_double_chevron']=a
    a=canvas();p=[]
    for i in range(32):
        r=.44 if i%2==0 else .31;ang=-math.pi/2+i*math.pi/16;p.append((.5+r*math.cos(ang),.5+r*math.sin(ang)))
    poly(a,p);shapes['19_sunburst']=a
    a=canvas();cv2.circle(a,(S//2,S//2),round(S*.42),255,-1,cv2.LINE_AA);cv2.circle(a,(S//2,S//2),round(S*.24),0,-1,cv2.LINE_AA);shapes['20_ring']=a
    a=canvas();p=[]
    for i in range(10):
        r=.44 if i%2==0 else .19;ang=-math.pi/2+i*math.pi/5;p.append((.5+r*math.cos(ang),.5+r*math.sin(ang)))
    poly(a,p);shapes['21_star']=a
    a=canvas();line(a,[(.05,.70),(.21,.28),(.37,.70),(.53,.28),(.69,.70),(.85,.28),(.96,.66)],.095);shapes['22_zigzag']=a
    a=canvas();line(a,[(.10,.55),(.25,.28),(.40,.72),(.55,.28),(.70,.72),(.90,.42)],.060);shapes['23_zigzag_thin']=a
    a=canvas();cv2.rectangle(a,(round(S*.12),round(S*.12)),(round(S*.88),round(S*.88)),255,round(S*.075),cv2.LINE_AA);shapes['24_square_outline']=a
    a=canvas();cv2.circle(a,(S//2,S//2),round(S*.41),255,round(S*.075),cv2.LINE_AA);shapes['25_circle_outline']=a
    a=canvas();poly(a,regular(6));shapes['26_hexagon']=a
    a=canvas();line(a,regular(6),.070,True);shapes['27_hexagon_outline']=a
    a=canvas();line(a,[(.08,.5),(.66,.5),(.51,.25),(.92,.5),(.51,.75),(.66,.5)],.070);shapes['28_arrow_outline']=a
    a=canvas();line(a,regular(3),.070,True);shapes['29_triangle_outline']=a
    a=canvas();poly(a,[(.10,.08),(.90,.08),(.65,.5),(.90,.92),(.10,.92),(.35,.5)]);shapes['30_concave_hourglass']=a
    a=canvas();poly(a,[(.08,.72),(.08,.40),(.48,.08),(.92,.08),(.92,.36),(.57,.36),(.20,.72)]);shapes['31_slope']=a
    a=canvas();p=[]
    for t in np.linspace(0,4.8*math.pi,260):
        r=.035+.023*t;p.append((.5+r*math.cos(t),.5+r*math.sin(t)))
    line(a,p,.045);shapes['32_spiral']=a
    a=canvas();
    # U mediante arco inferior y patas.
    cv2.ellipse(a,(S//2,round(S*.58)),(round(S*.34),round(S*.33)),0,0,180,255,round(S*.075),cv2.LINE_AA)
    cv2.line(a,(round(S*.16),round(S*.16)),(round(S*.16),round(S*.58)),255,round(S*.075),cv2.LINE_AA)
    cv2.line(a,(round(S*.84),round(S*.16)),(round(S*.84),round(S*.58)),255,round(S*.075),cv2.LINE_AA);shapes['33_u_shape']=a
    a=canvas();t=np.linspace(0,2*math.pi,400);x=16*np.sin(t)**3;y=13*np.cos(t)-5*np.cos(2*t)-2*np.cos(3*t)-np.cos(4*t);x=(x-x.min())/(x.max()-x.min())*.82+.09;y=(y.max()-y)/(y.max()-y.min())*.82+.09;poly(a,list(zip(x,y)));shapes['34_heart']=a
    a=canvas();x=np.linspace(.06,.94,220);top=.25+.08*np.sin((x-.06)/.88*2*math.pi);bot=.75+.08*np.sin((x-.06)/.88*2*math.pi+math.pi);poly(a,list(zip(x,top))+list(zip(x[::-1],bot[::-1])));shapes['35_wave_band']=a
    a=canvas();cv2.ellipse(a,(S//2,S//2),(round(S*.43),round(S*.43)),0,180,360,255,-1,cv2.LINE_AA);shapes['36_semicircle']=a
    a=canvas();cv2.circle(a,(round(S*.46),S//2),round(S*.42),255,-1,cv2.LINE_AA);cv2.circle(a,(round(S*.61),round(S*.43)),round(S*.38),0,-1,cv2.LINE_AA);shapes['37_crescent']=a
    a=canvas();r=round(S*.16);x0,y0,x1,y1=round(S*.08),round(S*.25),round(S*.92),round(S*.75);cv2.rectangle(a,(x0+r,y0),(x1-r,y1),255,-1);cv2.rectangle(a,(x0,y0+r),(x1,y1-r),255,-1);cv2.circle(a,(x0+r,y0+r),r,255,-1,cv2.LINE_AA);cv2.circle(a,(x1-r,y0+r),r,255,-1,cv2.LINE_AA);cv2.circle(a,(x0+r,y1-r),r,255,-1,cv2.LINE_AA);cv2.circle(a,(x1-r,y1-r),r,255,-1,cv2.LINE_AA);shapes['38_rounded_rect']=a
    a=canvas();r=round(S*.23);cv2.rectangle(a,(round(S*.22),round(S*.27)),(round(S*.78),round(S*.73)),255,-1);cv2.circle(a,(round(S*.22),S//2),r,255,-1,cv2.LINE_AA);cv2.circle(a,(round(S*.78),S//2),r,255,-1,cv2.LINE_AA);shapes['39_capsule']=a
    a=canvas();cv2.line(a,(round(S*.08),S//2),(round(S*.92),S//2),255,round(S*.055),cv2.LINE_AA);shapes['40_line']=a
    a=canvas();cv2.rectangle(a,(round(S*.42),round(S*.08)),(round(S*.58),round(S*.92)),255,-1);cv2.rectangle(a,(round(S*.08),round(S*.42)),(round(S*.92),round(S*.58)),255,-1);shapes['41_cross']=a
    a=canvas();p=[]
    for i in range(8):
        r=.44 if i%2==0 else .12;ang=-math.pi/2+i*math.pi/4;p.append((.5+r*math.cos(ang),.5+r*math.sin(ang)))
    poly(a,p);shapes['42_star4']=a
    for name,a in shapes.items():save(name,a)
    print('generated',len(shapes),'in',OUT)

if __name__=='__main__':main()
