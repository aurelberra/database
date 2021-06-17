import codecs 
import networkx as nx 
import sys 
import re 
from lxml import etree as et 

# Transforms a single file (variable: changed_file) from DOT to TEI (without teiHeader) and Graphml
# It is applied automaticly with each push for the files changed
# To perform for all files in bash: 
# for changed_file in $( find . -name '*.gv' ) ; do python ./transform/transformation.py $changed_file ; done
# 

if len(sys.argv) > 1:
    changed_file = str(sys.argv[1])

    with codecs.open(changed_file, 'r', 'utf-8') as dotfile:
        lines = dotfile.readlines()
        nodes = {}
        edges = []
        for line in lines:
            noAttrib = re.sub('\'.+?\'', '', line) 
            noAttrib = re.sub('".+?"', '', line)
            if "->" in noAttrib or "--" in noAttrib:
                origin = re.split('->', noAttrib)[0].strip()
                dest = re.split('->', noAttrib)[1].strip()
                if '[' in dest:
                    dest = re.split('\[', dest)[0].strip()
                if ';' in dest:
                    dest = re.split(';', dest)[0].strip()
                if origin not in nodes:
                    nodes[origin] = {}
                if dest not in nodes:
                    nodes[dest] = {}
                edge_attr = {'type': 'filiation', 'cert': 'unknown'}
                if '[' in noAttrib:
                    attributes = re.findall('(\w+)="(\w*)",?\s?', line)    
                    for attr in attributes:
                        if attr[0] == 'style':
                            if attr[1] == 'dashed':
                                edge_attr['type'] = 'contamination'
                        elif attr[0] == 'color':
                            if attr[1] == 'red':
                                edge_attr['cert'] = 'low'

                edges.append((origin,dest, edge_attr))
                
            elif '[' in noAttrib:
                node = re.split('\[', noAttrib)[0].strip()
                nodes[node] = {}
                attributes = re.findall('(\w+)="(\w*)",?\s?', line)
                for attr in attributes:
                    nodes[node][attr[0]] = attr[1]

    nodes = [ (x,nodes[x]) for x in nodes ]

    G = nx.DiGraph()
    # print(edges)
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    nx.write_graphml(G, changed_file[0:-3] + '.graphml', encoding="utf-8")


    tree = et.parse('./transform/template.tei.xml')
    root = tree.getroot()

    ns = {'tei': 'http://www.tei-c.org/ns/1.0', 'od': 'http://openstemmata.github.io/odd.html' }
    et.register_namespace('tei', 'http://www.tei-c.org/ns/1.0')
    et.register_namespace('od', 'http://openstemmata.github.io/odd.html')

    graph = root.find('.//tei:graph', ns)
    graph.attrib['type'] = 'directed'
    graph.attrib['order'] = str(len(G.nodes))
    graph.attrib['size'] = str(len(G.edges))

    for node in G.nodes(data=True):
        nodeEl = et.SubElement(graph, 'node', attrib={'{http://www.w3.org/XML/1998/namespace}id': "n_" + node[0]})
        labelEl = et.SubElement(nodeEl, 'label')
        if 'label' in node[1]:
            label = node[1]['label']
            if not re.match(r'^\s*$', label):   
                labelEl.text = label   
            else:
                labelEl.text = ''  
        else:
            labelEl.text = node[0]  
        if 'color' in node[1]:
            color = node[1]['color']
            if color == 'grey':
                nodeEl.attrib['type'] = 'hypothetical'
            else:
                nodeEl.attrib['type'] = 'witness'
        else:
            nodeEl.attrib['type'] = 'witness'
        in_degree = G.in_degree(node[0])
        out_degree = G.out_degree(node[0])
        nodeEl.attrib['inDegree'] = str(in_degree)
        nodeEl.attrib['outDegree'] = str(out_degree)
        

                
    for edge in G.edges(data=True):
        edgeEl = et.SubElement(graph, 'arc', attrib= {'from': "#n_" + edge[0], 
            'to': "#n_" + edge[1],})
        
        if 'type' in edge[2]:
            edgeEl.attrib["{http://openstemmata.github.io/odd.html}type"] = edge[2]['type']
        else:
            edgeEl.attrib['{http://openstemmata.github.io/odd.html}type'] = 'filiation'
        
        if 'cert' in edge[2]:
            edgeEl.attrib["cert"] = edge[2]['cert']
        




    tree.write( changed_file[0:-3] + '.tei.xml', pretty_print=True, encoding="UTF-8", xml_declaration=True)


        