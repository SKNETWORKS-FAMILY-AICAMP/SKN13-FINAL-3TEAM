
import json
import os
import random
import glob
from pathlib import Path
import math

# --- Configuration ---
INPUT_DIR = './reranker_final_data'
OUTPUT_DIR = './split_data'
TRAIN_RATIO = 0.8
VALID_RATIO = 0.1
# TEST_RATIO is implicitly 0.1

# --- Functions ---
def load_all_data(base_dir):
    """Loads all QA pairs from .jsonl files in the specified directory."""
    all_data = []
    # Use Path and glob to handle filenames with spaces correctly
    p = Path(base_dir)
    jsonl_files = list(p.glob('*.jsonl'))
    
    if not jsonl_files:
        print(f"Warning: No .jsonl files found in {base_dir}")
        return []

    for file_path in jsonl_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        all_data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Warning: JSON parsing error in {file_path}: {e} - Line: {line[:100]}...")
    return all_data

def write_jsonl(data, file_path):
    """Writes a list of dictionaries to a .jsonl file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"✅ {len(data)} items saved to {file_path}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting data splitting script...")

    # 1. Load all data
    all_qa_data = load_all_data(INPUT_DIR)
    total_data_count = len(all_qa_data)
    print(f"Loaded a total of {total_data_count} QA pairs.")

    if total_data_count > 0:
        # 2. Shuffle data
        random.seed(42) # for reproducibility
        random.shuffle(all_qa_data)

        # 3. Calculate split sizes
        train_end_idx = math.ceil(total_data_count * TRAIN_RATIO)
        valid_end_idx = train_end_idx + math.ceil(total_data_count * VALID_RATIO)

        # 4. Split data
        train_data = all_qa_data[:train_end_idx]
        valid_data = all_qa_data[train_end_idx:valid_end_idx]
        test_data = all_qa_data[valid_end_idx:]

        # 5. Save split data
        fields_to_keep = ['question', 'answer', 'contexts', 'positive_index']
        train_data_final = [{key: d[key] for key in fields_to_keep if key in d} for d in train_data]
        valid_data_final = [{key: d[key] for key in fields_to_keep if key in d} for d in valid_data]
        test_data_final = [{key: d[key] for key in fields_to_keep if key in d} for d in test_data]

        write_jsonl(train_data_final, os.path.join(OUTPUT_DIR, 'train02.jsonl'))
        write_jsonl(valid_data_final, os.path.join(OUTPUT_DIR, 'validation02.jsonl'))
        write_jsonl(test_data_final, os.path.join(OUTPUT_DIR, 'test02.jsonl'))

        print("\nData splitting and saving complete.")
        print(f"  - Training data: {len(train_data)} items")
        print(f"  - Validation data: {len(valid_data)} items")
        print(f"  - Test data: {len(test_data)} items")
