import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm


if __name__ == "__main__":
    print("hello world")
    # stats

    with open('aggregated.json') as f:
        aggregated_mentions = json.load(f)

    aggregated_en = []
    aggregated_he = []


    for mention in tqdm(aggregated_mentions, desc="separating mentions"):

        if mention["meta"]["language"] == "en":
            aggregated_en.append(mention)
        elif mention["meta"]["language"] == "he":
            aggregated_he.append(mention)



    with open("aggregated_en.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(aggregated_en, f, ensure_ascii=False, indent=2)

    with open("aggregated_he.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(aggregated_he, f, ensure_ascii=False, indent=2)

    print("finish")
