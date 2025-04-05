# ---------------- wl_kernel.py ----------------
from collections import Counter

def weisfeiler_lehman_kernel(G1, G2, h=3):
    for G in [G1, G2]:
        for node in G.nodes():
            G.nodes[node]['wl_label'] = G.nodes[node].get('type', 'unknown')

    def histogram(G):
        return Counter([G.nodes[n]['wl_label'] for n in G.nodes])

    G1_hist, G2_hist = [histogram(G1)], [histogram(G2)]

    for _ in range(h):
        def relabel(G):
            new_labels = {}
            for n in G.nodes():
                curr = G.nodes[n]['wl_label']
                neighbors = [f"{G.nodes[nb]['wl_label']}_{G.edges[n, nb].get('type', 'default')}" for nb in G.neighbors(n)]
                neighbors.sort()
                new_labels[n] = f"{curr}|{'-'.join(neighbors) if neighbors else 'LEAF'}"
            for n, lbl in new_labels.items():
                G.nodes[n]['wl_label'] = lbl

        relabel(G1)
        relabel(G2)
        G1_hist.append(histogram(G1))
        G2_hist.append(histogram(G2))

    weights = [0.8**i for i in range(h+1)]
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]

    similarity = 0.0
    for i in range(h+1):
        h1, h2 = G1_hist[i], G2_hist[i]
        all_labels = set(h1) | set(h2)
        intersect = sum(min(h1.get(l, 0), h2.get(l, 0)) for l in all_labels)
        union = sum(max(h1.get(l, 0), h2.get(l, 0)) for l in all_labels)
        similarity += weights[i] * (intersect / union if union > 0 else 0)

    return similarity

