#!/usr/bin/env python3
"""
Convert Hyperlink Network CSV to SocNetV GraphML Format (with labels)
Creates a GraphML file that SocNetV can import with visible node labels.
"""

import csv
import sys
from urllib.parse import urlparse


def escape_xml(text):
    """Escape special XML characters."""
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text


def convert_to_graphml(input_csv='hyperlink_network.csv', 
                       url_input='url_input.txt',
                       output_graphml='socnetv_network.graphml'):
    """
    Convert hyperlink network CSV to GraphML format with node labels.
    
    Args:
        input_csv: Input CSV file with Source, Target, Weight, Label columns
        url_input: Original URL input file with Actor names
        output_graphml: Output GraphML file for SocNetV
    """
    
    print("=" * 60)
    print("🔄 Converting to SocNetV GraphML Format (with Labels)")
    print("=" * 60)
    
    # Step 1: Read actor names from url_input.txt
    print(f"\n📖 Reading actor names from: {url_input}")
    url_to_actor = {}
    try:
        with open(url_input, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row['URL'].strip()
                actor = row['Actor'].strip()
                url_to_actor[url] = actor
        print(f"✅ Found {len(url_to_actor)} actors")
    except Exception as e:
        print(f"⚠️  Could not read actor names: {e}")
        print("   Continuing without actor labels...")
    
    # Step 2: Read the hyperlink network CSV and collect unique URLs
    print(f"\n📖 Reading network data from: {input_csv}")
    edges = []
    unique_urls = set()
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                source = row['Source'].strip()
                target = row['Target'].strip()
                weight = int(row['Weight'])
                
                unique_urls.add(source)
                unique_urls.add(target)
                edges.append((source, target, weight))
        
        print(f"✅ Read {len(edges)} edges")
        print(f"✅ Found {len(unique_urls)} unique nodes (URLs)")
    except Exception as e:
        print(f"❌ Error reading input file: {e}")
        sys.exit(1)
    
    # Step 3: Create URL to numeric ID mapping
    print(f"\n🔢 Creating node ID mapping...")
    url_to_id = {}
    id_to_url = {}
    
    # Sort URLs for consistent ordering
    sorted_urls = sorted(unique_urls)
    
    for idx, url in enumerate(sorted_urls, start=1):
        url_to_id[url] = f"n{idx}"
        id_to_url[f"n{idx}"] = url
    
    print(f"✅ Mapped {len(url_to_id)} URLs to node IDs")
    
    # Step 4: Write GraphML file
    print(f"\n📝 Writing GraphML file to: {output_graphml}")
    try:
        with open(output_graphml, 'w', encoding='utf-8') as f:
            # Write GraphML header
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n')
            f.write('         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
            f.write('         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n')
            f.write('         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n\n')
            
            # Define attributes
            f.write('  <!-- Define node and edge attributes -->\n')
            f.write('  <key id="label" for="node" attr.name="label" attr.type="string"/>\n')
            f.write('  <key id="url" for="node" attr.name="url" attr.type="string"/>\n')
            f.write('  <key id="actor" for="node" attr.name="actor" attr.type="string"/>\n')
            f.write('  <key id="weight" for="edge" attr.name="weight" attr.type="int"/>\n\n')
            
            # Create graph (directed)
            f.write('  <graph id="HyperlinkNetwork" edgedefault="directed">\n\n')
            
            # Write nodes
            f.write('    <!-- Nodes -->\n')
            for node_id in sorted(id_to_url.keys(), key=lambda x: int(x[1:])):
                url = id_to_url[node_id]
                actor = url_to_actor.get(url, '')
                
                # Create a readable label
                if actor:
                    label = actor
                else:
                    # Extract domain as label if no actor name
                    domain = urlparse(url).netloc
                    label = domain
                
                f.write(f'    <node id="{escape_xml(node_id)}">\n')
                f.write(f'      <data key="label">{escape_xml(label)}</data>\n')
                f.write(f'      <data key="url">{escape_xml(url)}</data>\n')
                f.write(f'      <data key="actor">{escape_xml(actor)}</data>\n')
                f.write(f'    </node>\n')
            
            f.write('\n    <!-- Edges -->\n')
            # Write edges
            edge_count = 0
            for source_url, target_url, weight in edges:
                source_id = url_to_id[source_url]
                target_id = url_to_id[target_url]
                edge_count += 1
                
                f.write(f'    <edge id="e{edge_count}" source="{escape_xml(source_id)}" target="{escape_xml(target_id)}">\n')
                f.write(f'      <data key="weight">{weight}</data>\n')
                f.write(f'    </edge>\n')
            
            # Close graph and graphml
            f.write('  </graph>\n')
            f.write('</graphml>\n')
        
        print(f"✅ Successfully wrote GraphML file with {len(id_to_url)} nodes and {len(edges)} edges")
    except Exception as e:
        print(f"❌ Error writing GraphML file: {e}")
        sys.exit(1)
    
    # Step 5: Print summary
    print("\n" + "=" * 60)
    print("📊 CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total Nodes:  {len(unique_urls)}")
    print(f"Total Edges:  {len(edges)}")
    print(f"\nOutput File Created:")
    print(f"  {output_graphml}")
    print(f"  → GraphML format with node labels and edge weights")
    print("\n" + "=" * 60)
    print("✅ CONVERSION COMPLETE!")
    print("=" * 60)
    print(f"\n💡 To use in SocNetV:")
    print(f"   1. Open SocNetV")
    print(f"   2. Go to: Network → Import → GraphML")
    print(f"   3. Select file: {output_graphml}")
    print(f"   4. Node labels will be visible as organization names!")
    print(f"\n💡 Node Labels:")
    
    # Show some example labels
    example_count = 0
    for node_id in sorted(id_to_url.keys(), key=lambda x: int(x[1:]))[:10]:
        url = id_to_url[node_id]
        actor = url_to_actor.get(url, '')
        if actor:
            label = actor
        else:
            label = urlparse(url).netloc
        print(f"   {node_id} = {label}")
        example_count += 1
    
    if len(id_to_url) > 10:
        print(f"   ... and {len(id_to_url) - 10} more nodes")
    print()


def main():
    """Main function to run the conversion."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert hyperlink network CSV to SocNetV GraphML format with labels.'
    )
    parser.add_argument(
        '-i', '--input',
        default='hyperlink_network.csv',
        help='Input CSV file (default: hyperlink_network.csv)'
    )
    parser.add_argument(
        '-u', '--urls',
        default='url_input.txt',
        help='URL input file with actor names (default: url_input.txt)'
    )
    parser.add_argument(
        '-o', '--output',
        default='socnetv_network.graphml',
        help='Output GraphML file (default: socnetv_network.graphml)'
    )
    
    args = parser.parse_args()
    
    convert_to_graphml(
        input_csv=args.input,
        url_input=args.urls,
        output_graphml=args.output
    )


if __name__ == '__main__':
    main()

