import json # This is a built-in library

def export_comments_by_rank(input_filepath="comments.json",
                              output_rank_0_filepath="comments_rank_0.json",
                              output_rank_1_filepath="comments_rank_1.json"):
    """
    Reads comments from a JSON file, filters them by 'comment_rank',
    and exports them to two separate JSON files.

    Args:
        input_filepath (str): Path to the input JSON file.
        output_rank_0_filepath (str): Path to save comments with rank 0.0.
        output_rank_1_filepath (str): Path to save comments with rank 1.0.
    """
    comments_rank_0 = []
    comments_rank_1 = []

    try:
        with open(input_filepath, 'r', encoding='utf-8') as f_in:
            all_comments = json.load(f_in)
    except FileNotFoundError:
        print(f"Error: Input file '{input_filepath}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filepath}'. Ensure it's a valid JSON array.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading the input file: {e}")
        return

    for comment in all_comments:
        # Using .get() is safer as it returns None if the key is missing,
        # rather than raising a KeyError.
        rank = comment.get("comment_rank")
        
        if rank == 0.0:
            comments_rank_0.append(comment)
        elif rank == 1.0:
            comments_rank_1.append(comment)

    try:
        with open(output_rank_0_filepath, 'w', encoding='utf-8') as f_out_0:
            # indent=2 makes the JSON file human-readable
            # ensure_ascii=False allows non-ASCII characters (like Cyrillic) to be written as is
            json.dump(comments_rank_0, f_out_0, indent=2, ensure_ascii=False)
        print(f"Successfully wrote {len(comments_rank_0)} comments to '{output_rank_0_filepath}'")
    except Exception as e:
        print(f"An error occurred while writing to '{output_rank_0_filepath}': {e}")

    try:
        with open(output_rank_1_filepath, 'w', encoding='utf-8') as f_out_1:
            json.dump(comments_rank_1, f_out_1, indent=2, ensure_ascii=False)
        print(f"Successfully wrote {len(comments_rank_1)} comments to '{output_rank_1_filepath}'")
    except Exception as e:
        print(f"An error occurred while writing to '{output_rank_1_filepath}': {e}")

if __name__ == '__main__':
    # This will use the default filenames:
    # input: "comments.json"
    # output for rank 0.0: "comments_rank_0.json"
    # output for rank 1.0: "comments_rank_1.json"
    export_comments_by_rank()

    # You can also specify different filenames if needed:
    # export_comments_by_rank(input_filepath="my_source_comments.json",
    #                           output_rank_0_filepath="output_zero.json",
    #                           output_rank_1_filepath="output_one.json")