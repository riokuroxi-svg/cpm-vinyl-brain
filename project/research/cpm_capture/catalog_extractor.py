#!/usr/bin/env python3
"""Extrae candidatos de vinilos desde capturas o una grabación de pantalla.

No inspecciona el APK. Solo procesa píxeles visibles de la interfaz.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def dhash(image: np.ndarray, size=16) -> int:
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY) if image.ndim==3 else image
    small=cv2.resize(gray,(size+1,size),interpolation=cv2.INTER_AREA)
    bits=small[:,1:]>small[:,:-1]
    value=0
    for bit in bits.ravel(): value=(value<<1)|int(bit)
    return value


def hamming(a:int,b:int)->int:
    return (a^b).bit_count()


def iter_frames(path:Path,every_seconds:float):
    if path.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}:
        frame=cv2.imread(str(path));
        if frame is not None: yield 0,frame
        return
    cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS) or 30
    step=max(1,round(fps*every_seconds));idx=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        if idx%step==0:yield idx,frame
        idx+=1
    cap.release()


def crop_layout(frame,layout):
    h,w=frame.shape[:2]
    bar=layout['barNormalized'];x0=round(bar[0]*w);y0=round(bar[1]*h);x1=round(bar[2]*w);y1=round(bar[3]*h)
    slot_w=layout.get('slotWidthNormalized',.0583)*w
    slots=layout.get('visibleSlots',14)
    start=x0+layout.get('slotOffsetNormalized',0)*w
    result=[]
    for i in range(slots):
        sx=round(start+i*slot_w);ex=round(start+(i+1)*slot_w)
        if ex>x1:break
        tile=frame[y0:y1,sx:ex]
        if tile.size:result.append((i,tile,(sx,y0,ex,y1)))
    return result


def normalize_thumb(tile,layout):
    h,w=tile.shape[:2]
    t=layout.get('thumbnailFraction',[.08,.04,.92,.72])
    x0,y0,x1,y1=round(t[0]*w),round(t[1]*h),round(t[2]*w),round(t[3]*h)
    crop=tile[y0:y1,x0:x1]
    # Neutralizar borde verde de selección recortando y normalizando fondo.
    return cv2.resize(crop,(96,96),interpolation=cv2.INTER_AREA)


def contact_sheet(items,path):
    cols=8;cell=150;label_h=34;rows=math.ceil(len(items)/cols)
    out=Image.new('RGB',(cols*cell,rows*(cell+label_h)),(24,27,32));d=ImageDraw.Draw(out)
    try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',14)
    except:font=ImageFont.load_default()
    for i,item in enumerate(items):
        im=Image.open(item['file']).convert('RGB');im.thumbnail((128,128),Image.Resampling.LANCZOS)
        x=(i%cols)*cell+(cell-im.width)//2;y=(i//cols)*(cell+label_h)+(128-im.height)//2
        out.paste(im,(x,y));d.text(((i%cols)*cell+8,(i//cols)*(cell+label_h)+132),f"{i:03d}",font=font,fill='white')
    out.save(path,optimize=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('inputs',nargs='+',type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--layout',type=Path)
    ap.add_argument('--every',type=float,default=.20)
    ap.add_argument('--dedup-distance',type=int,default=18)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    layout=json.loads((args.layout or Path(__file__).with_name('layout_2400x1080.json')).read_text())
    items=[];hashes=[]
    for source in args.inputs:
        for frame_idx,frame in iter_frames(source,args.every):
            for slot,tile,box in crop_layout(frame,layout):
                thumb=normalize_thumb(tile,layout);code=dhash(thumb)
                nearest=min((hamming(code,x) for x in hashes),default=999)
                if nearest<=args.dedup_distance:continue
                idx=len(items);file=args.out/f'candidate_{idx:03d}.png'
                cv2.imwrite(str(file),tile);hashes.append(code)
                items.append({'candidateId':idx,'file':str(file),'source':str(source),'frame':frame_idx,'slot':slot,'box':list(box),'hash':hex(code),'needsReview':True})
    (args.out/'catalog_candidates.json').write_text(json.dumps({'format':'cpm-visible-catalog','version':'0.1','layout':layout,'count':len(items),'items':items},indent=2,ensure_ascii=False),encoding='utf-8')
    if items:contact_sheet(items,args.out/'CATALOG_CONTACT_SHEET.png')
    print(f'Candidatos únicos: {len(items)} → {args.out}')

if __name__=='__main__':main()
