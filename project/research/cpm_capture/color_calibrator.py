#!/usr/bin/env python3
"""Mide color observado en capturas a partir de un manifiesto HEX/ROI."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
import cv2
import numpy as np
from skimage.color import rgb2lab


def parse_roi(s):return tuple(map(int,s.split(',')))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);args=ap.parse_args();samples=[]
    with args.manifest.open(newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            bgr=cv2.imread(row['file']);x,y,w,h=parse_roi(row['roi']);rgb=cv2.cvtColor(bgr[y:y+h,x:x+w],cv2.COLOR_BGR2RGB)
            # Evitar bordes/reflejos extremos usando percentiles centrales.
            pixels=rgb.reshape(-1,3);lo=np.percentile(pixels,20,axis=0);hi=np.percentile(pixels,80,axis=0);keep=np.all((pixels>=lo)&(pixels<=hi),axis=1);med=np.median(pixels[keep] if keep.any() else pixels,axis=0)
            lab=rgb2lab((med/255).reshape(1,1,3))[0,0]
            samples.append({'file':row['file'],'appliedHex':row['appliedHex'],'roi':row['roi'],'observedRGB':[round(float(v),3) for v in med],'observedLab':[round(float(v),4) for v in lab]})
    result={'format':'cpm-color-calibration','samples':samples,'notes':['iluminación/cámara deben permanecer fijas','ajustar modelo aplicadoHex→observedLab en la siguiente fase']}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print(len(samples),args.out)
if __name__=='__main__':main()
