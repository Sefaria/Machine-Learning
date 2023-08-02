import django, json, srsly, csv

django.setup()
# from sefaria.model import *
# from tqdm import tqdm
# from spacy.lang.he import Hebrew
# from sefaria.spacy_function_registry import inner_punct_tokenizer_factory
# from sefaria.model.linker.ref_part import span_inds
# from util.helper import create_normalizer
import random
import sys


def is_bavli(mention):
    if "Mishnah" not in mention['meta']['ref'] and "Jerusalem" not in mention['meta']['ref']:
        return True
    else:
        return False


def is_yerushalmi(mention):
    if "Jerusalem" in mention['meta']['ref']:
        return True
    else:
        return False


def is_mishna(mention):
    if "Mishnah" in mention['meta']['ref']:
        return True
    else:
        return False


def stochastic_selection(p):
    if random.random() < p:
        return True
    else:
        return False

def compute_priors(mentions_list):
    bavli_count, yerushalmi_count, mishna_count = count_mention_types(mentions_list)
    all_count = bavli_count+yerushalmi_count+mishna_count
    return bavli_count/all_count, yerushalmi_count/all_count, mishna_count/all_count

def count_mention_types(mentions_list):
    bavli_count = 0
    yerushalmi_count = 0
    mishna_count = 0
    for par in mentions_list:
        if is_bavli(par):
            bavli_count+=1
        elif is_yerushalmi(par):
            yerushalmi_count+=1
        elif is_mishna(par):
            mishna_count+=1
    return bavli_count, yerushalmi_count, mishna_count


if __name__ == "__main__":
    # print("hello world")

    all_data_file = sys.argv[1]
    portion_of_data = float(sys.argv[2])
    bavli_weight = float(sys.argv[3])
    yerushalmi_weight = float(sys.argv[4])
    mishna_weight = float(sys.argv[5])
    denominator = bavli_weight+yerushalmi_weight+mishna_weight

    q_bavli = bavli_weight/denominator
    q_yerushalmi = yerushalmi_weight/denominator
    q_mishna = mishna_weight/denominator


    # probability_for_training = float(sys.argv[2])

    training = []
    test = []
    minimum_portion = 0

    with open(all_data_file) as f:
        data = json.load(f)
        prior_bavli, prior_yerushalmi, prior_mishna = compute_priors(data)

        #Bayse:
        p_bavli = (portion_of_data * q_bavli) / prior_bavli
        p_yerushalmi = (portion_of_data * q_yerushalmi) / prior_yerushalmi
        p_mishna = (portion_of_data * q_mishna) / prior_mishna

        max_portion = 1 / max(q_bavli/prior_bavli, q_yerushalmi/prior_yerushalmi, q_mishna/prior_mishna)


        for item in data:
            p = 0
            if is_bavli(item):
                p = p_bavli
            elif is_yerushalmi(item):
                p = p_yerushalmi
            elif is_mishna(item):
                p = p_mishna
            
            if stochastic_selection(p):
                training.append(item)
            else:
                test.append(item)

    bavli_count, yerushalmi_count, mishna_count = count_mention_types(training)
    print("bavli training refs: " + str(bavli_count))
    print("yerushalmi training refs: " + str(yerushalmi_count))
    print("mishna training refs: " + str(mishna_count))
    print("all training refs: " + str(bavli_count+yerushalmi_count+mishna_count))
    print("max possible 'portion' of all data: " + str(max_portion))


    with open('generated_training_set.json', 'w') as f:
        json.dump(training, f, ensure_ascii=False, indent=2)
    with open('generated_test_set.json', 'w') as f:
        json.dump(test, f, ensure_ascii=False, indent=2)
