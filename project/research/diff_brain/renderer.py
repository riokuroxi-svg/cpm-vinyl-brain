"""Renderizador diferenciable experimental para Brain 1.0.

Requiere PyTorch. Optimiza simultáneamente posición, escala, rotación y selección
suave de figura dentro de un bloque semántico. No accede al juego ni al APK.
"""
from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class DifferentiableVinylRenderer(nn.Module):
    def __init__(self, shape_bank: torch.Tensor, layer_count: int, canvas_hw: tuple[int,int]):
        super().__init__()
        if shape_bank.ndim != 4 or shape_bank.shape[1] != 1:
            raise ValueError('shape_bank debe ser [K,1,H,W]')
        self.register_buffer('shape_bank', shape_bank.clamp(0,1))
        self.layer_count=layer_count
        self.canvas_hw=canvas_hw
        k=shape_bank.shape[0]
        self.position=nn.Parameter(torch.zeros(layer_count,2))
        self.log_scale=nn.Parameter(torch.full((layer_count,2),-1.2))
        self.angle=nn.Parameter(torch.zeros(layer_count))
        self.shape_logits=nn.Parameter(torch.zeros(layer_count,k))
        self.opacity_logits=nn.Parameter(torch.full((layer_count,),2.5))
        self.color_logits=nn.Parameter(torch.zeros(layer_count,3))

    def transformed_masks(self,temperature:float=1.0):
        n=self.layer_count;h,w=self.canvas_hw
        weights=F.gumbel_softmax(self.shape_logits,tau=temperature,hard=False,dim=1)
        source=torch.einsum('nk,kchw->nchw',weights,self.shape_bank)
        pos=torch.tanh(self.position)
        scale=torch.exp(self.log_scale).clamp(.015,2.0)
        c=torch.cos(self.angle);s=torch.sin(self.angle)
        # affine_grid transforma coordenadas de salida hacia la fuente.
        invx=1/scale[:,0];invy=1/scale[:,1]
        theta=torch.zeros(n,2,3,device=source.device,dtype=source.dtype)
        theta[:,0,0]= c*invx;theta[:,0,1]= s*invx
        theta[:,1,0]=-s*invy;theta[:,1,1]= c*invy
        theta[:,:,2]=-pos
        grid=F.affine_grid(theta,(n,1,h,w),align_corners=False)
        masks=F.grid_sample(source,grid,mode='bilinear',padding_mode='zeros',align_corners=False)
        return masks[:,0]

    def forward(self,background:torch.Tensor,temperature:float=1.0):
        masks=self.transformed_masks(temperature)
        alpha=torch.sigmoid(self.opacity_logits)[:,None,None]*masks
        colors=torch.sigmoid(self.color_logits)[:, :,None,None]
        canvas=background.expand(3,*self.canvas_hw)
        for i in range(self.layer_count):
            a=alpha[i][None]
            canvas=colors[i]*a+canvas*(1-a)
        return canvas.clamp(0,1),masks


def sobel_edges(image:torch.Tensor):
    gray=(image*torch.tensor([.299,.587,.114],device=image.device)[:,None,None]).sum(0,keepdim=True)[None]
    kx=torch.tensor([[-1,0,1],[-2,0,2],[-1,0,1]],dtype=image.dtype,device=image.device)[None,None]
    ky=kx.transpose(-1,-2)
    gx=F.conv2d(gray,kx,padding=1);gy=F.conv2d(gray,ky,padding=1)
    return torch.sqrt(gx.square()+gy.square()+1e-8)[0]


def block_loss(rendered,target,masks,allowed_mask,semantic_weight=None,layer_lambda=1e-4):
    weight=semantic_weight if semantic_weight is not None else 1.0
    color=(torch.abs(rendered-target)*weight).mean()
    edge=torch.abs(sobel_edges(rendered)-sobel_edges(target)).mean()
    union=1-torch.prod(1-masks.clamp(0,1),dim=0)
    outside=(union*(1-allowed_mask)).mean()
    active=masks.mean(dim=(1,2)).sum()
    return color+.35*edge+2.5*outside+layer_lambda*active,{
        'color':color.detach(),'edge':edge.detach(),'outside':outside.detach(),'active':active.detach()
    }
