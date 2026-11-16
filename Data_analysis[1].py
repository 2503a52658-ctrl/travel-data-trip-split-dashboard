from pathlib import Path
import argparse
import pandas as pd
BASE=Path(__file__).resolve().parent

def analyze(input_path=BASE/'clean_dataset.csv'):
    df=pd.read_csv(input_path,parse_dates=['start_date_clean','end_date_clean'])
    df['year']=df['start_date_clean'].dt.year
    out=BASE/'analysis_outputs'; out.mkdir(exist_ok=True)
    def save_counts(series,name):
        result=series.fillna('Unknown').value_counts().rename_axis('category').reset_index(name='trip_count')
        result.to_csv(out/f'{name}.csv',index=False); return result
    dest=save_counts(df['destination_clean'],'top_destinations')
    accom=save_counts(df['accommodation_type'],'accommodation_counts')
    transport=save_counts(df['transportation_type_clean'],'transportation_counts')
    by_year=df.groupby('year',dropna=False).size().rename('trip_count').reset_index(); by_year.to_csv(out/'trips_by_year.csv',index=False)
    total_accom=df['accommodation_cost'].sum(min_count=1); total_transport=df['transportation_cost'].sum(min_count=1)
    summary=[
        'TRAVEL DATA ANALYSIS SUMMARY',
        f'Records analyzed: {len(df)}',
        f'Unique destinations after conservative alias cleanup: {df.destination_clean.nunique(dropna=True)}',
        f'Average traveler age: {df.traveler_age.mean():.1f}' if df.traveler_age.notna().any() else 'Average traveler age: unavailable',
        f'Average recorded trip duration (days): {df.duration_days_recorded.mean():.2f}',
        f'Mean calculated elapsed duration (days): {df.duration_days_calculated.mean():.2f}',
        f'Accommodation cost sum (numeric source values): {total_accom:.2f}',
        f'Transportation cost sum (numeric source values): {total_transport:.2f}',
        f'Rows where duration agrees with date difference: {int(df.duration_matches_dates.fillna(False).sum())} / {len(df)}',
        '', 'Top destinations by record count:',
    ]
    summary += [f"  {r.category}: {r.trip_count}" for r in dest.head(10).itertuples()]
    summary += ['', 'Most common accommodation types:']
    summary += [f"  {r.category}: {r.trip_count}" for r in accom.head(8).itertuples()]
    summary += ['', 'Most common transportation labels after cleanup:']
    summary += [f"  {r.category}: {r.trip_count}" for r in transport.head(8).itertuples()]
    summary += ['', 'Caution: currency values are summed as recorded after numeric parsing. The source mixes currency notation; treat USD as an assumption pending confirmation. Date readings with ambiguous month/day order should be reviewed using data_cleaning_log.txt.']
    (out/'analysis_summary.txt').write_text('\n'.join(summary),encoding='utf-8')
    print(f'Wrote analysis outputs to {out}')
    return df
if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Summarize the cleaned travel dataset.')
    ap.add_argument('--input',type=Path,default=BASE/'clean_dataset.csv')
    a=ap.parse_args(); analyze(a.input)
