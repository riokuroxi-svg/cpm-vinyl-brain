#!/usr/bin/env python3
"""Orquestador de pruebas CPM Vinyl Brain 0.5.

Ejecuta análisis → subpartes → baseline 0.3 → pool virtual ADD/CUT → Optimize & Reduce.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROFILES = {
    "quick": {"analysis_side":512,"solver_side":256,"candidates":180,"refinements":60,"attempts":1,
              "virtual_layers":256,"correction_candidates":35,"correction_refinements":10},
    "balanced": {"analysis_side":768,"solver_side":320,"candidates":240,"refinements":80,"attempts":1,
                 "virtual_layers":430,"correction_candidates":55,"correction_refinements":14},
    "quality": {"analysis_side":768,"solver_side":384,"candidates":260,"refinements":90,"attempts":2,
                "virtual_layers":500,"correction_candidates":70,"correction_refinements":18},
}


def run(command):
    print("\n$", " ".join(map(str,command)), flush=True)
    subprocess.run(list(map(str,command)), check=True)


def main():
    ap=argparse.ArgumentParser(description="Pipeline completo del Cerebro de vinilos")
    ap.add_argument('--input',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--shapes',type=Path)
    ap.add_argument('--profile',choices=PROFILES,default='quality')
    ap.add_argument('--seed',type=int,default=20260720)
    args=ap.parse_args()
    here=Path(__file__).resolve().parent
    project=here.parents[1]
    shapes=args.shapes or project/'src/main/resources/shapes'
    cfg=PROFILES[args.profile]
    analysis=args.out/'01_analysis';subparts=args.out/'02_subparts';final=args.out/'03_baseline_v03';optimized=args.out/'04_optimize_reduce_v05'
    args.out.mkdir(parents=True,exist_ok=True)

    run([sys.executable,here/'analyzer.py','--input',args.input,'--out',analysis,
         '--max-side',cfg['analysis_side'],'--colors',20,'--seed',args.seed])
    run([sys.executable,here/'subparts.py','--input',args.input,'--out',subparts,
         '--max-side',cfg['analysis_side']])
    run([sys.executable,here/'solver_final.py','--graph',subparts/'layer_graph.json',
         '--shapes',shapes,'--input',args.input,'--out',final,
         '--max-side',cfg['solver_side'],'--candidates',cfg['candidates'],
         '--refinements',cfg['refinements'],'--attempts',cfg['attempts'],'--seed',args.seed])
    run([sys.executable,here/'solver_v05.py','--base-recipe',final/'final_recipe.json',
         '--semantic-target',final/'semantic_target.png','--graph',subparts/'layer_graph.json',
         '--shapes',shapes,'--out',optimized,'--work-side',min(256,cfg['solver_side']),
         '--virtual-layers',cfg['virtual_layers'],'--candidates',cfg['correction_candidates'],
         '--refinements',cfg['correction_refinements'],'--seed',args.seed+1])

    recipe=json.loads((optimized/'recipe_430.json').read_text(encoding='utf-8'))
    comparison=json.loads((optimized/'comparison_metrics.json').read_text(encoding='utf-8'))
    manifest={
        'format':'cpm-brain-test-run','version':'0.5.0','createdAt':datetime.now(timezone.utc).isoformat(),
        'input':str(args.input),'profile':args.profile,'seed':args.seed,'configuration':cfg,
        'outputs':{
            'progressivePreview':'01_analysis/VISTA_PREVIA_ANALIZADOR.png',
            'layerGraph':'02_subparts/layer_graph.json',
            'partsPreview':'02_subparts/VISTA_PREVIA_0_2B.png',
            'baselineRecipe':'03_baseline_v03/final_recipe.json',
            'recipe064':'04_optimize_reduce_v05/recipe_064.json',
            'recipe128':'04_optimize_reduce_v05/recipe_128.json',
            'recipe256':'04_optimize_reduce_v05/recipe_256.json',
            'recipe430':'04_optimize_reduce_v05/recipe_430.json',
            'comparison':'04_optimize_reduce_v05/FINAL_COMPARISON_03_VS_05.png'
        },
        'metrics':recipe['metrics'],'comparison':comparison
    }
    (args.out/'run_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print("\nPipeline completado:",args.out)
    print(json.dumps(recipe['metrics'],indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
