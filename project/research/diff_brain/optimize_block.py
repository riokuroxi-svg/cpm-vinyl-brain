#!/usr/bin/env python3
"""Optimiza un bloque con el renderizador diferenciable.

Esqueleto ejecutable en Colab/GPU tras instalar torch. La exportación final
convierte selección suave a IDs discretos y poda capas de baja importancia.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from renderer import DifferentiableVinylRenderer,block_loss


def load_mask(path,size):
    im=Image.open(path).convert('L').resize((size[1],size[0]),Image.Resampling.LANCZOS)
    return torch.from_numpy(np.asarray(im,dtype=np.float32)/255)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--shapes',type=Path,required=True);ap.add_argument('--target',type=Path,required=True)
    ap.add_argument('--allowed-mask',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--layers',type=int,default=25);ap.add_argument('--steps',type=int,default=1200);ap.add_argument('--size',type=int,default=192)
    args=ap.parse_args();device='cuda' if torch.cuda.is_available() else 'cpu';hw=(args.size,args.size)
    shape_files=sorted(args.shapes.glob('*.png'));bank=[]
    for p in shape_files:
        alpha=Image.open(p).convert('RGBA').getchannel('A').resize((128,128),Image.Resampling.LANCZOS)
        bank.append(torch.from_numpy(np.asarray(alpha,dtype=np.float32)/255)[None])
    bank=torch.stack(bank).to(device)
    target_im=Image.open(args.target).convert('RGB').resize((args.size,args.size),Image.Resampling.LANCZOS)
    target=torch.from_numpy(np.asarray(target_im,dtype=np.float32).transpose(2,0,1)/255).to(device)
    allowed=load_mask(args.allowed_mask,hw).to(device)
    background=torch.zeros(3,1,1,device=device)
    model=DifferentiableVinylRenderer(bank,args.layers,hw).to(device)
    opt=torch.optim.Adam(model.parameters(),lr=.025)
    log=[]
    for step in range(args.steps):
        temperature=max(.15,1-step/args.steps)
        rendered,masks=model(background,temperature)
        loss,parts=block_loss(rendered,target,masks,allowed)
        opt.zero_grad();loss.backward();opt.step()
        if step%50==0:
            item={'step':step,'loss':float(loss.detach()),**{k:float(v) for k,v in parts.items()}};log.append(item);print(item)
    args.out.mkdir(parents=True,exist_ok=True)
    Image.fromarray((rendered.detach().cpu().numpy().transpose(1,2,0)*255).astype(np.uint8)).save(args.out/'preview.png')
    probs=torch.softmax(model.shape_logits,dim=1);ids=probs.argmax(1).detach().cpu().tolist()
    recipe=[]
    for i in range(args.layers):
        recipe.append({'index':i,'shapeId':shape_files[ids[i]].stem,'x':float(torch.tanh(model.position[i,0]).detach()),'y':float(torch.tanh(model.position[i,1]).detach()),
                       'scaleX':float(torch.exp(model.log_scale[i,0]).detach()),'scaleY':float(torch.exp(model.log_scale[i,1]).detach()),
                       'rotationDeg':float(torch.rad2deg(model.angle[i]).detach()),'opacity':float(torch.sigmoid(model.opacity_logits[i]).detach()),
                       'color':[float(x) for x in torch.sigmoid(model.color_logits[i]).detach().cpu()]})
    (args.out/'recipe_soft.json').write_text(json.dumps({'device':device,'layers':recipe,'log':log},indent=2),encoding='utf-8')
if __name__=='__main__':main()
