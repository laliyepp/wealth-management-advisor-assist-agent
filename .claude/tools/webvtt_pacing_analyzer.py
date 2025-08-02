#!/usr/bin/env python3
"""Minimal WebVTT speech pacing analyzer"""

import re
import sys


def parse_time(time_str):
    """Convert WebVTT timestamp to seconds"""
    parts = time_str.strip().split(':')
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def analyze_webvtt_pacing(file_path):
    """Analyze speech pacing from WebVTT file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract subtitle blocks
    blocks = re.findall(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n(.+?)(?=\n\n|\Z)', content, re.DOTALL)
    
    results = []
    for start_str, end_str, text in blocks:
        start = parse_time(start_str)
        end = parse_time(end_str)
        duration = end - start
        
        # Clean text and count words
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        word_count = len(re.findall(r'\b\w+\b', clean_text))
        
        if duration > 0 and word_count > 0:
            wps = word_count / duration
            results.append({
                'start': start_str,
                'duration': duration,
                'words': word_count,
                'wps': round(wps, 2),
                'text': clean_text[:50] + '...' if len(clean_text) > 50 else clean_text
            })
    
    if not results:
        return {'error': 'No valid segments found'}
    
    wps_values = [r['wps'] for r in results]
    total_words = sum(r['words'] for r in results)
    total_duration = sum(r['duration'] for r in results)
    
    return {
        'segments': len(results),
        'avg_wps': round(sum(wps_values) / len(wps_values), 2),
        'overall_wps': round(total_words / total_duration, 2),
        'target_range_2_3_wps': sum(1 for wps in wps_values if 2 <= wps <= 3),
        'out_of_range': sum(1 for wps in wps_values if wps < 2 or wps > 3),
        'fastest': max(results, key=lambda x: x['wps']),
        'slowest': min(results, key=lambda x: x['wps'])
    }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python webvtt_pacing_analyzer.py <file.vtt>")
        sys.exit(1)
    
    try:
        result = analyze_webvtt_pacing(sys.argv[1])
        import json
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")