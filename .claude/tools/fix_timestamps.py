#!/usr/bin/env python3

import sys

def time_to_seconds(time_str):
    """Convert HH:MM:SS.mmm to seconds"""
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def seconds_to_time(seconds):
    """Convert seconds to HH:MM:SS.mmm format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def fix_overlaps(file_path, gap=1.5):
    """Fix overlapping timestamps by adjusting all subsequent timestamps"""
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    adjustment = 0  # cumulative time adjustment
    prev_end = 0
    
    for i, line in enumerate(lines):
        if '-->' in line:
            start_str, end_str = line.strip().split(' --> ')
            start_time = time_to_seconds(start_str) + adjustment
            end_time = time_to_seconds(end_str) + adjustment
            
            # Check if we need additional adjustment for overlap
            if start_time < prev_end:
                additional_adjustment = prev_end - start_time + gap
                adjustment += additional_adjustment
                start_time += additional_adjustment
                end_time += additional_adjustment
                print(f"Fixed overlap at line {i+1}: added {additional_adjustment:.3f}s adjustment")
            
            new_timestamp = f"{seconds_to_time(start_time)} --> {seconds_to_time(end_time)}\n"
            new_lines.append(new_timestamp)
            prev_end = end_time
        else:
            new_lines.append(line)
    
    # Write back fixed file
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Fixed timestamps written to {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_timestamps.py <vtt_file> [gap_seconds]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    gap = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
    
    fix_overlaps(file_path, gap)