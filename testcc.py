import pytest
from fastapi.testclient import TestClient
from callback_client import APP

client = TestClient(APP)

def test_client():
    q={
    "message": {
        "query_graph": {
            "edges": {
                "e01": {
                    "object": "n0",
                    "subject": "n1",
                    "predicates": [
                        "biolink:entity_negatively_regulates_entity"
                    ]
                }
            },
            "nodes": {
                "n0": {
                    "ids": [
                        "NCBIGene:23221"
                    ],
                    "categories": [
                        "biolink:Gene"
                    ]
                },
                "n1": {
                    "categories": [
                        "biolink:Gene"
                    ]
                }
            }
        }
    }
    }
    client.post('/query',params={'host_url':'http://0.0.0.0:4868'},json=q)