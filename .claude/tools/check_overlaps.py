#!/usr/bin/env python3

import sys

def time_to_seconds(time_str):
    """Convert HH:MM:SS.mmm to seconds"""
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def check_overlaps(file_path):
    """Check for overlapping timestamps in WebVTT file"""
    overlaps = []
    prev_end = 0
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if '-->' in line:
            start_str, end_str = line.strip().split(' --> ')
            start_time = time_to_seconds(start_str)
            end_time = time_to_seconds(end_str)
            
            if start_time < prev_end:
                overlaps.append({
                    'line': i + 1,
                    'timestamp': line.strip(),
                    'start': start_time,
                    'prev_end': prev_end,
                    'overlap': prev_end - start_time
                })
            
            prev_end = end_time
    
    return overlaps

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_overlaps.py <vtt_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    overlaps = check_overlaps(file_path)
    
    print(f"Found {len(overlaps)} overlapping timestamps:")
    for overlap in overlaps:
        print(f"Line {overlap['line']}: {overlap['timestamp']}")
        print(f"  Start: {overlap['start']:.3f}s, Previous end: {overlap['prev_end']:.3f}s")
        print(f"  Overlap: {overlap['overlap']:.3f}s")
        print()