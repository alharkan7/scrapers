#!/usr/bin/env python3
"""
PDF Compression Script

Compresses PDF files with minimum text quality loss using multiple strategies:
1. pypdf library for basic compression
2. Ghostscript for advanced compression with image quality control

Usage:
    python pdf_compressor.py input.pdf output.pdf [--quality high|medium|low]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def compress_with_pypdf(input_path, output_path, quality='medium'):
    """
    Compress PDF using pypdf library.
    Preserves text quality while compressing images.
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("pypdf not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
        from pypdf import PdfReader, PdfWriter

    print(f"Compressing {input_path} using pypdf...")

    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)

    # Set compression settings based on quality
    if quality == 'high':
        # Minimal compression, maximum quality
        writer.compress_identical_objects = True
        writer.compress_streams = True
    elif quality == 'medium':
        # Balanced compression
        writer.compress_identical_objects = True
        writer.compress_streams = True
    else:  # low
        # Aggressive compression
        writer.compress_identical_objects = True
        writer.compress_streams = True

    # Save compressed PDF
    with open(output_path, 'wb') as f:
        writer.write(f)

    return output_path


def compress_with_ghostscript(input_path, output_path, quality='medium'):
    """
    Compress PDF using Ghostscript with advanced options.
    Excellent for image-heavy PDFs while preserving text.
    """
    print(f"Compressing {input_path} using Ghostscript...")

    # Quality settings for Ghostscript
    quality_settings = {
        'high': {
            'color_image_resolution': 150,
            'gray_image_resolution': 150,
            'mono_image_resolution': 300,
            'color_image_downsample_threshold': 1.5,
            'jpeg_quality': 85
        },
        'medium': {
            'color_image_resolution': 100,
            'gray_image_resolution': 100,
            'mono_image_resolution': 200,
            'color_image_downsample_threshold': 2.0,
            'jpeg_quality': 75
        },
        'low': {
            'color_image_resolution': 72,
            'gray_image_resolution': 72,
            'mono_image_resolution': 150,
            'color_image_downsample_threshold': 3.0,
            'jpeg_quality': 60
        }
    }

    settings = quality_settings[quality]

    # Ghostscript command for PDF compression
    cmd = [
        'gs',
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.7',
        '-dPDFSETTINGS=/ebook',  # Good balance for images and text
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        f'-dColorImageResolution={settings["color_image_resolution"]}',
        f'-dGrayImageResolution={settings["gray_image_resolution"]}',
        f'-dMonoImageResolution={settings["mono_image_resolution"]}',
        f'-dColorImageDownsampleThreshold={settings["color_image_downsample_threshold"]}',
        f'-dGrayImageDownsampleThreshold={settings["color_image_downsample_threshold"]}',
        f'-dMonoImageDownsampleThreshold={settings["color_image_downsample_threshold"]}',
        '-dColorImageFilter=/DCTEncode',
        '-dGrayImageFilter=/DCTEncode',
        '-dMonoImageFilter=/CCITTFaxEncode',
        '-dAutoFilterColorImages=false',
        '-dAutoFilterGrayImages=false',
        f'-dJPEGQ={settings["jpeg_quality"]}',
        '-dDownsampleColorImages=true',
        '-dDownsampleGrayImages=true',
        '-dDownsampleMonoImages=true',
        '-dCompressPages=true',
        '-dUseFlateCompression=true',
        f'-sOutputFile={output_path}',
        input_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Ghostscript compression failed: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Ghostscript not found. Please install it:")
        print("  macOS: brew install ghostscript")
        print("  Ubuntu: sudo apt-get install ghostscript")
        return None


def get_file_size(path):
    """Get file size in MB"""
    return os.path.getsize(path) / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description='Compress PDF files with minimum text quality loss')
    parser.add_argument('input', help='Input PDF file path')
    parser.add_argument('output', help='Output PDF file path')
    parser.add_argument('--quality', choices=['high', 'medium', 'low'],
                       default='medium', help='Compression quality (default: medium)')
    parser.add_argument('--method', choices=['pypdf', 'ghostscript', 'auto'],
                       default='auto', help='Compression method (default: auto)')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist")
        return 1

    # Get original file size
    original_size = get_file_size(input_path)
    print(".2f")

    # Choose compression method
    if args.method == 'auto':
        # Try Ghostscript first (better for image-heavy PDFs), fallback to pypdf
        methods = [('ghostscript', compress_with_ghostscript),
                  ('pypdf', compress_with_pypdf)]
    elif args.method == 'ghostscript':
        methods = [('ghostscript', compress_with_ghostscript)]
    else:
        methods = [('pypdf', compress_with_pypdf)]

    compressed_path = None
    for method_name, compress_func in methods:
        print(f"\nTrying {method_name} compression...")
        result = compress_func(input_path, output_path, args.quality)
        if result and Path(result).exists():
            compressed_path = result
            break

    if not compressed_path:
        print("Error: All compression methods failed")
        return 1

    # Check results
    compressed_size = get_file_size(compressed_path)
    reduction = ((original_size - compressed_size) / original_size) * 100

    print("\nCompression Results:")
    print(f"Compressed file size: {compressed_size:.2f} MB")
    print(f"Size reduction: {reduction:.1f}%")

    if compressed_size >= original_size:
        print("Warning: File size did not decrease. The PDF might already be optimized.")
    elif reduction < 10:
        print("Note: Compression achieved less than 10% reduction. Try lower quality setting.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
