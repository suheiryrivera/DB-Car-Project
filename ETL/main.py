import psycopg2
import pandas as pd

# URL connection
url = ('postgresql://suheiry:PiMw0t7wnl08ibDqaFjTkQbVcttBetXR'
       '@dpg-db3h3fbtqb8s73dvp3a0-a.virginia-postgres.render.com'
       '/newdb')

# DB connection
conn = psycopg2.connect(url)
# Create cursor and pass query
cur = conn.cursor()

# tables = ['vehicle_kind', 'fuel_type', 'vehicle_type', 'vehicle_status',
#           'parking_area', 'driver', 'vehicle', 'road_segment',
#           'vehicle_assignment', 'location_ping', 'trip']

###########################INSERT ROW###############################
# Vehicle Kind Table
print("Inserting data into vehicle_kind table...", flush=True)
df = pd.read_parquet('vehicle_kind.parquet', engine='pyarrow')
for x in range(len(df)):
    name = df['name'].iloc[x]
    vehicle_kind_id = int(df['vehicle_kind_id'].iloc[x])
    query = """INSERT INTO vehicle_kind(name, vehicle_kind_id)
                VALUES (%s, %s)"""
    name = name
    vehicle_kind_id = vehicle_kind_id
    cur.execute(query, (name, vehicle_kind_id))

# Fuel Type Table
print("Inserting data into fuel_type table...", flush=True)
df = pd.read_parquet('fuel_type.parquet', engine='pyarrow')
for x in range(len(df)):
    name = df['name'].iloc[x]
    fuel_type_id = int(df['fuel_type_id'].iloc[x])
    query = """INSERT INTO fuel_type(name, fuel_type_id)
                VALUES (%s, %s)"""
    name = name
    fuel_type_id = fuel_type_id
    cur.execute(query, (name, fuel_type_id))

# Vehicle Status Table
print("Inserting data into vehicle_status table...", flush=True)
df = pd.read_parquet('vehicle_status.parquet', engine='pyarrow')
for x in range(len(df)):
    name = df['name'].iloc[x]
    vehicle_status_id = int(df['vehicle_status_id'].iloc[x])
    query = """INSERT INTO vehicle_status(name, vehicle_status_id)
                VALUES (%s, %s)"""
    name = name
    vehicle_status_id = vehicle_status_id
    cur.execute(query, (name, vehicle_status_id))

# Parking Area Table
print("Inserting data into parking_area table...", flush=True)
df = pd.read_parquet('parking_area.parquet', engine='pyarrow')
for x in range(len(df)):
    name = df['name'].iloc[x]
    capacity = int(df['capacity'].iloc[x])
    geom = df['geom'].iloc[x]
    created_at = df['created_at'].iloc[x]
    parking_area_id = int(df['parking_area_id'].iloc[x])
    query = """INSERT INTO parking_area(name, capacity, geom, created_at, parking_area_id)
                VALUES (%s, %s, %s, %s, %s)"""
    name = name
    capacity = capacity
    geom = geom
    created_at = created_at
    parking_area_id = parking_area_id
    cur.execute(query, (name, capacity, geom, created_at, parking_area_id))

# Vehicle Type Table
print("Inserting data into vehicle_type table...", flush=True)
df = pd.read_parquet('vehicle_type.parquet', engine='pyarrow')
for x in range(len(df)):
    vehicle_kind_id = int(df['vehicle_kind_id'].iloc[x])
    fuel_type_id = int(df['fuel_type_id'].iloc[x])
    emissions_rating = float(df['emissions_rating'].iloc[x])
    created_at = df['created_at'].iloc[x]
    vehicle_type_id = int(df['vehicle_type_id'].iloc[x])
    query = """INSERT INTO vehicle_type(vehicle_kind_id, fuel_type_id, emissions_rating, created_at, vehicle_type_id)
                VALUES (%s, %s, %s, %s, %s)"""
    vehicle_kind_id = vehicle_kind_id
    fuel_type_id = fuel_type_id
    emissions_rating = emissions_rating
    created_at = created_at
    vehicle_type_id = vehicle_type_id
    cur.execute(query, (vehicle_kind_id, fuel_type_id, emissions_rating, created_at, vehicle_type_id))

# Driver Table
print("Inserting data into driver table...", flush=True)
df = pd.read_parquet('driver.parquet', engine='pyarrow')
for x in range(len(df)):
    first_name = df['first_name'].iloc[x]
    last_name = df['last_name'].iloc[x]
    license_number = df['license_number'].iloc[x]
    hired_at = df['hired_at'].iloc[x]
    driver_id = int(df['driver_id'].iloc[x])
    query = """INSERT INTO driver(first_name, last_name, license_number, hired_at, driver_id)
                VALUES (%s, %s, %s, %s, %s)"""
    first_name = first_name
    last_name = last_name
    license_number = license_number
    hired_at = hired_at
    driver_id = driver_id
    cur.execute(query, (first_name, last_name, license_number, hired_at, driver_id))

# Vehicle Table
print("Inserting data into vehicle table...", flush=True)
df = pd.read_parquet('vehicle.parquet', engine='pyarrow')
for x in range(len(df)):
    vehicle_type_id = int(df['vehicle_type_id'].iloc[x])
    vehicle_status_id = int(df['vehicle_status_id'].iloc[x])
    plate_number = df['plate_number'].iloc[x]
    make = df['make'].iloc[x]
    model = df['model'].iloc[x]
    year = int(df['year'].iloc[x])
    created_at = df['created_at'].iloc[x]
    vehicle_id = int(df['vehicle_id'].iloc[x])
    query = """INSERT INTO vehicle(vehicle_type_id, vehicle_status_id, plate_number, make, model, year, created_at, vehicle_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    vehicle_type_id = vehicle_type_id
    vehicle_status_id = vehicle_status_id
    plate_number = plate_number
    make = make
    model = model
    year = year
    created_at = created_at
    vehicle_id = vehicle_id
    cur.execute(query, (vehicle_type_id, vehicle_status_id, plate_number, make, model, year, created_at, vehicle_id))

# Road Segment Table
print("Inserting data into road_segment table... Takes approx. 10 minutes", flush=True)
df = pd.read_parquet('road_segment.parquet', engine='pyarrow')
for x in range(len(df)):
    name = df['name'].iloc[x]
    speed_limit_kph = int(df['speed_limit_kph'].iloc[x])
    geom = df['geom'].iloc[x]
    created_at = df['created_at'].iloc[x]
    is_oneway = bool(df['is_oneway'].iloc[x])
    direction = df['direction'].iloc[x]
    road_id = int(df['road_id'].iloc[x])
    query = """INSERT INTO road_segment(name, speed_limit_kph, geom, created_at, is_oneway, direction, road_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    name = name
    speed_limit_kph = speed_limit_kph
    geom = geom
    created_at = created_at
    is_oneway = is_oneway
    direction = direction
    road_id = road_id
    cur.execute(query, (name, speed_limit_kph, geom, created_at, is_oneway, direction, road_id))

# Vehicle Assignment Table
print("Inserting data into vehicle_assignment table...", flush=True)
df = pd.read_parquet('vehicle_assignment.parquet', engine='pyarrow')
for x in range(len(df)):
    vehicle_id = int(df['vehicle_id'].iloc[x])
    driver_id = int(df['driver_id'].iloc[x])
    assigned_from = None #(df['assigned_from'].iloc[x])
    assigned_to = None #df['assigned_to'].iloc[x]
    assignment_id = int(df['assignment_id'].iloc[x])
    query = """INSERT INTO vehicle_assignment(vehicle_id, driver_id, assigned_from, assigned_to, assignment_id)
                VALUES (%s, %s, %s, %s, %s);"""
    vehicle_id = vehicle_id
    driver_id = driver_id
    assigned_from = assigned_from
    assigned_to = assigned_to
    assignment_id = int(assignment_id)
    cur.execute(query, (vehicle_id, driver_id, assigned_from, assigned_to, assignment_id))

# Location Ping Table
print("Inserting data into location_ping table... Takes approx. 50 minutes", flush=True)
df = pd.read_parquet('location_ping.parquet', engine='pyarrow')
for x in range(len(df)):
    vehicle_id = int(df['vehicle_id'].iloc[x])
    ts = df['ts'].iloc[x]
    geom = df['geom'].iloc[x]
    speed_kph = float(df['speed_kph'].iloc[x])
    heading_deg = float(df['heading_deg'].iloc[x])
    ping_id = int(df['ping_id'].iloc[x])
    query = """INSERT INTO location_ping(vehicle_id, ts, geom, speed_kph, heading_deg, ping_id)
                VALUES (%s, %s, %s, %s, %s, %s);"""
    vehicle_id = vehicle_id
    ts = ts;
    geom = geom;
    speed_kph = speed_kph;
    heading_deg = heading_deg;
    ping_id = ping_id;
    cur.execute(query, (vehicle_id, ts, geom, speed_kph, heading_deg, ping_id))

# Trip Table
print("Inserting data into trip table...", flush=True)
df = pd.read_parquet('trip.parquet', engine='pyarrow')
for x in range(len(df)):
    vehicle_id = int(df['vehicle_id'].iloc[x])
    start_ts = df['start_ts'].iloc[x]
    end_ts = df['end_ts'].iloc[x]
    start_geom = df['start_geom'].iloc[x]
    end_geom = df['end_geom'].iloc[x]
    distance_km = float(df['distance_km'].iloc[x])
    trip_id = int(df['trip_id'].iloc[x])
    query = """INSERT INTO trip(vehicle_id, start_ts, end_ts, start_geom, end_geom, distance_km, trip_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s);"""
    vehicle_id = vehicle_id
    start_ts = start_ts
    end_ts = end_ts
    start_geom = start_geom
    end_geom = end_geom
    distance_km = distance_km
    trip_id = trip_id
    cur.execute(query, (vehicle_id, start_ts, end_ts, start_geom, end_geom, distance_km, trip_id))

conn.commit()
##########################LOOPS####################################
# len() es de python y .iloc[] es de pandas
# for x in range(len(df)):
#     first_name = df['first_name'].iloc[x]
#     print(first_name)

# similar to enhance for loop
# for first_name in df['first_name']:
#     print(first_name)

# for table in tables:
#     .........
#################################################################

cur.close()
conn.close()