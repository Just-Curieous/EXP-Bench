#!/usr/bin/env python3
"""
Script to modify the exp_bench_test.csv file by adding three new columns:
1. github_url - extracted from conference-specific JSON files
2. pdf_url - extracted from conference-specific JSON files  
3. design - extracted from design JSON files based on conference, paper_id, and task_index

The script matches papers by title and adds the required columns to all rows.
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path

def load_json_file(file_path):
    """Load JSONL file and return the data as a list."""
    try:
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON on line {line_num} in {file_path}: {e}")
                        continue
        return data
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return []

def get_github_url_from_record(record):
    """Extract github_url from a record, preferring code_url over reproduce_eval.code."""
    if record.get("code_url"):
        return record["code_url"]
    elif record.get("reproduce_eval", {}).get("code"):
        return record["reproduce_eval"]["code"]
    else:
        return None

def create_title_to_info_mapping(conference_data):
    """Create a mapping from paper title to paper info (pdf_url, github_url)."""
    title_mapping = {}
    for record in conference_data:
        title = record.get("title", "").strip()
        if title:
            pdf_url = record.get("pdf_url", "")
            github_url = get_github_url_from_record(record)
            title_mapping[title] = {
                "pdf_url": pdf_url,
                "github_url": github_url or ""
            }
    return title_mapping

def load_regular_json_file(file_path):
    """Load a regular JSON file (not JSONL)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return None

def get_design_data(conference, paper_id, task_index, base_path):
    """Extract design_complexity from the appropriate JSON file."""
    design_file_path = os.path.join(base_path, f"outputs/logs/{conference}/{paper_id}/{paper_id}_complete_final.json")
    
    if not os.path.exists(design_file_path):
        print(f"Warning: Design file not found: {design_file_path}")
        return None
    
    design_data = load_regular_json_file(design_file_path)
    if not design_data or "questions" not in design_data:
        print(f"Warning: Invalid design data structure in {design_file_path}")
        return None
    
    questions = design_data["questions"]
    if not isinstance(questions, list) or task_index >= len(questions):
        print(f"Warning: Invalid task_index {task_index} for file {design_file_path} (has {len(questions)} questions)")
        return None
    
    question_data = questions[task_index]
    design_complexity = question_data.get("design_complexity")
    
    if design_complexity is None:
        print(f"Warning: No design_complexity found at task_index {task_index} in {design_file_path}")
        return None
    
    return design_complexity

def main():
    # Define file paths
    csv_file_path = "/home/patkon/EXP-Bench/outputs/EXP-Bench_hf_cache/exp_bench_test.csv"
    iclr_json_path = "/home/patkon/EXP-Bench/logs/iclr2024/iclr2024_withcode_popularity_stars-100.json"
    neurips_json_path = "/home/patkon/EXP-Bench/logs/neurips2024/neurips_abs_2024_withcode_popularity_stars-100.json"
    base_path = "/home/patkon/EXP-Bench"
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found: {csv_file_path}")
        sys.exit(1)
    
    print("Loading CSV file...")
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    print(f"CSV loaded with {len(df)} rows")
    
    # Load conference JSON files
    print("Loading ICLR JSON file...")
    iclr_data = load_json_file(iclr_json_path)
    print(f"Loaded {len(iclr_data)} ICLR papers")
    
    print("Loading NeurIPS JSON file...")
    neurips_data = load_json_file(neurips_json_path)
    print(f"Loaded {len(neurips_data)} NeurIPS papers")
    
    # Create title mappings
    iclr_mapping = create_title_to_info_mapping(iclr_data)
    neurips_mapping = create_title_to_info_mapping(neurips_data)
    
    print(f"Created mappings: ICLR={len(iclr_mapping)}, NeurIPS={len(neurips_mapping)}")
    
    # Initialize new columns
    df['github_url'] = ''
    df['pdf_url'] = ''
    df['design'] = None
    
    # Track statistics
    stats = {
        'total_rows': len(df),
        'github_url_found': 0,
        'pdf_url_found': 0,
        'design_found': 0,
        'iclr_matched': 0,
        'neurips_matched': 0,
        'no_conference_match': 0
    }
    
    print("Processing rows...")
    for idx, row in df.iterrows():
        conference = row.get('conference', '').strip()
        paper_title = row.get('paper_title', '').strip()
        paper_id = row.get('paper_id', '')
        task_index = row.get('task_index', 0)
        
        if idx % 1000 == 0:
            print(f"Processing row {idx}/{len(df)}")
        
        # Get paper info based on conference
        paper_info = None
        if conference == 'iclr2024':
            paper_info = iclr_mapping.get(paper_title)
            if paper_info:
                stats['iclr_matched'] += 1
        elif conference == 'neurips2024':
            paper_info = neurips_mapping.get(paper_title)
            if paper_info:
                stats['neurips_matched'] += 1
        else:
            stats['no_conference_match'] += 1
            print(f"Warning: Unknown conference '{conference}' at row {idx}")
        
        # Set github_url and pdf_url
        if paper_info:
            df.at[idx, 'github_url'] = paper_info['github_url']
            df.at[idx, 'pdf_url'] = paper_info['pdf_url']
            
            if paper_info['github_url']:
                stats['github_url_found'] += 1
            if paper_info['pdf_url']:
                stats['pdf_url_found'] += 1
        else:
            if conference in ['iclr2024', 'neurips2024']:
                print(f"Warning: No match found for title '{paper_title}' in {conference} at row {idx}")
        
        # Get design data
        try:
            design_data = get_design_data(conference, paper_id, int(task_index), base_path)
            if design_data:
                df.at[idx, 'design'] = json.dumps(design_data)
                stats['design_found'] += 1
        except Exception as e:
            print(f"Warning: Error getting design data for row {idx}: {e}")
    
    # Print statistics
    print("\n=== Processing Statistics ===")
    print(f"Total rows processed: {stats['total_rows']}")
    print(f"ICLR papers matched: {stats['iclr_matched']}")
    print(f"NeurIPS papers matched: {stats['neurips_matched']}")
    print(f"Rows with unknown conference: {stats['no_conference_match']}")
    print(f"GitHub URLs found: {stats['github_url_found']}")
    print(f"PDF URLs found: {stats['pdf_url_found']}")
    print(f"Design data found: {stats['design_found']}")
    
    # Check if all rows have values for the new columns
    missing_github = df['github_url'].isna().sum() + (df['github_url'] == '').sum()
    missing_pdf = df['pdf_url'].isna().sum() + (df['pdf_url'] == '').sum()
    missing_design = df['design'].isna().sum()
    
    print(f"\n=== Missing Data Check ===")
    print(f"Rows missing github_url: {missing_github}")
    print(f"Rows missing pdf_url: {missing_pdf}")
    print(f"Rows missing design: {missing_design}")
    
    if missing_github > 0 or missing_pdf > 0 or missing_design > 0:
        print("WARNING: Not all rows have complete data!")
    else:
        print("SUCCESS: All rows have values for all three new columns!")
    
    # Save the modified CSV
    output_file = csv_file_path.replace('.csv', '_modified.csv')
    print(f"\nSaving modified CSV to: {output_file}")
    try:
        df.to_csv(output_file, index=False)
        print("File saved successfully!")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)
    
    print("\n=== Script completed successfully! ===")

if __name__ == "__main__":
    main()