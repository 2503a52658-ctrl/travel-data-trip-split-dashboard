from pathlib import Path
from datetime import datetime
import argparse, re
import pandas as pd

BASE = Path(__file__).resolve().parent
ALIASES = {
    'paris':'Paris, France','tokyo':'Tokyo, Japan','bali':'Bali, Indonesia',
    'sydney':'Sydney, Australia','sydney, aus':'Sydney, Australia','sydney, australia':'Sydney, Australia',
    'cape town':'Cape Town, South Africa','cape town, sa':'Cape Town, South Africa','cape town, south africa':'Cape Town, South Africa',
    'bangkok':'Bangkok, Thailand','bangkok, thai':'Bangkok, Thailand',
    'phuket':'Phuket, Thailand','phuket, thai':'Phuket, Thailand',
    'london':'London, UK','rome':'Rome, Italy','barcelona':'Barcelona, Spain',
    'new york':'New York, USA','new york city, usa':'New York, USA',
}

def date_candidates(value):
    value = str(value or '').strip()
    if not value: return []
    formats = ['%m-%d-%Y','%m/%d/%Y','%d-%m-%Y','%d/%m/%Y','%Y-%m-%d']
    out=[]
    for fmt in formats:
        try:
            dt=datetime.strptime(value,fmt).date()
            if dt not in out: out.append(dt)
        except ValueError:
            continue
    return out

def parse_date_pair(start_value, end_value, duration):
    starts=date_candidates(start_value); ends=date_candidates(end_value)
    try: expected=int(float(duration))
    except (ValueError,TypeError): expected=None
    # Choose an unambiguous date pair that agrees with the recorded elapsed days.
    for start in starts:
        for end in ends:
            if end >= start and expected is not None and (end-start).days == expected:
                return start,end
    # Otherwise use the preferred month-first reading where it yields a valid sequence.
    for start in starts:
        for end in ends:
            if end >= start: return start,end
    return (starts[0] if starts else None, ends[0] if ends else None)
def parse_cost(value):
    text=str(value or '').strip()
    if not text: return None
    text=text.replace(',','')
    text=re.sub(r'(?i)\bUSD\b','',text).replace('$','').strip()
    m=re.search(r'-?\d+(?:\.\d+)?',text)
    return float(m.group(0)) if m else None

def clean(input_path=BASE/'travel_dataset_raw.tsv', output_path=BASE/'clean_dataset.csv'):
    df=pd.read_csv(input_path,sep='\t',dtype=str,keep_default_na=False)
    df.columns=[re.sub(r'[^a-z0-9]+','_',c.strip().lower()).strip('_') for c in df.columns]
    df=df.replace(r'^\s*$',pd.NA,regex=True)
    df=df.dropna(how='all').copy()
    df=df.dropna(subset=['trip_id','destination']).copy()
    df['trip_id']=pd.to_numeric(df['trip_id'],errors='coerce').astype('Int64')
    df=df.dropna(subset=['trip_id','destination']).copy()
    df['trip_id']=df['trip_id'].astype(int)
    df['destination']=df['destination'].astype('string').str.strip()
    df['destination_clean']=df['destination'].str.lower().map(ALIASES).fillna(df['destination'])
    df['accommodation_type']=df['accommodation_type'].astype('string').str.strip()
    df['transportation_type']=df['transportation_type'].astype('string').str.strip()
    df['transportation_type_clean']=df['transportation_type'].str.lower().replace({'plane':'Flight','airplane':'Flight','flight':'Flight','train':'Train','car rental':'Car rental','bus':'Bus','subway':'Subway','ferry':'Ferry','car':'Car'})
    df['traveler_age']=pd.to_numeric(df['traveler_age'],errors='coerce').astype('Int64')
    df['duration_days_recorded']=pd.to_numeric(df['duration_days'],errors='coerce').astype('Int64')
    date_pairs=[parse_date_pair(s,e,d) for s,e,d in zip(df['start_date'],df['end_date'],df['duration_days_recorded'])]
    df['start_date_clean']=[p[0] for p in date_pairs]
    df['end_date_clean']=[p[1] for p in date_pairs]
    df['start_date_clean']=pd.to_datetime(df['start_date_clean']).dt.strftime('%Y-%m-%d')
    df['end_date_clean']=pd.to_datetime(df['end_date_clean']).dt.strftime('%Y-%m-%d')
    df['accommodation_cost_source']=df['accommodation_cost']
    df['transportation_cost_source']=df['transportation_cost']
    df['accommodation_cost']=df['accommodation_cost'].map(parse_cost)
    df['transportation_cost']=df['transportation_cost'].map(parse_cost)
    df['duration_days_calculated']=(pd.to_datetime(df['end_date_clean'])-pd.to_datetime(df['start_date_clean'])).dt.days.astype('Int64')
    df['duration_matches_dates']=df['duration_days_recorded'].eq(df['duration_days_calculated'])
    df['cost_currency_assumption']='USD (assumed from source examples)'
    # Keep original fields for traceability while adding normalized columns.
    df.to_csv(output_path,index=False)
    log=BASE/'data_cleaning_log.txt'
    log.write_text(f"Input: {Path(input_path).name}\nOutput: {Path(output_path).name}\nRows retained: {len(df)}\nTrip IDs unique: {df['trip_id'].is_unique}\nRows with missing start/end date: {int(df['start_date_clean'].isna().sum()) + int(df['end_date_clean'].isna().sum())}\nRows where recorded duration differs from date difference: {int((~df['duration_matches_dates'].fillna(False)).sum())}\nCurrency: values are converted to numbers; USD is an assumption because the source mixes bare numbers, $ signs, and USD labels.\nAmbiguous dates: month-first interpretation is preferred for ambiguous numeric dates. Review the mismatches before final analysis.\n",encoding='utf-8')
    print(f'Wrote {output_path} ({len(df)} records)')
    return df

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Clean the supplied travel-trip TSV dataset.')
    ap.add_argument('--input',type=Path,default=BASE/'travel_dataset_raw.tsv')
    ap.add_argument('--output',type=Path,default=BASE/'clean_dataset.csv')
    a=ap.parse_args(); clean(a.input,a.output)



