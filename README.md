# Program Similarity Using Weisfeiler-Lehman Kernel on PDGs

This project evaluates the similarity between two C programs by analyzing their **Program Dependency Graphs (PDGs)** using the **Weisfeiler-Lehman (WL) kernel** algorithm. It goes beyond superficial syntax comparison and focuses on the underlying semantics of the code.

---

## Features

- Parses and processes C code using `pycparser`.
- Generates Program Dependency Graphs (PDGs) with control and data dependencies.
- Visualizes PDGs using `networkx` and `matplotlib`.
- Applies the Weisfeiler-Lehman kernel to compare structural graph representations.
- Returns a similarity score that reflects how similar two programs are, regardless of variable names or minor structural changes.

---

## How It Works

1. **Parse C Code into AST**  
   The input C code files are parsed using `pycparser`, generating their respective Abstract Syntax Trees (ASTs). The AST captures the structural layout of the code.

2. **Generate Program Dependency Graphs (PDGs)**  
   A custom visitor class traverses each AST to build a PDG:
   - Each node represents a meaningful unit of the code (e.g., assignment, if-statement).
   - Edges capture control flow and data dependencies between the nodes.

3. **Visualize PDGs**  
   PDGs are visualized and saved as `pdg1.png` and `pdg2.png`, offering an intuitive view of the code structure.

4. **Apply Weisfeiler-Lehman Kernel Algorithm**  
   The WL kernel iteratively relabels each graph node based on its neighbors. The updated labels are then used to generate feature vectors for each graph. A similarity score is computed as the dot product of these vectors.

5. **Output Similarity Score**  
   A floating-point value between 0 and 1 is output:
   - 1.0: The graphs (and thus, programs) are structurally very similar.
   - 0.0: The programs have no structural or semantic similarity.

---

## Example

Given two similar C programs that perform the same logic but use different variable names, the system might output:

```
WL Kernel Similarity: 0.83
```

This indicates high semantic similarity.

---

## Requirements

- Python 3.x
- pycparser
- networkx
- matplotlib

Install all dependencies using:

```
pip install -r requirements.txt
```

---

## Files

- `main.py`: Main script that runs the pipeline.
- `pdg_generator.py`: Contains classes and logic to generate PDGs from ASTs.
- `wl_kernel.py`: Implements the Weisfeiler-Lehman kernel similarity algorithm.
- `pdg1.png`, `pdg2.png`: Visual representation of each program's PDG.
- `file1.c`, `file2.c`: Sample input C code files.

---

## Usage

1. Place two C source files as `file1.c` and `file2.c` in the root directory.
2. Run the main script:

```
python __main__.py
```

3. The output will be the similarity score and the generated PDG visualizations.

---

## Applications

- Code plagiarism detection
- Semantic code search
- Similarity analysis for program clustering
- ML-based code recommendation systems

---

## Future Work

- Extend support to handle function calls and library usage.
- Optimize for large-scale programs.
- Add support for other programming languages.

---

Let me know if you'd like a badge/header style or contribution/license section as well!
