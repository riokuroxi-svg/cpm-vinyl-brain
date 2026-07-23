#!/usr/bin/env python3
"""Convierte una forma visible del editor en PNG blanco con alfa.

Modos: white-on-dark, dark-on-light y green-excess.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def parse_roi(text):return tuple(map(int,text.split(',')))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--image',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--roi',required=True,help='x,y,w,h')
    ap.add_argument('--mode',choices=['white-on-dark','dark-on-light','green-excess'],default='white-on-dark')
    ap.add_argument('--threshold',type=float,default=8)
    ap.add_argument('--repair-horizontal',help='y0,y1 relativos al ROI')
    args=ap.parse_args()
    bgr=cv2.imread(str(args.image));x,y,w,h=parse_roi(args.roi);crop=bgr[y:y+h,x:x+w]
    rgb=cv2.cvtColor(crop,cv2.COLOR_BGR2RGB).astype(np.float32)
    if args.mode=='white-on-dark':
        alpha=np.max(rgb,axis=2)-np.min(rgb,axis=2)*.15
    elif args.mode=='dark-on-light':
        alpha=255-np.mean(rgb,axis=2)
    else:
        r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2];alpha=(g-(r+b)/2)*2.75
    alpha=np.clip((alpha-args.threshold)/(255-args.threshold)*255,0,255)
    if args.repair_horizontal:
        y0,y1=map(int,args.repair_horizontal.split(','));a=max(0,y0-3);b=min(h-1,y1+3)
        top=np.median(alpha[max(0,a-3):a+1],axis=0);bot=np.median(alpha[b:min(h,b+4)],axis=0)
        for yy in range(a,b+1):
            t=(yy-a)/max(1,b-a);alpha[yy]=top*(1-t)+bot*t
    alpha[alpha<2]=0
    ys,xs=np.where(alpha>2)
    if len(xs):
        pad=8;x0=max(0,xs.min()-pad);x1=min(w,xs.max()+pad+1);y0=max(0,ys.min()-pad);y1=min(h,ys.max()+pad+1);alpha=alpha[y0:y1,x0:x1]
    rgba=np.full((*alpha.shape,4),255,np.uint8);rgba[:,:,3]=alpha.astype(np.uint8)
    args.out.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(rgba,'RGBA').save(args.out,optimize=True)
    print(args.out,rgba.shape[1],rgba.shape[0])

if __name__=='__main__':main()
