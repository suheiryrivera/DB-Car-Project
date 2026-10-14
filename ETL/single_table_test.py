import psycopg2
import pandas as pd

# URL connection
url = ('postgresql://suheiry:PiMw0t7wnl08ibDqaFjTkQbVcttBetXR'
       '@dpg-db3h3fbtqb8s73dvp3a0-a.virginia-postgres.render.com'
       '/dbclass_823k')

# DB connection
conn = psycopg2.connect(url)
# Create cursor and pass query
cur = conn.cursor()

# Test desired table
table = "location_ping"

print('Table in the DB')
query = f"SELECT * FROM {table};"
cur.execute(query)
for row in cur:
    print(row)
print()

print('Data from the parquet file')
df = pd.read_parquet(f'{table}.parquet', engine='pyarrow')
print(df)

cur.close()
conn.close()