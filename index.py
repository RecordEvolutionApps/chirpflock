import asyncio
import random

from ironflock import IronFlock
from datetime import datetime
import os
DEVICE_NAME = os.environ['DEVICE_NAME']

# Load a location path to simulate geo tracking
# see https://geojson.io/
def prepGeoDemo():
    import json

    if DEVICE_NAME not in ('device-a', 'device-b'): 
        filename = './geoPath-device-a.json'
    else:
        filename = f'./geoPath-{DEVICE_NAME}.json'
        
    with open(filename, 'r') as file:
        geoFC = json.load(file)
        
    geoPath = geoFC['features'][0]['geometry']['coordinates']
    return geoPath

async def main():
    """Publishes sample data every second"""
    pos = 0
    geoPath = prepGeoDemo()
    while True:
        randomTemp = random.randint(20, 30)
        randomHumi = random.randint(40, 80)
        data = {"tsp": datetime.now().astimezone().isoformat(), "temperature": randomTemp, "humidity": randomHumi, "lon": 8.714759789104392, "lat": 50.11225759535884}
        # publish an event (if connection is not established the publish is skipped)
        await ironflock.publish_to_table("sensordata", data)
        print(f'Published Data: {data}')
        await asyncio.sleep(1)
        
        geo = {"tsp": datetime.now().astimezone().isoformat(), "lon": geoPath[pos][0], "lat": geoPath[pos][1]}
        pos = (pos+1) % len(geoPath)
        await ironflock.publish_to_table("geodata", geo)
        print(f'Published Geo: {geo}')
        await asyncio.sleep(1)

# create a reswarm instance, which auto connects to your WAMP message router in the IronFlock Platform for publishing data
ironflock = IronFlock(mainFunc=main)
ironflock.run()
