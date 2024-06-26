from .team_list import TeamList
from database.conn import DBObject

# Import SQLAlchemy MetaData and create_all function
from sqlalchemy import MetaData

# List of all models
tables = [TeamList]

# Initialize the SQLAlchemy connection
db = DBObject()

# Create MetaData object without bind
metadata = MetaData()

# Bind the engine to the MetaData object
metadata.bind = db.engine

# Iterate over each table/model and create its table
for table in tables:
    # Create the table in the database
    table.__table__.create(bind=db.engine, checkfirst=True)
