#!/usr/bin/env python3
"""
Aggressive File Size Compression Script
- Maximum file size reduction using multiple techniques
- Option to convert to WebP format for best compression
- Maintains original dimensions
- Outputs to a separate 'compressed_optimized' folder
"""

import os
from pathlib import Path
from PIL import Image
import argparse

# Configuration
SOURCE_DIR = Path(__file__).parent  # Process images in the same folder as the script
OUTPUT_DIR = Path(__file__).parent / "output"  # Output to "output" folder
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff'}

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR}")

def format_size(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def compress_to_original_format(img, output_path, file_ext):
    """Compress to original format with optimization"""
    if file_ext in ['.jpg', '.jpeg']:
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=85, optimize=True, progressive=True)
    elif file_ext == '.png':
        img.save(output_path, 'PNG', optimize=True, compress_level=9)
    elif file_ext == '.webp':
        img.save(output_path, 'WEBP', quality=85, method=6)
    else:
        img.save(output_path, optimize=True, quality=85)

def compress_to_webp(img, output_path, quality=80):
    """Convert and compress to WebP format"""
    img.save(output_path, 'WEBP', quality=quality, method=6)

def compress_image(image_path, use_webp=False, webp_quality=80):
    """Process a single image with aggressive compression"""
    try:
        # Get original file size
        original_size = image_path.stat().st_size
        
        with Image.open(image_path) as img:
            width, height = img.size
            file_name = image_path.name
            file_ext = image_path.suffix.lower()
            
            print(f"\n📷 Processing: {file_name}")
            print(f"   Dimensions: {width}x{height}px")
            print(f"   Original size: {format_size(original_size)}")
            
            if use_webp:
                # Convert to WebP
                output_name = file_name.rsplit('.', 1)[0] + '.webp'
                output_path = OUTPUT_DIR / output_name
                compress_to_webp(img, output_path, webp_quality)
                print(f"   → Converted to WebP")
            else:
                # Keep original format
                output_path = OUTPUT_DIR / file_name
                compress_to_original_format(img, output_path, file_ext)
            
            # Get compressed file size
            compressed_size = output_path.stat().st_size
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            print(f"   Compressed size: {format_size(compressed_size)}")
            
            if reduction > 0:
                print(f"   ✓ Reduction: {reduction:.1f}% ({format_size(original_size - compressed_size)} saved)")
            elif reduction < 0:
                print(f"   ⚠ Size increased: {abs(reduction):.1f}%")
            else:
                print(f"   → Same size")
            
            return True, original_size, compressed_size
            
    except Exception as e:
        print(f"   ✗ Error processing {image_path.name}: {str(e)}")
        return False, 0, 0

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Compress images by file size')
    parser.add_argument('--webp', action='store_true', 
                       help='Convert all images to WebP format for maximum compression')
    parser.add_argument('--quality', type=int, default=80, 
                       help='WebP quality (1-100, default: 80)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🗜️  Aggressive File Size Compression Tool")
    print("=" * 70)
    print(f"Source: {SOURCE_DIR}")
    
    if args.webp:
        print(f"Mode: Convert to WebP")
        print(f"WebP Quality: {args.quality}%")
    else:
        print(f"Mode: Optimize original formats")
    
    print("=" * 70)
    
    # Ensure output directory exists
    ensure_output_dir()
    
    # Check if source directory exists
    if not SOURCE_DIR.exists():
        print(f"✗ Error: Source directory not found: {SOURCE_DIR}")
        return
    
    # Get all image files (excluding Python scripts and output folder)
    image_files = [
        f for f in SOURCE_DIR.iterdir() 
        if f.is_file() 
        and f.suffix.lower() in SUPPORTED_FORMATS
        and f != Path(__file__)  # Exclude the script itself
        and not str(f).startswith(str(OUTPUT_DIR))  # Exclude output folder
    ]
    
    if not image_files:
        print("✗ No supported image files found in source directory")
        print(f"   Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return
    
    print(f"\n📁 Found {len(image_files)} image(s) to process\n")
    
    # Process each image
    success_count = 0
    total_original = 0
    total_compressed = 0
    
    for image_path in image_files:
        success, orig_size, comp_size = compress_image(
            image_path, 
            use_webp=args.webp, 
            webp_quality=args.quality
        )
        if success:
            success_count += 1
            total_original += orig_size
            total_compressed += comp_size
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✓ Processing complete!")
    print(f"   Successfully processed: {success_count}/{len(image_files)} images")
    print(f"   Total original size: {format_size(total_original)}")
    print(f"   Total compressed size: {format_size(total_compressed)}")
    
    if total_original > 0:
        total_reduction = ((total_original - total_compressed) / total_original) * 100
        space_saved = total_original - total_compressed
        
        if total_reduction > 0:
            print(f"   ✓ Total reduction: {total_reduction:.1f}%")
            print(f"   ✓ Space saved: {format_size(space_saved)}")
        else:
            print(f"   ⚠ Total size increased: {abs(total_reduction):.1f}%")
    
    print(f"   Output location: {OUTPUT_DIR}")
    print("=" * 70)
    
    if not args.webp:
        print("\n💡 Tip: Use --webp flag for better compression (converts to WebP format)")
        print("   Example: python3 compress_images_optimized.py --webp --quality 80")

if __name__ == "__main__":
    main()
