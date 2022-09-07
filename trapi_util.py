import networkx as nx
import matplotlib.pyplot as plt

def get_node_label(node_id, node):
# creates a node label. Every node level is prefixed with the node id used in 
# the query graph. If there is one or more ids listed, then the label suffix is 
# a comma-delimited list of ids. Otherwise, the label suffix is a 
# comma-delimited list of categories.
  if "ids" in node:
    return node_id + "\n" + ','.join(node["ids"])
  return node_id + "\n" + ','.join(node["categories"])

def display_query(trapi_json, fig_dim):
# create a simple graphical depiction of a TRAPI query 
  query_graph = trapi_json["message"]["query_graph"]
  node_labels = dict([(node_id, get_node_label(node_id, node)) for node_id, node in query_graph["nodes"].items()])
  
  edges = [[node_labels.get(edge["subject"]), node_labels.get(edge["object"])] for edge_id, edge in query_graph["edges"].items()]
  edge_labels = dict([[(node_labels.get(edge["subject"]), node_labels.get(edge["object"])), ',\n'.join(edge["predicates"])] for edge_id, edge in query_graph["edges"].items()])
  
  print(edges)
  print(edge_labels)
  G = nx.DiGraph()
  G.add_edges_from(edges)
  
  plt.figure(figsize=(fig_dim, fig_dim))
  pos = nx.spring_layout(G)
  nx.draw(G, with_labels=True, node_color='pink', node_size = 5000, 
          width=2, alpha=0.9, arrows=True, arrowsize=20, edge_cmap=plt.cm.Blues, pos = pos)
  nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
  plt.axis('off')
  plt.show()

def get_kg_edge_source_provenance(knowledge_graph):
    # returns the original knowlege sources for the edges in the input KG. Each 
    # original knowledge source is mapped to counts of aggregator knowledge sources 
    # that provided the data in a nested dictionary structure.
    edges = [v for k,v in knowledge_graph["edges"].items()]
    attribute_lists = [e["attributes"] for e in edges]

    # populate the sources dictionary with key = original source and value = a set 
    # containing aggregator sources that are associated with the original source
    sources = {}
    for alist in attribute_lists:
        aggregators = list()
        for a in alist:
            if (a["attribute_type_id"] == "biolink:original_knowledge_source"):
                original_source= a["value"]
                # print(original_source)
            if (a["attribute_type_id"] == "biolink:aggregator_knowledge_source"):
                v = a["value"]
                # some values for the aggregator knowledge source are strings, and 
                # some are lists so we handle both -- what is the TRAPI spec?
                # The list values are ['infores:biothings-explorer']
                if type(v) == list:
                    [aggregators.append(s) for s in v]
                    # print(v)
                else: 
                    aggregators.append(v)
        aggregators.sort()
        aggregator_source = '|'.join(aggregators)
        if original_source in sources:
            innerdict = sources[original_source]
            if aggregator_source in innerdict:
                innerdict[aggregator_source] += 1
            else: 
                innerdict[aggregator_source] = 1
        else:
            innerdict = {}
            innerdict[aggregator_source] = 1
            sources[original_source] = innerdict
    return sources

def get_original_source_edges(knowledge_graph, original_source_infores):
# simple function that returns True if the specified edge has the specified 
# original_knowledge_source

  def has_original_source(kedge):
  # helper function to identify edges that are specific to the specified
  # original source
    has_aggregator_source = False
    has_orig_source_cohd = False
    for attribute in kedge["attributes"]:
      if attribute["attribute_type_id"] == "biolink:original_knowledge_source" and attribute["attribute_source"] == original_source_infores: 
        has_orig_source_cohd = True
      if attribute["attribute_type_id"] == "biolink:aggregator_knowledge_source": 
        has_aggregator_source = True
    return has_orig_source_cohd and not has_aggregator_source

  original_source_edges = [(k,v) for k,v in knowledge_graph["edges"].items() if has_original_source(v)]
  return original_source_edges