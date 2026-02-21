from graph import graph
from langgraph.visualization import to_mermaid

mermaid_code=to_mermaid(graph)
print(mermaid_code)