# ---------------- visualizer.py ----------------
import matplotlib.pyplot as plt
import networkx as nx

def visualize_pdg(pdg, title="PDG"):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(pdg, seed=42)
    node_labels = nx.get_node_attributes(pdg, 'label')
    edge_labels = nx.get_edge_attributes(pdg, 'type')
    nx.draw(pdg, pos, with_labels=True, labels=node_labels, node_color='lightblue', node_size=2500, arrows=True)
    nx.draw_networkx_edge_labels(pdg, pos, edge_labels=edge_labels)
    plt.title(title)
    plt.axis('off')
    return plt