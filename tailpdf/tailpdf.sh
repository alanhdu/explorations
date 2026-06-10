#!/bin/bash

# Check if a file was provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <input.pdf>"
    exit 1
fi

input_pdf="$1"

# Check if file exists
if [ ! -f "$input_pdf" ]; then
    echo "Error: File '$input_pdf' not found"
    exit 1
fi

# Check if pdftk is installed
if ! command -v pdftk &> /dev/null; then
    echo "Error: pdftk is not installed"
    exit 1
fi

# Create temporary output file
output_pdf="output_temp_$$.pdf"

# Remove first page
pdftk "$input_pdf" cat 2-end output "$output_pdf"

# Check if pdftk succeeded
if [ $? -eq 0 ]; then
    # Replace original with modified PDF
    mv "$output_pdf" "$input_pdf"
    echo "Successfully removed first page from '$input_pdf'"
else
    echo "Error: Failed to process PDF"
    # Clean up temp file if it exists
    [ -f "$output_pdf" ] && rm "$output_pdf"
    exit 1
fi
