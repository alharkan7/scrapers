#!/usr/bin/env python3
"""
Convert Hyperlink Network CSV to SocNetV GML Format (with labels)
Creates a GML file that SocNetV can import with visible node labels.
"""

import csv
import sys
from urllib.parse import urlparse


def escape_gml_string(text):
    """Escape special characters for GML strings."""
    text = str(text)
    # Escape backslashes and quotes
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    return text


def convert_to_gml(input_csv='hyperlink_network.csv', 
                   url_input='url_input.txt',
                   output_gml='socnetv_network.gml'):
    """
    Convert hyperlink network CSV to GML format with node labels.
    
    Args:
        input_csv: Input CSV file with Source, Target, Weight, Label columns
        url_input: Original URL input file with Actor names
        output_gml: Output GML file for SocNetV
    """
    
    print("=" * 60)
    print("🔄 Converting to SocNetV GML Format (with Labels)")
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
        url_to_id[url] = idx
        id_to_url[idx] = url
    
    print(f"✅ Mapped {len(url_to_id)} URLs to node IDs")
    
    # Step 4: Write GML file
    print(f"\n📝 Writing GML file to: {output_gml}")
    try:
        with open(output_gml, 'w', encoding='utf-8') as f:
            # Write GML header
            f.write('graph [\n')
            f.write('  comment "Hyperlink Network Analysis"\n')
            f.write('  directed 1\n')
            f.write('\n')
            
            # Write nodes
            f.write('  /* Nodes */\n')
            for node_id in sorted(id_to_url.keys()):
                url = id_to_url[node_id]
                actor = url_to_actor.get(url, '')
                
                # Create a readable label
                if actor:
                    label = actor
                else:
                    # Extract domain as label if no actor name
                    domain = urlparse(url).netloc
                    label = domain
                
                f.write(f'  node [\n')
                f.write(f'    id {node_id}\n')
                f.write(f'    label "{escape_gml_string(label)}"\n')
                f.write(f'  ]\n')
            
            f.write('\n  /* Edges */\n')
            # Write edges
            for source_url, target_url, weight in edges:
                source_id = url_to_id[source_url]
                target_id = url_to_id[target_url]
                
                f.write(f'  edge [\n')
                f.write(f'    source {source_id}\n')
                f.write(f'    target {target_id}\n')
                f.write(f'    value {weight}\n')
                f.write(f'  ]\n')
            
            # Close graph
            f.write(']\n')
        
        print(f"✅ Successfully wrote GML file with {len(id_to_url)} nodes and {len(edges)} edges")
    except Exception as e:
        print(f"❌ Error writing GML file: {e}")
        sys.exit(1)
    
    # Step 5: Print summary
    print("\n" + "=" * 60)
    print("📊 CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total Nodes:  {len(unique_urls)}")
    print(f"Total Edges:  {len(edges)}")
    print(f"\nOutput File Created:")
    print(f"  {output_gml}")
    print(f"  → GML format with node labels and edge weights")
    print("\n" + "=" * 60)
    print("✅ CONVERSION COMPLETE!")
    print("=" * 60)
    print(f"\n💡 To use in SocNetV:")
    print(f"   1. Open SocNetV")
    print(f"   2. Go to: Network → Import → GML")
    print(f"   3. Select file: {output_gml}")
    print(f"   4. Node labels will be visible as organization names!")
    print(f"\n💡 Node Labels (first 10):")
    
    # Show some example labels
    for node_id in sorted(id_to_url.keys())[:10]:
        url = id_to_url[node_id]
        actor = url_to_actor.get(url, '')
        if actor:
            label = actor
        else:
            label = urlparse(url).netloc
        print(f"   Node {node_id} = {label}")
    
    if len(id_to_url) > 10:
        print(f"   ... and {len(id_to_url) - 10} more nodes")
    print()


def main():
    """Main function to run the conversion."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert hyperlink network CSV to SocNetV GML format with labels.'
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
        default='socnetv_network.gml',
        help='Output GML file (default: socnetv_network.gml)'
    )
    
    args = parser.parse_args()
    
    convert_to_gml(
        input_csv=args.input,
        url_input=args.urls,
        output_gml=args.output
    )


if __name__ == '__main__':
    main()

