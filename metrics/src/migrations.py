from peewee import *
from models import db, Address, TransactionCount


def create_tables():
    with db:
        db.create_tables([Address, TransactionCount])


if __name__ == "__main__":
    create_tables()
    print("Tables created successfully")
