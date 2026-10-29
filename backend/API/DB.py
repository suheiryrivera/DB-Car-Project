import psycopg2
import os

class VehicleAssignmentDAO:
    def __init__(self):
        self.pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.environ["DATABASE_URL"]
        )