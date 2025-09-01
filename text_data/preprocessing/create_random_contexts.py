import os
import json
import random
import re
from pathlib import Path

def clean_metadata(text: str) -> str:
    if not text:
        return ""
    # A safer regex for parentheses: matches a '(', then any number of non-')' chars, then a ')'.
    # This prevents catastrophic matches across the whole text.
    cleaned_text = re.sub(r'\([^\\]*\)', ' ', text)
    cleaned_text = re.sub(r'\[[^\\]*\]', ' ', cleaned_text)
    
    # Remove specific metadata patterns identified from examples
    cleaned_text = re.sub(r'The Journal of the Convergence on Culture Technology[\s\S]*?-\s?\d+\s?-', ' ', cleaned_text)
    cleaned_text = re.sub(r'Figure\d+\..*?', ' ', cleaned_text)
    cleaned_text = re.sub(r'그림\s?\d+\..*?', ' ', cleaned_text)

    # ADDED: Remove separator lines like '----------'
    cleaned_text = re.sub(r'\n-+[\n\s]*', '\n', cleaned_text)
    cleaned_text = re.sub(r'-{10,}', '', cleaned_text)

    # Remove leading Q./A.
    cleaned_text = re.sub(r'^[QA]\.\s*', '', cleaned_text.strip())
    
    # Normalize whitespace
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

def create_final_reranker_data(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for jsonl_file in input_path.glob("*_chunks_qa.jsonl"):
        print(f"Processing {jsonl_file.name}...")

        all_chunks = []
        original_data_list = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                original_data_list.append(data)
                all_chunks.append(data.get("chunk_text", ""))

        if len(all_chunks) < 3:
            print(f"Warning: Not enough chunks ({len(all_chunks)}) in {jsonl_file.name} to sample from. Skipping file.")
            continue

        new_lines_to_write = []
        for i, original_data in enumerate(original_data_list):
            positive_chunk_raw = original_data.get("chunk_text", "")

            # MODIFIED: Ensure negative chunks are unique and not same as positive
            positive_chunk_cleaned = clean_metadata(positive_chunk_raw)

            # Create a pool of all other chunks
            other_chunks_pool = all_chunks[:i] + all_chunks[i+1:]
            
            # Clean the pool and filter out any exact matches to the positive chunk
            negative_candidates = list(set([
                clean_metadata(chunk) for chunk in other_chunks_pool 
                if clean_metadata(chunk) != positive_chunk_cleaned and chunk
            ]))

            # Sample 2 negative chunks
            if len(negative_candidates) >= 2:
                negative_chunks_cleaned = random.sample(negative_candidates, 2)
            else:
                # If not enough unique candidates, take what's available and fill with placeholders if needed
                negative_chunks_cleaned = negative_candidates
                while len(negative_chunks_cleaned) < 2:
                    negative_chunks_cleaned.append("(no unique context available)")

            # Use tuples to robustly track the positive context
            pos_tuple = (positive_chunk_cleaned, True)
            neg_tuples = [(chunk, False) for chunk in negative_chunks_cleaned]
            
            contexts_tuples = [pos_tuple] + neg_tuples
            random.shuffle(contexts_tuples)

            # Find the 1-based index of the positive item after shuffling
            positive_idx = -1
            for idx, item_tuple in enumerate(contexts_tuples):
                if item_tuple[1]: # Check the boolean flag
                    positive_idx = idx + 1
                    break
            
            # Create the final list of strings for the 'contexts' field
            final_contexts_str_list = [item[0] for item in contexts_tuples]
            formatted_contexts = [f"[{k+1}] {chunk}" for k, chunk in enumerate(final_contexts_str_list)]

            updated_data = original_data
            updated_data['contexts'] = formatted_contexts
            updated_data['positive_index'] = positive_idx
            new_lines_to_write.append(updated_data)

        output_file = output_path / jsonl_file.name
        with open(output_file, 'w', encoding='utf-8') as f:
            for line_data in new_lines_to_write:
                f.write(json.dumps(line_data, ensure_ascii=False) + '\n')
        print(f"Finished processing {jsonl_file.name}. Saved to {output_file}")

def main():
    INPUT_DIRECTORY = "./chunking_result"
    OUTPUT_DIRECTORY = "./reranker_final_data"
    create_final_reranker_data(INPUT_DIRECTORY, OUTPUT_DIRECTORY)

if __name__ == "__main__":
    main()
