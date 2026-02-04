import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received data keys: {list(data.keys())}")
                if 'logs' in data:
                    print(f"Logs count: {len(data['logs'])}")
                if 'metric' in data:
                    print(f"Metric: {data['metric'].get('rpsActual')}")
                break # Just receive one message
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
