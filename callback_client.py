from fastapi import FastAPI
from reasoner_pydantic import Query, Response
import socket
import requests
import asyncio

APP = FastAPI(title="CallbackClient")
queue = asyncio.Queue()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@APP.post("/callback")
async def trapi_operation(response: Response) -> int:
    print('it called back')
    await queue.put(response)
    print('it is in the queue')
    return 200

@APP.post("/query", response_model=Response)
async def postit(query:Query, host_url) -> Response:
    aquery = f'{host_url}/asyncquery'
    queryd = query.dict()
    print("Calling")
    print(get_ip())
    queryd['callback'] = f'http://{get_ip()}:8080/callback'
    resp = requests.post(aquery,json=queryd)
    print(resp.status_code)
    if resp.status_code != 200:
        print(resp.json())
        return "Error",resp.status_code
    response = await queue.get()
    print('got it out of the queue')
    #print(response)
    return response