import plotly.graph_objects as go
import networkx as nx
import numpy as np
from sklearn.cluster import SpectralClustering
import plotly.express as px
import json
panel_color = '#161a28'
def get_graph(nodes, A, n_query=0):
    customdata = [json.dumps(node) for node in nodes]
    if n_query >1:
        clustering = SpectralClustering(n_components = min(n_query,8), affinity='precomputed')
        clustering.fit(A)
    G = nx.Graph()
    A = np.array(A)
    A[A<0.08] = 0
    for idx, node in enumerate(nodes):
        G.add_node(idx, **{'title': node['title']})

    edge_widths = []
    for n1,_ in enumerate(nodes[:len(A)]):
        for n2,_ in enumerate(nodes[:]):
            if n1 == n2: continue
            j = n2
            if A[n1, j] > 0:
                G.add_edges_from([(n1,j,{'weight': A[n1,j]})])
    pos = nx.spring_layout(G,k=1.5/np.sqrt(len(nodes)))
    edge_x = []
    edge_y = []
    for edge in G.edges():
        edge_widths.append(G[edge[0]][edge[1]]['weight'])
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    # bm_trace = go.Scatter(
    #     x=node_x[:n_query], y=node_y[:n_query],
    #     mode='text')

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        customdata= customdata,
        marker=dict(
            showscale=False,
            # colorscale options
            #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='rainbow',
            # color_discrete_sequence=px.colors.qualitative.G10,
            # color=[],
            size=20,
            line_width=3,
            line_color='white'))
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append('# of connections: '+str(len(adjacencies[1])))

    if n_query > 1:
        node_trace.marker.color = [px.colors.qualitative.Vivid[c] for c in clustering.labels_]
    else:
        node_trace.marker.color = ['indianred'] + ['lightgrey' for n in nodes[1:]]
    node_trace.marker.line.width = [3]*n_query + [0.1]*(len(nodes)-n_query)
    node_trace.text = [node['title'] for node in nodes]
    edge_trace.line.width = 2
    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0,l=0,r=0,t=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)),
                )
    fig.update_layout(plot_bgcolor=panel_color)
    # fig.update_layout(clickmode='event+select')
    fig.update_layout(clickmode='event')
    return fig, node_trace.marker.color
