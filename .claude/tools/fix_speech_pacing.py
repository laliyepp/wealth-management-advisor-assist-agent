#!/usr/bin/env python3
"""Minimal speech pacing fixer with randomness"""

import re
import sys
import random


def parse_time(time_str):
    """Convert WebVTT timestamp to seconds"""
    parts = time_str.strip().split(':')
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def format_time(seconds):
    """Convert seconds to WebVTT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def fix_speech_pacing(file_path, target_min=2.0, target_max=3.0):
    """Fix speech pacing to be within target range"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract subtitle blocks with line numbers
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a timestamp line
        if '-->' in line:
            # Parse timestamps
            parts = line.split(' --> ')
            start_str, end_str = parts[0], parts[1]
            start = parse_time(start_str)
            end = parse_time(end_str)
            duration = end - start
            
            # Get text content (next non-empty lines)
            text_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip():
                text_lines.append(lines[j])
                j += 1
            
            if text_lines:
                # Clean and count words
                text = ' '.join(text_lines)
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                word_count = len(re.findall(r'\b\w+\b', clean_text))
                
                if word_count > 0:
                    current_wps = word_count / duration
                    
                    # Fix if outside target range
                    if current_wps < target_min or current_wps > target_max:
                        # Calculate ideal duration with some randomness
                        ideal_wps = random.uniform(target_min, target_max)
                        new_duration = word_count / ideal_wps
                        
                        # Add small random variation (±0.2 seconds)
                        variation = random.uniform(-0.2, 0.2)
                        new_duration += variation
                        
                        # Ensure minimum duration
                        new_duration = max(new_duration, 0.5)
                        
                        # Update end time
                        new_end = start + new_duration
                        new_end_str = format_time(new_end)
                        
                        new_lines.append(f"{start_str} --> {new_end_str}")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            
            # Add text lines
            for text_line in text_lines:
                new_lines.append(text_line)
            
            i = j
        else:
            new_lines.append(line)
            i += 1
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"Fixed speech pacing in {file_path}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python fix_speech_pacing.py <webvtt_file>")
        sys.exit(1)
    
    fix_speech_pacing(sys.argv[1])