from er_graph import NodeType, EdgeType, Graph, Edge, Node, Key
import numpy as np
import random

def init_workload_distribution_parameters(graph, names, N_total, s=1.15, tau=300, seed=7, min_each=0):
    """
    names: ordered by desired popularity rank (rank 1 is largest).
    s: Zipf tail (bigger -> heavier head). tau: Dirichlet strength (bigger -> less noise).
    min_each: floor per subtype.
    """
    rng = np.random.default_rng(seed)
    k = len(names)
    ranks = np.arange(1, k+1)
    base = 1.0 / (ranks ** s)          # Zipf shares
    base /= base.sum()
    w = rng.dirichlet(tau * base)       # noisy shares around Zipf
    counts = rng.multinomial(N_total - min_each * k, w) + min_each
    counts_list = counts.tolist()

    return dict(zip(names, counts))

#iterate the inheritance hierarchies from leaf level to top - make distributions zip-f across siblings in each layer
def iterate_inheritance_hierarchy_helper(graph, node, level_number=1):
    if all(len(child.children) == 0 for child in node.children):
        subtypes = [child.unique_name for child in node.children]
        rng = random.Random(42)
        rng.shuffle(subtypes)
        dict_counts = init_workload_distribution_parameters(subtypes, 100000*(2**level_number), s=1.2, tau=400, min_each=1000)
        for key in dict_counts:
            entity_node = graph.get_node_by_name(key)
            assert entity_node.unique_name == key
            node.relation_size = dict_counts[key]
            node.parent_entity.relation_size += node.relation_size

    if len(node.children) > 0:
            for child in node.children:
                if len(child.children) > 0:
                    iterate_inheritance_hierarchy_helper(child)

def iterate_inheritance_hierarchy(graph):
    for node in graph.nodes:
        if len(node.children) > 0:
            iterate_inheritance_hierarchy(node)