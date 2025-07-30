
import requests
import pandas as pd
from datetime import date, timedelta

ACCESS_KEY = 'a88f7d6899aa7427a545d3ae217a589e'
BASE       = 'USD'
SYMBOLS    = ['EUR','JPY','GBP','CNY','HKD','CAD']

end_date   = date.today() - timedelta(days=1)
start_date = end_date   - timedelta(days=99)

url    = 'http://api.currencylayer.com/timeframe'
params = {
    'access_key': ACCESS_KEY,
    'start_date': start_date.isoformat(),
    'end_date':   end_date.isoformat(),
    'source':     BASE,
    'currencies': ','.join(SYMBOLS),
}

resp = requests.get(url, params=params)
resp.raise_for_status()
data = resp.json()


if not data.get('success', False) or 'quotes' not in data:
    raise RuntimeError(f"API error: {data}")

df = pd.DataFrame.from_dict(data['quotes'], orient='index')
df.index.name = 'date'


df.rename(columns=lambda c: c[len(BASE):], inplace=True)
df = df[SYMBOLS]

EXCEL_PATH = 'exchange_rates_last30d.xlsx'
CSV_PATH   = 'exchange_rates_last30d.csv'

df.to_excel(EXCEL_PATH)
df.to_csv(CSV_PATH)

print(f"Wrote {len(df)} rows to:\n • {EXCEL_PATH}\n • {CSV_PATH}")
