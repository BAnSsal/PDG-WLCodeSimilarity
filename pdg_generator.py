# ---------------- pdg_generator.py ----------------
import networkx as nx
from pycparser import c_ast

class PDGGenerator:
    def __init__(self):
        self.pdg = nx.DiGraph()
        self.node_id = 0
        self.last_assignment = {}

    def generate(self, ast):
        class Visitor(c_ast.NodeVisitor):
            def __init__(self, outer):
                self.outer = outer
                self.current_node = None

            def add_node(self, label, node_type):
                nid = f"n{self.outer.node_id}"
                self.outer.pdg.add_node(nid, label=label, type=node_type)
                if self.current_node is not None:
                    self.outer.pdg.add_edge(self.current_node, nid, type="control")
                self.current_node = nid
                self.outer.node_id += 1
                return nid

            def visit_Decl(self, node):
                decl_id = self.add_node(f"Decl {node.name}", "decl")
                if node.init:
                    if isinstance(node.init, c_ast.FuncCall):
                        call_id = self.visit_FuncCall(node.init)
                        assign_id = self.add_node(f"{node.name} = [call]", "assign")
                        self.outer.pdg.add_edge(assign_id, call_id, type="data")
                    else:
                        init_str = self.get_text(node.init)
                        assign_id = self.add_node(f"{node.name} = {init_str}", "assign")

            def visit_Assignment(self, node):
                lval = self.get_text(node.lvalue)
                if isinstance(node.rvalue, c_ast.FuncCall):
                    call_id = self.visit_FuncCall(node.rvalue)
                    nid = self.add_node(f"{lval} {node.op} [call]", "assign")
                    self.outer.pdg.add_edge(nid, call_id, type="data")
                else:
                    rval = self.get_text(node.rvalue)
                    nid = self.add_node(f"{lval} {node.op} {rval}", "assign")
                self.outer.last_assignment[lval] = nid
                self.generic_visit(node.rvalue)

            def visit_FuncCall(self, node):
                func_name = self.get_text(node.name)
                args = []
                if node.args and hasattr(node.args, 'exprs'):
                    args = [self.get_text(arg) for arg in node.args.exprs]
                return self.add_node(f"Call {func_name}({', '.join(args)})", "func_call")

            def visit_If(self, node):
                cond = self.get_text(node.cond)
                cond_nid = self.add_node(f"If {cond}?", "if")
                if node.iftrue:
                    old = self.current_node
                    self.current_node = cond_nid
                    self.visit(node.iftrue)
                    self.outer.pdg.add_edge(cond_nid, self.current_node, type="control")
                    self.current_node = old
                if node.iffalse:
                    old = self.current_node
                    self.current_node = cond_nid
                    self.visit(node.iffalse)
                    self.outer.pdg.add_edge(cond_nid, self.current_node, type="control")
                    self.current_node = old

            def visit_Return(self, node):
                label = f"Return {self.get_text(node.expr)}" if node.expr else "Return"
                self.add_node(label, "return")
                if node.expr:
                    self.generic_visit(node.expr)

            def visit_Compound(self, node):
                for stmt in (node.block_items or []):
                    self.visit(stmt)

            def visit_ID(self, node):
                name = node.name
                if name in self.outer.last_assignment:
                    use_nid = self.add_node(f"Use {name}", "use")
                    self.outer.pdg.add_edge(self.outer.last_assignment[name], use_nid, type="data")

            def get_text(self, node):
                if isinstance(node, c_ast.Constant): return node.value
                elif isinstance(node, c_ast.ID): return node.name
                elif isinstance(node, c_ast.BinaryOp): return f"({self.get_text(node.left)} {node.op} {self.get_text(node.right)})"
                elif isinstance(node, c_ast.Assignment): return f"{self.get_text(node.lvalue)} {node.op} {self.get_text(node.rvalue)}"
                elif isinstance(node, c_ast.UnaryOp): return f"{node.op}{self.get_text(node.expr)}"
                elif isinstance(node, c_ast.FuncCall):
                    args = [self.get_text(arg) for arg in node.args.exprs] if node.args and hasattr(node.args, 'exprs') else []
                    return f"Call {self.get_text(node.name)}({', '.join(args)})"
                return "?"

        visitor = Visitor(self)
        visitor.visit(ast)
        return self.pdg