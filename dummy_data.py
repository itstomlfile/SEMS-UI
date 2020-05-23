import random
import redis
import json


def generate_values(key):

    values = list()

    for i in range(0, 96):
        values.append(random.randrange(1, 100))

    return {key: values}


def populate(key):
    r = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)

    r.set(key, json.dumps(generate_values(key)))


if __name__ == '__main__':
    project_name = "GREENWICH"
    ID = "20200420140137"
    name = "dummy"
    key = project_name + ":DATA:" + ID + ":" + name
    populate(key)
