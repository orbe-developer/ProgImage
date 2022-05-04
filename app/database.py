from datetime import datetime
from peewee import *

# Connect to the database.
pg_db = PostgresqlDatabase('heycar_db',
                           user='postgres',
                           password='postgres',
                           host='localhost',
                           port=5432)


""" class Py3Blob(BlobField):
    def python_value(self, value):
        if isinstance(value, memoryview):
            return value.tobytes()
        else:
            return super().python_value(value)
 """

class Image(Model):
    # image = CharField()
    content_type = CharField()
    # image = Py3Blob()
    image = BlobField() 
    # image = BinaryUUIDField()
    description = CharField(max_length=50)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = pg_db
        table_name = 'images'
