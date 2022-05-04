from datetime import datetime
from peewee import *

# Connect to the database.
pg_db = PostgresqlDatabase('heycar_db',
                           user='postgres',
                           password='postgres',
                           host='localhost',
                           port=5432)


class Image(Model):
    content_type = CharField()
    image = BlobField()
    description = CharField(max_length=50)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = pg_db
        table_name = 'images'
