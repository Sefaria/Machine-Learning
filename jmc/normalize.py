from util.library_exporter import TextWalker


tw = TextWalker(open("corpus/all_text_en.txt", 'w'), open("corpus/all_text_en.jsonl", 'w'), "en")

with open("all_text_en.txt") as f:
    for line in f:
        tw.write_lines(line.strip())