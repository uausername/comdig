import json # This is a built-in library

def extract_comment_details_to_txt(json_filepath="comments_rank_1.json",
                                     output_txt_filepath="extracted_rank_1_comments.txt"):
    """
    Reads comments from a JSON file (expected to contain rank 1.0 comments),
    extracts "comment_url", "text", and "likes", and writes them to a
    formatted TXT file.

    Args:
        json_filepath (str): Path to the input JSON file.
        output_txt_filepath (str): Path to save the extracted details in TXT format.
    """
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f_in:
            comments_data = json.load(f_in)
    except FileNotFoundError:
        print(f"Error: Input file '{json_filepath}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_filepath}'. Ensure it's a valid JSON array.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading the input file: {e}")
        return

    if not isinstance(comments_data, list):
        print(f"Error: Expected a list of comments in '{json_filepath}', but got {type(comments_data)}.")
        return

    try:
        with open(output_txt_filepath, 'w', encoding='utf-8') as f_out:
            for i, comment in enumerate(comments_data, 1):
                text = comment.get("text", "N/A") # Default to "N/A" if missing
                url = comment.get("comment_url", "N/A") # Default to "N/A" if missing
                
                # Handle likes: if key is missing or value is None, default to 0
                likes = comment.get("likes")
                if likes is None: # JSON null becomes Python None
                    likes_count = 0
                else:
                    likes_count = likes

                # Write the formatted entry
                f_out.write(f"{i}. {text}.\n")
                f_out.write(f"LINK: {url}\n")
                f_out.write(f"Likes: {likes_count}\n")
                
                # Add an empty row between entries, but not after the last one
                if i < len(comments_data):
                    f_out.write("\n")
            
        print(f"Successfully extracted {len(comments_data)} comments to '{output_txt_filepath}'")

    except Exception as e:
        print(f"An error occurred while writing to '{output_txt_filepath}': {e}")

if __name__ == '__main__':
    # This will use the default filenames:
    # input: "comments_rank_1.json"
    # output: "extracted_rank_1_comments.txt"
    extract_comment_details_to_txt()

    # You can also specify different filenames if needed:
    # extract_comment_details_to_txt(json_filepath="my_filtered_comments.json",
    #                                output_txt_filepath="details_output.txt")