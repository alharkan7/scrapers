#!/usr/bin/env python3
"""
Convert Hyperlink Network CSV to SocNetV Format
Converts hyperlink_network.csv to SocNetV-compatible edge list format.
"""

import csv
import sys


def convert_to_socnetv(input_csv='hyperlink_network.csv', 
                       url_input='url_input.txt',
                       output_edges='socnetv_edges.txt',
                       output_nodes='socnetv_nodes.csv'):
    """
    Convert hyperlink network CSV to SocNetV format.
    
    Args:
        input_csv: Input CSV file with Source, Target, Weight, Label columns
        url_input: Original URL input file with Actor names
        output_edges: Output edge list file for SocNetV (space-separated)
        output_nodes: Output node mapping file (CSV with ID, URL, Actor)
    """
    
    print("=" * 60)
    print("🔄 Converting to SocNetV Format")
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
    
    print(f"✅ Mapped {len(url_to_id)} URLs to numeric IDs (1-{len(url_to_id)})")
    
    # Step 4: Write SocNetV edge list (space-separated, no header)
    print(f"\n📝 Writing SocNetV edge list to: {output_edges}")
    try:
        with open(output_edges, 'w', encoding='utf-8') as f:
            for source_url, target_url, weight in edges:
                source_id = url_to_id[source_url]
                target_id = url_to_id[target_url]
                f.write(f"{source_id} {target_id} {weight}\n")
        
        print(f"✅ Successfully wrote {len(edges)} edges")
    except Exception as e:
        print(f"❌ Error writing edge list: {e}")
        sys.exit(1)
    
    # Step 5: Write node mapping file (CSV with headers for reference)
    print(f"\n📝 Writing node mapping to: {output_nodes}")
    try:
        with open(output_nodes, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['NodeID', 'URL', 'Actor', 'Label'])
            
            for node_id in sorted(id_to_url.keys()):
                url = id_to_url[node_id]
                actor = url_to_actor.get(url, '')
                
                # Create a readable label
                if actor:
                    label = f"{actor} ({node_id})"
                else:
                    # Extract domain as label if no actor name
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    label = f"{domain} ({node_id})"
                
                writer.writerow([node_id, url, actor, label])
        
        print(f"✅ Successfully wrote {len(id_to_url)} node mappings")
    except Exception as e:
        print(f"❌ Error writing node mapping: {e}")
        sys.exit(1)
    
    # Step 6: Print summary statistics
    print("\n" + "=" * 60)
    print("📊 CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total Nodes:  {len(unique_urls)}")
    print(f"Total Edges:  {len(edges)}")
    print(f"\nOutput Files Created:")
    print(f"  1. {output_edges}")
    print(f"     → SocNetV edge list (space-separated: source target weight)")
    print(f"  2. {output_nodes}")
    print(f"     → Node mapping reference (NodeID, URL, Actor, Label)")
    print("\n" + "=" * 60)
    print("✅ CONVERSION COMPLETE!")
    print("=" * 60)
    print(f"\n💡 To use in SocNetV:")
    print(f"   1. Open SocNetV")
    print(f"   2. Go to: Network → Import → Edge List (Weighted)")
    print(f"   3. Select file: {output_edges}")
    print(f"   4. Use {output_nodes} to identify which node ID = which organization")
    print()


def main():
    """Main function to run the conversion."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert hyperlink network CSV to SocNetV format.'
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
        '-e', '--edges',
        default='socnetv_edges.txt',
        help='Output edge list file (default: socnetv_edges.txt)'
    )
    parser.add_argument(
        '-n', '--nodes',
        default='socnetv_nodes.csv',
        help='Output node mapping file (default: socnetv_nodes.csv)'
    )
    
    args = parser.parse_args()
    
    convert_to_socnetv(
        input_csv=args.input,
        url_input=args.urls,
        output_edges=args.edges,
        output_nodes=args.nodes
    )


if __name__ == '__main__':
    main()

