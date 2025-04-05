from pycparser import c_parser, c_ast
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter

def parse_c_code(c_code):
    """Parse C code and return the AST"""
    parser = c_parser.CParser()
    return parser.parse(c_code)
def generate_pdg(ast):
    """
    Generate a simplified Program Dependence Graph (PDG) from an AST.
    Nodes represent statements with a 'label' and 'type'.
    Edges include:
      - Control dependency edges (type "control")
      - Data dependency edges (type "data")
    """
    pdg = nx.DiGraph()
    node_id = 0
    # For a very simple data dependency, track last assignment for variables.
    last_assignment = {}

    class PDGVisitor(c_ast.NodeVisitor):
        def __init__(self):
            self.current_node = None

        def add_node(self, label, node_type):
            nonlocal node_id 
            nid = f"n{node_id}"
            pdg.add_node(nid, label=label, type=node_type)
            if self.current_node is not None:
                # Connect sequentially executed nodes (control dependency)
                pdg.add_edge(self.current_node, nid, type="control")
            self.current_node = nid
            node_id += 1
            return nid

        def visit_Decl(self, node):
            # Always create a declaration node.
            decl_label = f"Decl {node.name}"
            decl_id = self.add_node(decl_label, "decl")
            
            # If an initializer exists, create a separate assignment node.
            if node.init:
                if isinstance(node.init, c_ast.FuncCall):
                    # Create a node for the function call first.
                    call_id = self.visit_FuncCall(node.init)
                    # Then create an assignment node that points to the call.
                    assign_label = f"{node.name} = [call]"
                    assign_id = self.add_node(assign_label, "assign")
                    pdg.add_edge(assign_id, call_id, type="data")
                else:
                    init_str = self.get_text(node.init)
                    assign_label = f"{node.name} = {init_str}"
                    assign_id = self.add_node(assign_label, "assign")
                    
        def visit_Assignment(self, node):
            lval = self.get_text(node.lvalue)
            # If the right-hand side is a function call, handle it separately.
            if isinstance(node.rvalue, c_ast.FuncCall):
                call_id = self.visit_FuncCall(node.rvalue)
                label = f"{lval} {node.op} [call]"
                nid = self.add_node(label, "assign")
                pdg.add_edge(nid, call_id, type="data")
            else:
                rval = self.get_text(node.rvalue)
                label = f"{lval} {node.op} {rval}"
                nid = self.add_node(label, "assign")
            last_assignment[lval] = nid  # record assignment for data dependency
            self.generic_visit(node.rvalue)

        def visit_FuncCall(self, node):
            """
            Process a function call by creating its own node.
            """
            func_name = self.get_text(node.name)
            args_list = []
            if node.args and hasattr(node.args, 'exprs'):
                for arg in node.args.exprs:
                    args_list.append(self.get_text(arg))
            label = f"Call {func_name}({', '.join(args_list)})"
            call_node = self.add_node(label, "func_call")
            # Optionally, visit children if needed:
            # self.generic_visit(node)
            return call_node

        def visit_If(self, node):
            cond = self.get_text(node.cond)
            cond_nid = self.add_node(f"If {cond}?", "if")
            # Process true branch
            if node.iftrue:
                old_current = self.current_node
                self.current_node = cond_nid
                self.visit(node.iftrue)
                true_end = self.current_node
                pdg.add_edge(cond_nid, true_end, type="control")
                self.current_node = old_current
            # Process false branch, if exists
            if node.iffalse:
                old_current = self.current_node
                self.current_node = cond_nid
                self.visit(node.iffalse)
                false_end = self.current_node
                pdg.add_edge(cond_nid, false_end, type="control")
                self.current_node = old_current

        def visit_Return(self, node):
            if node.expr:
                ret_val = self.get_text(node.expr)
                label = f"Return {ret_val}"
            else:
                label = "Return"
            self.add_node(label, "return")
            if node.expr:
                self.generic_visit(node.expr)

        def visit_Compound(self, node):
            if node.block_items:
                for stmt in node.block_items:
                    self.visit(stmt)

        def visit_ID(self, node):
            var_name = node.name
            if var_name in last_assignment:
                # Create a dummy node for this use
                use_nid = self.add_node(f"Use {var_name}", "use")
                pdg.add_edge(last_assignment[var_name], use_nid, type="data")
            return

        def get_text(self, node):
            if isinstance(node, c_ast.Constant):
                return node.value
            elif isinstance(node, c_ast.ID):
                return node.name
            elif isinstance(node, c_ast.BinaryOp):
                left = self.get_text(node.left)
                right = self.get_text(node.right)
                return f"({left} {node.op} {right})"
            elif isinstance(node, c_ast.Assignment):
                return f"{self.get_text(node.lvalue)} {node.op} {self.get_text(node.rvalue)}"
            elif isinstance(node, c_ast.UnaryOp):
                return f"{node.op}{self.get_text(node.expr)}"
            elif isinstance(node, c_ast.FuncCall):
                # Return a string representation without creating a new node.
                func_name = self.get_text(node.name)
                args_list = []
                if node.args and hasattr(node.args, 'exprs'):
                    for arg in node.args.exprs:
                        args_list.append(self.get_text(arg))
                return f"Call {func_name}({', '.join(args_list)})"
            return "?"
        
    visitor = PDGVisitor()
    visitor.visit(ast)
    return pdg
def weisfeiler_lehman_kernel(G1, G2, h=3):
    """
    Compute similarity between two graphs G1 and G2 using the
    Weisfeiler-Lehman kernel. Nodes are assumed to have an initial label
    in attribute 'type' (or 'label' if preferred). We perform h iterations
    of relabeling and then compare label histograms using weighted Jaccard similarity.
    """
    # Initialize each node's WL label based on its type.
    for G in [G1, G2]:
        for node in G.nodes():
            # Use the node's type as the initial WL label
            G.nodes[node]['wl_label'] = G.nodes[node].get('type', 'unknown')
    
    # Store label histograms for each iteration
    G1_label_histograms = []
    G2_label_histograms = []
    
    def get_histogram(G):
        return Counter([G.nodes[node]['wl_label'] for node in G.nodes()])
    
    G1_label_histograms.append(get_histogram(G1))
    G2_label_histograms.append(get_histogram(G2))
    
    # Perform h iterations of WL relabeling
    for i in range(h):
        # New labels for each graph
        new_labels_G1 = {}
        new_labels_G2 = {}
        
        # Update labels for G1
        for node in G1.nodes():
            current_label = G1.nodes[node]['wl_label']
            neighbor_labels = []
            # Include labels from neighbors along with edge type information
            for nbr in G1.neighbors(node):
                nbr_label = G1.nodes[nbr]['wl_label']
                edge_type = G1.edges[node, nbr].get('type', 'default')
                neighbor_labels.append(f"{nbr_label}_{edge_type}")
            neighbor_labels.sort()
            new_label = f"{current_label}|{'-'.join(neighbor_labels) if neighbor_labels else 'LEAF'}"
            new_labels_G1[node] = new_label
        
        # Update labels for G2
        for node in G2.nodes():
            current_label = G2.nodes[node]['wl_label']
            neighbor_labels = []
            for nbr in G2.neighbors(node):
                nbr_label = G2.nodes[nbr]['wl_label']
                edge_type = G2.edges[node, nbr].get('type', 'default')
                neighbor_labels.append(f"{nbr_label}_{edge_type}")
            neighbor_labels.sort()
            new_label = f"{current_label}|{'-'.join(neighbor_labels) if neighbor_labels else 'LEAF'}"
            new_labels_G2[node] = new_label
        
        # Apply the new labels and update histograms
        for node, label in new_labels_G1.items():
            G1.nodes[node]['wl_label'] = label
        for node, label in new_labels_G2.items():
            G2.nodes[node]['wl_label'] = label
        
        G1_label_histograms.append(get_histogram(G1))
        G2_label_histograms.append(get_histogram(G2))
    
    # Now compute the weighted Jaccard similarity over all iterations
    kernel_value = 0.0
    weights = [1.0]
    for i in range(h):
        weights.append(weights[-1] * 0.8)  # Decaying weight
    
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]
    
    for i in range(h+1):
        hist1 = G1_label_histograms[i]
        hist2 = G2_label_histograms[i]
        # All labels appearing in either histogram
        all_labels = set(hist1.keys()) | set(hist2.keys())
        # Intersection and union counts (using minimum and maximum counts)
        intersection = sum(min(hist1.get(l, 0), hist2.get(l, 0)) for l in all_labels)
        union = sum(max(hist1.get(l, 0), hist2.get(l, 0)) for l in all_labels)
        if union > 0:
            kernel_value += weights[i] * (intersection / union)
    
    return kernel_value
def visualize_pdg(pdg, title="Program Dependence Graph"):
    """Visualize a PDG using matplotlib and networkx"""
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(pdg, seed=42)
    node_labels = nx.get_node_attributes(pdg, 'label')
    edge_labels = nx.get_edge_attributes(pdg, 'type')
    nx.draw(pdg, pos, with_labels=True, labels=node_labels, node_color='lightblue', node_size=2500, arrows=True)
    nx.draw_networkx_edge_labels(pdg, pos, edge_labels=edge_labels)
    plt.title(title)
    plt.axis('off')
    return plt
# Sample C code for testing (factorial function)

code1 = """
int factorial(int n) {
    if (n <= 1) {
        return 1;
    } else {
    int i=0;
    while(i<5){
    num++;
    i++;}
        int temp = n - 1;
        int rec = factorial(temp);
        return n * rec;
    }
}
"""
# A slightly modified version of factorial (renamed variables, same logic)
code2 = """
int compute_factori(int num) {
    if (num <= 1) {
        return 1;
    } else {
    for( int i=0 ; i<5;i++){
    num++;}
        int l = compute_factori(num-1);
        return num * l;
    }
}
"""

if __name__ == "__main__":
    print("Parsing and generating PDGs...")
    ast1 = parse_c_code(code1)
    ast2 = parse_c_code(code2)
    
    pdg1 = generate_pdg(ast1)
    pdg2 = generate_pdg(ast2)
    
    # Visualize PDGs (optional)
    plt1 = visualize_pdg(pdg1, "PDG - Code Sample 1")
    plt1.savefig("pdg1.png")
    plt1.close()
    
    plt2 = visualize_pdg(pdg2, "PDG - Code Sample 2")
    plt2.savefig("pdg2.png")
    plt2.close()
    
    # Compute WL kernel similarity between the two PDGs
    similarity = weisfeiler_lehman_kernel(pdg1, pdg2, h=3)
    print(f"WL Kernel Similarity: {similarity:.4f}")
