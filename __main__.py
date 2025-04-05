
from parser_utils import parse_c_code
from pdg_generator import PDGGenerator
from wl_kernel import weisfeiler_lehman_kernel
from visualizer import visualize_pdg

with open("test_codes/code1.c") as f:
    code1 = f.read()
with open("test_codes/code2.c") as f:
    code2 = f.read()

ast1 = parse_c_code(code1)
ast2 = parse_c_code(code2)

gen = PDGGenerator()
pdg1 = gen.generate(ast1)

gen2 = PDGGenerator()
pdg2 = gen2.generate(ast2)

plt1 = visualize_pdg(pdg1, "PDG - Code 1")
plt1.savefig("pdg1.png")
plt1.close()

plt2 = visualize_pdg(pdg2, "PDG - Code 2")
plt2.savefig("pdg2.png")
plt2.close()

sim = weisfeiler_lehman_kernel(pdg1, pdg2, h=3)
print(f"WL Kernel Similarity: {sim:.4f}")
