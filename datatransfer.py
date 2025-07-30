
import pandas as pd

df = pd.read_excel(
    'exchange_rates_last30d.xlsx',
    index_col='date',
    parse_dates=['date']
)

df_long = (
    df
    .reset_index()
    .melt(
        id_vars=['date'],
        var_name='to_currency',
        value_name='rate'
    )
)

df_long['from_currency'] = 'USD'
df_long['id'] = (
    df_long['from_currency']
    + df_long['to_currency']
    + df_long['date'].dt.strftime('%Y%m%d')
)

df_final = df_long[['id','date','from_currency','to_currency','rate']]
out_csv = 'exchange_rates_with_id.csv'
df_final.to_csv(out_csv, index=False)

print(f"Wrote {len(df_final)} rows to {out_csv}")
