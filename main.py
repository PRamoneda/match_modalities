import json

from openai import OpenAI

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def extract_identifiers_with_chain_of_thought(title, client):
    identifiers = {
        "error": True,
        "Composer": "N/A",
        "Title": "N/A",
        "Catalog Number": "N/A",
        "Key": "N/A",
        "Form": "N/A"
    }
    # Define the messages with a chain of thought approach
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that extracts information from classical piano music titles. "
                "Your task is to identify and extract the following components from the title: "
                "composer, title, catalog number, key, and form. "
                "Follow a step-by-step reasoning process to ensure accuracy. "
                "The output should be a standardized JSON object with 'N/A' as placeholders for missing information. "
                "Format composer names as in this example: 'B. Bartok'. Use the first initial of the first name, followed "
                "by a period, and then the full surname without accents or special characters. "
                "Catalog numbers should be formatted as 'op' or another identifier, optionally followed by a comma, "
                "and then the number of the piece, and optionally including the movement. For example: 'op. 25, No. 1'. "
                "Keys should match this pattern: an uppercase letter A-G, optionally followed by '#' or 'b', with 'major' "
                "or 'minor' following, e.g., 'C major', 'F# minor'."
            )
        },
        {
            "role": "user",
            "content": (
                f"Analyze the following title and extract its main identifiers: {title}. "
                "Please ensure that the output is in JSON format with these keys: 'Composer', 'Title', "
                "'Catalog Number', 'Key', and 'Form'. Use 'N/A' for any missing information."
            )
        }
    ]

    # Call the OpenAI Chat API
    response = client.chat.completions.create(
        model="gemma2",
        messages=messages,
        max_tokens=1000,  # Allow for a more detailed response
        temperature=0  # Set temperature to 0 for deterministic output
    )

    # Extract the response content
    extracted_text = response.choices[0].message.content

    # Look for JSON output within the response content
    try:
        # Find the JSON object within the response
        start_idx = extracted_text.index('{')
        end_idx = extracted_text.rindex('}') + 1
        json_text = extracted_text[start_idx:end_idx]

        # Parse the JSON content
        identifiers = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        # Handle parsing errors and provide feedback
        print("Error parsing JSON output:", e)
    identifiers["query"] = title
    identifiers["answer"] = extracted_text

    return identifiers


client = OpenAI(
    base_url='http://localhost:11434/v1/',
    # required but ignored
    api_key='ollama',
)


def cipi():
    parsed_cipi = {}
    data = load_json('original/index_CIPI.json')
    for k, v in data.items():
        metadata = v["composer"] + " " + (v["book"] if "book" in v else "") + " " + v["work_name"]
        identifiers = extract_identifiers_with_chain_of_thought(metadata, client)
        print(json.dumps(identifiers, indent=4))
        parsed_cipi[k] = identifiers
        save_json('parsed/cipi_parsed.json', parsed_cipi)

def audio():
    parsed_audio = {}
    index = load_json('original/split_audio.json')
    data = list(index["0"]["train"].keys()) + list(index["0"]["test"].keys()) + list(index["0"]["val"].keys())
    metadata_composers = {**load_json('original/metadata_men_extended2.json'), **load_json(
        'original/metadata_women_extended2.json')}

    for metadata in data:
        composer = metadata_composers[metadata]["composer"]
        metadata = metadata[len(composer):]
        print(metadata)
        identifiers = extract_identifiers_with_chain_of_thought(metadata, client)
        # plot pretty json
        identifiers["Composer"] = composer
        print(json.dumps(identifiers, indent=4))
        parsed_audio[metadata] = identifiers
        save_json('parsed/audio_parsed.json', parsed_audio)


def fs():
    parsed_fs = {}
    data = load_json('original/index_freescores_difficulty.json')
    for k, v in data.items():
        metadata = v["piece_text"]
        identifiers = extract_identifiers_with_chain_of_thought(metadata, client)
        print(json.dumps(identifiers, indent=4))
        parsed_fs[k] = identifiers
        save_json('parsed/fs_parsed.json', parsed_fs)

def pstreet():
    parsed_fs = {}
    data = load_json('original/index_pianostreet_onlypiano_difficulty.json')
    for k, v in data.items():
        metadata = v["composer"] + " " + v["work"] + " " + v["key"]
        identifiers = extract_identifiers_with_chain_of_thought(metadata, client)
        print(json.dumps(identifiers, indent=4))
        parsed_fs[k] = identifiers
        save_json('parsed/pstreet_parsed.json', parsed_fs)



if __name__ == '__main__':
    fs()
    pstreet()
    cipi()
    audio()


