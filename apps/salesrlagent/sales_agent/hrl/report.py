"""Standalone reward curves from actual Monitor CSV episode records."""
import csv
from pathlib import Path

def reward_curves(directory):
    root=Path(directory);series={}
    for name in ['strategy','voice','strategy_no_information']:
        path=root/f'{name}.monitor.csv'
        if not path.exists():continue
        with path.open() as f:
            next(f);rows=list(csv.DictReader(f))
        values=[float(r['r']) for r in rows]
        series[name]=[(i,sum(values[max(0,i-49):i+1])/len(values[max(0,i-49):i+1])) for i in range(0,len(values),max(1,len(values)//300))]
    pieces=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="800" viewBox="0 0 1000 800"><rect width="1000" height="800" fill="white"/><text x="30" y="30" font-size="22">Synthetic training reward — rolling 50-episode mean</text>']
    for row,(name,points) in enumerate(series.items()):
        y=70+row*235;low=min(v for _,v in points);high=max(v for _,v in points);last=max(i for i,_ in points)
        coords=' '.join(f'{90+i/max(1,last)*860:.1f},{y+180-(v-low)/max(.01,high-low)*150:.1f}' for i,v in points)
        pieces.extend([f'<text x="30" y="{y}" font-size="18">{name} | reward range {low:.2f} to {high:.2f}</text>',f'<polyline points="{coords}" fill="none" stroke="#245944" stroke-width="2"/>',f'<text x="90" y="{y+205}" font-size="14">Episode 0</text><text x="820" y="{y+205}" font-size="14">Episode {last}</text>'])
    pieces.append('</svg>');(root/'reward-curves.svg').write_text(''.join(pieces))
