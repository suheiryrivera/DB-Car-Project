create table vehicle_kind(
    name text,
    vehicle_kind_id bigint primary key);

create table fuel_type(
    name text,
    fuel_type_id bigint primary key);

create table vehicle_status(
    name text,
    vehicle_status_id bigint primary key);

create table parking_area(
    name text,
    capacity bigint,
    geom geometry(polygon, 4326),
    created_at timestamp,
    parking_area_id bigint primary key);

create table vehicle_type(
    vehicle_kind_id bigint references vehicle_kind(vehicle_kind_id),
    fuel_type_id bigint references fuel_type(fuel_type_id),
    emissions_rating double precision,
    created_at timestamp,
    vehicle_type_id bigint primary key);

create table driver(
    first_name text,
    last_name text,
    license_number text,
    hired_at timestamp,
    driver_id bigint primary key);

create table vehicle(
    vehicle_type_id bigint references vehicle_type(vehicle_type_id),
    vehicle_status_id bigint references vehicle_status(vehicle_status_id),
    plate_number text,
    make text,
    model text,
    year bigint,
    created_at timestamp,
    vehicle_id bigint primary key);

create table road_segment(
    name text,
    speed_limit_kph bigint,
    geom geometry(linestring, 4326),
    created_at timestamp,
    is_oneway boolean,
    direction text,
    road_id bigint primary key);

create table vehicle_assignment(
    vehicle_id bigint references vehicle(vehicle_id),
    driver_id bigint references driver(driver_id),
    assigned_from timestamp,
    assigned_to timestamp,
    assignment_id bigint primary key);

create table location_ping(
    vehicle_id bigint references vehicle(vehicle_id),
    ts timestamp,
    geom geometry(point, 4326),
    speed_kph double precision,
    heading_deg double precision,
    ping_id bigint primary key);

create table trip(
    vehicle_id bigint references vehicle(vehicle_id),
    start_ts timestamp,
    end_ts timestamp,
    start_geom geometry(point, 4326),
    end_geom geometry(point, 4326),
    distance_km double precision,
    trip_id bigint primary key);
