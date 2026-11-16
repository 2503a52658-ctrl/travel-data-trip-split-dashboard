from pathlib import Path
import argparse, html
import pandas as pd
BASE=Path(__file__).resolve().parent

def svg_bar_chart(title, labels, values, color='#247A7A'):
    W,H=960,430; left,right,top,bottom=250,35,75,50; plot_w=W-left-right; plot_h=H-top-bottom
    maxv=max(values or [1]) or 1
    bar_h=min(32,plot_h/max(len(values),1)*0.58); gap=plot_h/max(len(values),1)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}">',
      '<rect width="100%" height="100%" fill="#fbfaf7"/>',f'<text x="32" y="42" font-family="Arial" font-size="24" font-weight="700" fill="#17344B">{html.escape(title)}</text>']
    for i,(lab,val) in enumerate(zip(labels,values)):
        y=top+i*gap+(gap-bar_h)/2; barw=plot_w*val/maxv
        parts.append(f'<text x="{left-12}" y="{y+bar_h*.72:.1f}" text-anchor="end" font-family="Arial" font-size="16" fill="#263746">{html.escape(str(lab))}</text>')
        parts.append(f'<rect x="{left}" y="{y:.1f}" width="{barw:.1f}" height="{bar_h:.1f}" rx="5" fill="{color}"/>')
        parts.append(f'<text x="{left+barw+8:.1f}" y="{y+bar_h*.72:.1f}" font-family="Arial" font-size="15" fill="#263746">{val}</text>')
    parts.append('</svg>'); return ''.join(parts)

def build():
    d=BASE/'analysis_outputs'; d.mkdir(exist_ok=True)
    specs=[('top_destinations.csv','category','trip_count','Top destinations by trip records',10),('accommodation_counts.csv','category','trip_count','Accommodation types',8),('transportation_counts.csv','category','trip_count','Transportation modes',8),('trips_by_year.csv','year','trip_count','Trips by start year',20)]
    blocks=[]
    for filename,label,value,title,limit in specs:
        p=d/filename
        if not p.exists(): raise FileNotFoundError(f'{p} not found. Run Data_analysis.py first.')
        df=pd.read_csv(p).head(limit)
        labels=df[label].fillna('Unknown').astype(str).tolist(); values=pd.to_numeric(df[value],errors='coerce').fillna(0).astype(int).tolist()
        blocks.append(f'<section><h2>{html.escape(title)}</h2>{svg_bar_chart(title,labels,values)}</section>')
    page='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Travel Data Visualizations</title><style>body{font-family:Arial,sans-serif;max-width:1080px;margin:36px auto;padding:0 18px;background:#f1f3f2;color:#243746}h1{color:#12314a}section{background:#fff;padding:20px;margin:20px 0;border-radius:12px;box-shadow:0 2px 8px #0001}svg{width:100%;height:auto}</style></head><body><h1>Travel Data Visualizations</h1><p>Charts are based on the cleaned travel dataset. Counts are record counts, not unique travelers.</p>'''+''.join(blocks)+'''<p><small>Review date interpretations and currency assumptions in data_cleaning_log.txt and README.md.</small></p></body></html>'''
    target=BASE/'travel_data_visualizations.html'; target.write_text(page,encoding='utf-8'); print(f'Wrote {target}')
if __name__=='__main__':
    argparse.ArgumentParser(description='Build self-contained SVG charts from Data_analysis.py outputs.').parse_args(); build()
