#!/usr/bin/env python3
"""Ajusta valor editor → píxel usando capturas de un marcador coloreado."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import cv2
import numpy as np
from sklearn.linear_model import LinearRegression


def parse_roi(s):return tuple(map(int,s.split(',')))
def hexrgb(s):s=s.lstrip('#');return np.array([int(s[i:i+2],16) for i in (0,2,4)],np.float32)

def detect(path,roi,target,tol):
    bgr=cv2.imread(str(path));rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB);x,y,w,h=roi;crop=rgb[y:y+h,x:x+w]
    dist=np.linalg.norm(crop.astype(np.float32)-target,axis=2);mask=(dist<tol).astype(np.uint8)
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours:return None
    c=max(contours,key=cv2.contourArea);(cx,cy),(rw,rh),angle=cv2.minAreaRect(c)
    return {'pixelX':cx+x,'pixelY':cy+y,'pixelWidth':rw,'pixelHeight':rh,'pixelAngle':angle,'area':cv2.contourArea(c)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--roi',required=True,help='x,y,w,h');ap.add_argument('--marker-color',default='#39FF14');ap.add_argument('--tolerance',type=float,default=65)
    args=ap.parse_args();roi=parse_roi(args.roi);target=hexrgb(args.marker_color);rows=[]
    with args.manifest.open(newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            d=detect(Path(row['file']),roi,target,args.tolerance)
            if d:rows.append({**row,**d})
    if len(rows)<4:raise SystemExit('Se necesitan al menos 4 detecciones válidas')
    X=np.array([[float(r['editorX']),float(r['editorY'])] for r in rows]);px=np.array([r['pixelX'] for r in rows]);py=np.array([r['pixelY'] for r in rows])
    mx=LinearRegression().fit(X,px);my=LinearRegression().fit(X,py)
    pred=np.c_[mx.predict(X),my.predict(X)];actual=np.c_[px,py];rmse=float(np.sqrt(np.mean((pred-actual)**2)))
    result={'format':'cpm-coordinate-calibration','samples':rows,'mapping':{'pixelX':{'intercept':float(mx.intercept_),'editorX':float(mx.coef_[0]),'editorY':float(mx.coef_[1])},'pixelY':{'intercept':float(my.intercept_),'editorX':float(my.coef_[0]),'editorY':float(my.coef_[1])}},'rmsePixels':rmse,'roi':list(roi),'markerColor':args.marker_color}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print('RMSE',rmse,args.out)

if __name__=='__main__':main()
