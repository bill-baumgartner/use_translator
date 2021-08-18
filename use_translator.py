import json
import requests
from collections import defaultdict
import pandas as pd
import copy
from datetime import datetime as dt

#https://pypi.org/project/gamma-viewer/
from gamma_viewer import GammaViewer
from IPython.display import display

#ARS functions
def submit_to_ars(m,ars_url='https://ars.ci.transltr.io/ars/api',arax_url='https://arax.ncats.io'):
    submit_url=f'{ars_url}/submit'
    response = requests.post(submit_url,json=m)
    try:
        message_id = response.json()['pk']
    except:
        print('fail')
        message_id = None
    print(f'{arax_url}/?source=ARS&id={message_id}')
    return message_id

def retrieve_ars_results(mid,ars_url='https://ars.ci.transltr.io/ars/api'):
    message_url = f'{ars_url}/messages/{mid}?trace=y'
    response = requests.get(message_url)
    j = response.json()
    print( j['status'] )
    results = {}
    for child in j['children']:
        print(child['status'])
        if child['status']  == 'Done':
            childmessage_id = child['message']
            child_url = f'{ars_url}/messages/{childmessage_id}'
            try:
                child_response = requests.get(child_url).json()
                nresults = len(child_response['fields']['data']['message']['results'])
                if nresults > 0:
                    results[child['actor']['agent']] = {'message':child_response['fields']['data']['message']}
            except Exception as e:
                nresults=0
                child['status'] = 'ARS Error'
        elif child['status'] == 'Error':
            nresults=0
            childmessage_id = child['message']
            child_url = f'{ars_url}/messages/{childmessage_id}'
            try:
                child_response = requests.get(child_url).json()
                results[child['actor']['agent']] = {'message':child_response['fields']['data']['message']}
            except Exception as e:
                print(e)
                child['status'] = 'ARS Error'
        else:
            nresults = 0
        print( child['status'], child['actor']['agent'],nresults )
    return results

#utils
def printjson(j):
    print(json.dumps(j,indent=4))
def print_json(j):
    printjson(j)

def name_lookup(text):
    url= f'https://name-resolution-sri.renci.org/lookup?string={text}&offset=0&limit=10'
    response = requests.post(url)
    printjson(response.json())

def print_errors(strider_result):
    errorcounts = defaultdict(int)
    if 'logs' not in strider_result:
        return
    for logmessage in strider_result['logs']:
        if logmessage['level'] in('ERROR','WARNING'):
            try:
                e = logmessage['error']
                if e == '':
                    e = logmessage['message']
            except KeyError:
                e = 'Missing error message'
                e = logmessage['message']
            errorcounts[e] += 1
    for error, count in errorcounts.items():
        print(f'{error} ({count} times)')

def post(name,url,message,params=None):
    """Wrap a post in some basic error reporting"""
    start = dt.now()
    if params is None:
        response = requests.post(url,json=message)
    else:
        response = requests.post(url,json=message,params=params)
    end = dt.now()
    if not response.status_code == 200:
        print(name, 'error:',response.status_code)
        print(response.json())
        return response.json()
    print(f'{name} returned in {end-start}s')
    m = response.json()
    if 'message' in m:
        if 'results' in m['message']:
            print(f'Num Results: {len(m["message"]["results"])}')
    print_errors(m)
    return m

### Log parsing


def print_queried_sources(strider_result):
    querycounts = defaultdict(int)
    for logmessage in strider_result['logs']:
        if 'step' in logmessage and isinstance(logmessage['step'], list):
            for s in logmessage['step']:
                querycounts[s['url']] += 1
    for url, count in querycounts.items():
        print(f'{url} ({count} times)')

def print_query_for_source(strider_result, url):
    for logmessage in strider_result['logs']:
        if 'step' in logmessage and isinstance(logmessage['step'], list):
            for s in logmessage['step']:
                if s['url'] == url:
                    print(s)

def get_provenance(message):
    """Given a message with results, find the source of the edges"""
    prov = defaultdict(lambda: defaultdict(int)) # {qedge->{source->count}}
    results = message['message']['results']
    kg = message['message']['knowledge_graph']['edges']
    edge_bindings = [ r['edge_bindings'] for r in results ]
    for bindings in edge_bindings:
        for qg_e, kg_l in bindings.items():
            for kg_e in kg_l:
                for att in kg[kg_e['id']]['attributes']:
                    if att['attribute_type_id'] in ( "biolink:original_knowledge_source", 'biolink:primary_knowledge_source', 'biolink:aggregator_knowledge_source'):
                        source = att['value']
                        if isinstance(source,list):
                            source = source[0]
                        prov[qg_e][source]+=1
    qg_edges = []
    sources = []
    counts = []
    for qg_e in prov:
        for source in prov[qg_e]:
            qg_edges.append(qg_e)
            sources.append(source)
            counts.append(prov[qg_e][source])
    prov_table =pd.DataFrame({"QG Edge":qg_edges, "Source":sources, "Count":counts})
    return prov_table

#####
#
# Stuff from here down is mostly ranking-agent specific (though it would be easy to expand)
#
###

#Call particular endpoints

def automat(db,message):
    """Call a particular automat"""
    automat_url = f'https://automat.renci.org/{db}/1.1/query'
    response = post(f'automat/{db}',automat_url,message)
    return response

def strider(message):
    url = 'https://strider.renci.org/1.1/query'
    strider_answer = post('strider',url,message)
    return strider_answer

def aragorn(message,coalesce_type='xnone'):
    if coalesce_type == 'xnone':
        answer = post('aragorn','https://aragorn.renci.org/1.1/query',message)
    else:
        answer = post('aragorn','https://aragorn.renci.org/1.1/query',message, params={'answer_coalesce_type':coalesce_type})
    return answer

def local_aragorn(message):
    answer = post('aragorn','http://0.0.0.0:4868/query',message)
    return answer

def local_strider(message):
    answer = post('aragorn','http://0.0.0.0:5781/query',message)
    return answer

def rtx(message):
    url = 'https://arax.ncats.io/api/rtxkg2/v1.1/query'
    return post('rtx',url,message)

def bte(message):
    url = 'https://api.bte.ncats.io/v1/query'
    return post('bte',url,message)

def cam(message):
    url = 'https://cam-kp-api.renci.org/query'
    return post('cam',url,message)

###
#
# Functions for handling AC results

def ac_to_table(aragorn_result, mnode):
    # scores = []
    answer_node_count = []
    merged_count = []
    method = []
    extra = []
    for res_i, result in enumerate(aragorn_result['message']['results']):
        # scores.append(result['score'])
        answer_node_count.append(len(result['node_bindings']))
        merged_count.append(len(result['node_bindings'][mnode]))
        try:
            method.append(result['node_bindings'][mnode][0]['coalescence_method'])
        except:
            method.append('Original')
    df = pd.DataFrame({'N_Answer_Nodes': answer_node_count, 'N_Merged_Nodes': merged_count, 'Method': method})
    return df


def filter_to_simple(aragorn_result, mnode):
    simple_result = copy.deepcopy(aragorn_result)
    simple_result['message']['results'] = list(
        filter(lambda x: 'coalescence_method' not in x['node_bindings'][mnode][0],
               aragorn_result['message']['results'])
    )
    print(len(simple_result['message']['results']))
    return simple_result


def print_nodenames(simple_result, qnode):
    # Print the names of the answers
    for result in simple_result['message']['results']:
        # Each answer has an identifier:
        n1_id = result['node_bindings'][qnode][0]['id']
        # The information for that identifier is in the KG:
        node = simple_result['message']['knowledge_graph']['nodes'][n1_id]
        # Each node has a name
        print(node['name'])


def filter_to_coal(aragorn_result, mnode, method):
    # The results that have been coalesced:
    coalesced_results = list(
        filter(lambda x: 'coalescence_method' in x['node_bindings'][mnode][0],
               aragorn_result['message']['results'])
    )
    # Those that have been coalesced via a new node (graph coalescence)
    graph_coalesced_results = list(
        filter(lambda x: x['node_bindings'][mnode][0]['coalescence_method'] == method, coalesced_results)
    )
    print(len(graph_coalesced_results))
    simple_result = copy.deepcopy(aragorn_result)
    simple_result['message']['results'] = graph_coalesced_results
    return simple_result


def filter_to_gc(aragorn_result, mnode):
    return filter_to_coal(aragorn_result, mnode, 'graph_enrichment')


def filter_to_pc(aragorn_result, mnode):
    return filter_to_coal(aragorn_result, mnode, 'property_enrichment')


def print_gc_result(graph, gc_result, node):
    print('p_value:', gc_result['node_bindings'][node][0]['p_value'])
    maxprint = 5
    for extra_edge in gc_result['edge_bindings']:
        if not extra_edge.startswith('extra_'):
            continue
        numnodes = len(gc_result['edge_bindings'][extra_edge])
        if numnodes == 0:
            printjson(gc_result)
            return
        print('Merged', numnodes)
        nprint = min([numnodes, maxprint])
        for eb in gc_result['edge_bindings'][extra_edge][:maxprint]:
            kge = graph['edges'][eb['id']]
            subject_node = kge['subject']
            object_node = kge['object']
            pred = kge['predicate']
            print(f"  {graph['nodes'][subject_node]['name']} -[{pred}]-> {graph['nodes'][object_node]['name']}")
    print('----')


def print_pc_result(knowledge_graph, pc_result, node):
    print('p_value:', pc_result['node_bindings'][node][0]['p_values'])
    print('properties:', pc_result['node_bindings'][node][0]['properties'])
    numnodes = len(pc_result['node_bindings'][node])
    print('node count', numnodes)
    maxprint = 5
    nprint = min([numnodes, maxprint])
    for node in pc_result['node_bindings'][node][:nprint]:
        kgn = knowledge_graph['nodes'][node['id']]
        print(f"  {kgn['name']}")
    if numnodes > maxprint:
        print('  ...')
    print('----')
