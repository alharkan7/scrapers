#!/usr/bin/env python3
"""
Intelligent Image Compression Script
- Scales down images with any side > 2000px to max 2000px
- Maintains aspect ratio
- Preserves original format and filename
- Outputs to a separate 'compressed' folder
"""

import os
from pathlib import Path
from PIL import Image

# Configuration
SOURCE_DIR = Path(__file__).parent  # Process images in the same folder as the script
OUTPUT_DIR = Path(__file__).parent / "output"  # Output to "output" folder
MAX_DIMENSION = 2000
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff'}

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR}")

def should_resize(width, height):
    """Check if image needs resizing"""
    return width > MAX_DIMENSION or height > MAX_DIMENSION

def calculate_new_dimensions(width, height):
    """Calculate new dimensions while maintaining aspect ratio"""
    if width > height:
        # Width is the limiting factor
        new_width = MAX_DIMENSION
        new_height = int((MAX_DIMENSION / width) * height)
    else:
        # Height is the limiting factor
        new_height = MAX_DIMENSION
        new_width = int((MAX_DIMENSION / height) * width)
    
    return new_width, new_height

def compress_image(image_path):
    """Process a single image"""
    try:
        # Open image
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            file_name = image_path.name
            
            print(f"\n📷 Processing: {file_name}")
            print(f"   Original size: {original_width}x{original_height}px")
            
            # Check if resize is needed
            if should_resize(original_width, original_height):
                new_width, new_height = calculate_new_dimensions(original_width, original_height)
                print(f"   → Resizing to: {new_width}x{new_height}px")
                
                # Resize with high-quality resampling
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save with same format and filename
                output_path = OUTPUT_DIR / file_name
                resized_img.save(output_path, optimize=True, quality=95)
                
                print(f"   ✓ Compressed and saved to: {output_path.name}")
            else:
                print(f"   → No resize needed (both dimensions < {MAX_DIMENSION}px)")
                
                # Still copy to output folder
                output_path = OUTPUT_DIR / file_name
                img.save(output_path, optimize=True, quality=95)
                
                print(f"   ✓ Copied to: {output_path.name}")
            
            return True
            
    except Exception as e:
        print(f"   ✗ Error processing {image_path.name}: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("=" * 60)
    print("🖼️  Intelligent Image Compression Tool")
    print("=" * 60)
    print(f"Source: {SOURCE_DIR}")
    print(f"Max dimension: {MAX_DIMENSION}px")
    print("=" * 60)
    
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
    for image_path in image_files:
        if compress_image(image_path):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✓ Processing complete!")
    print(f"   Successfully processed: {success_count}/{len(image_files)} images")
    print(f"   Output location: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
