#!/usr/bin/env python3
"""
File Size Compression Script
- Compresses images by reducing file size, not resolution
- Uses quality optimization and format-specific compression
- Maintains original dimensions and format
- Outputs to a separate 'compressed_by_size' folder
"""

import os
from pathlib import Path
from PIL import Image
import io

# Configuration
SOURCE_DIR = Path(__file__).parent  # Process images in the same folder as the script
OUTPUT_DIR = Path(__file__).parent / "output"  # Output to "output" folder
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff'}

# Compression settings
JPEG_QUALITY = 85  # 85% quality for JPEG (good balance between size and quality)
PNG_OPTIMIZE = True  # Enable PNG optimization
WEBP_QUALITY = 85  # 85% quality for WebP

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

def compress_png(img, output_path):
    """Compress PNG with optimization"""
    # PNG compression uses palette reduction and optimization
    # Convert RGBA to RGB if no transparency is actually used
    if img.mode == 'RGBA':
        # Check if alpha channel is actually used
        alpha = img.split()[-1]
        if alpha.getextrema() == (255, 255):
            # No transparency, convert to RGB
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1])
            rgb_img.save(output_path, 'PNG', optimize=True, compress_level=9)
        else:
            # Has transparency, keep RGBA
            img.save(output_path, 'PNG', optimize=True, compress_level=9)
    else:
        img.save(output_path, 'PNG', optimize=True, compress_level=9)

def compress_jpeg(img, output_path):
    """Compress JPEG with quality setting"""
    # Convert to RGB if needed (JPEG doesn't support transparency)
    if img.mode in ('RGBA', 'LA', 'P'):
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = rgb_img
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    img.save(output_path, 'JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)

def compress_webp(img, output_path):
    """Compress WebP with quality setting"""
    img.save(output_path, 'WEBP', quality=WEBP_QUALITY, method=6)

def compress_image(image_path):
    """Process a single image with size-based compression"""
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
            
            output_path = OUTPUT_DIR / file_name
            
            # Apply format-specific compression
            if file_ext in ['.jpg', '.jpeg']:
                compress_jpeg(img, output_path)
            elif file_ext == '.png':
                compress_png(img, output_path)
            elif file_ext == '.webp':
                compress_webp(img, output_path)
            else:
                # For other formats, use default optimization
                img.save(output_path, optimize=True, quality=85)
            
            # Get compressed file size
            compressed_size = output_path.stat().st_size
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            print(f"   Compressed size: {format_size(compressed_size)}")
            
            if reduction > 0:
                print(f"   ✓ Reduction: {reduction:.1f}% smaller")
            elif reduction < 0:
                print(f"   ⚠ Size increased: {abs(reduction):.1f}% (keeping compressed version)")
            else:
                print(f"   → Same size")
            
            return True, original_size, compressed_size
            
    except Exception as e:
        print(f"   ✗ Error processing {image_path.name}: {str(e)}")
        return False, 0, 0

def main():
    """Main execution function"""
    print("=" * 70)
    print("🗜️  File Size Compression Tool")
    print("=" * 70)
    print(f"Source: {SOURCE_DIR}")
    print(f"JPEG Quality: {JPEG_QUALITY}%")
    print(f"PNG Optimization: {PNG_OPTIMIZE}")
    print(f"WebP Quality: {WEBP_QUALITY}%")
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
        success, orig_size, comp_size = compress_image(image_path)
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
        print(f"   Total reduction: {total_reduction:.1f}%")
        print(f"   Space saved: {format_size(space_saved)}")
    
    print(f"   Output location: {OUTPUT_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
