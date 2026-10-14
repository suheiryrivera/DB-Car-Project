import psycopg2

# URL connection
url = ('postgresql://suheiry:PiMw0t7wnl08ibDqaFjTkQbVcttBetXR'
       '@dpg-db3h3fbtqb8s73dvp3a0-a.virginia-postgres.render.com'
       '/dbclass_823k')

# DB connection
conn = psycopg2.connect(url)
# Create cursor and pass query
cur = conn.cursor()

cur.execute("DELETE FROM trip;")
cur.execute("DELETE FROM location_ping;")
cur.execute("DELETE FROM vehicle_assignment;")
cur.execute("DELETE FROM road_segment;")
cur.execute("DELETE FROM vehicle;")
cur.execute("DELETE FROM driver;")
cur.execute("DELETE FROM parking_area;")
cur.execute("DELETE FROM vehicle_status;")
cur.execute("DELETE FROM vehicle_type;")
cur.execute("DELETE FROM fuel_type;")
cur.execute("DELETE FROM vehicle_kind;")

conn.commit()

print("\nAll tables deleted")

cur.close()
conn.close()