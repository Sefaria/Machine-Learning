import django, re, csv, srsly, json, argparse
django.setup()
from tqdm import tqdm
import fasttext
# from gensim.models import Word2Vec
# from gensim.models.word2vec import LineSentence


def train_fasttext(dim, train_file, output):
    print("FASTTEXT", dim)
    model = fasttext.train_unsupervised(train_file, dim=dim, epoch=10, minCount=10)
    model.save_model(output)

def convert_fasttext_bin_to_vec(in_path, out_path):
    # original BIN model loading
    f = fasttext.load_model(in_path)

    # get all words from model
    words = f.get_words()

    with open(out_path, 'w') as file_out:
        
        # the first line must contain number of total words and vector dimension
        file_out.write(str(len(words)) + " " + str(f.get_dimension()) + "\n")

        # line by line, you append vectors to VEC file
        for w in tqdm(words):
            v = f.get_word_vector(w)
            vstr = ""
            for vi in v:
                vstr += " " + str(vi)
            try:
                file_out.write(w + vstr+'\n')
            except:
                pass


def train_fasttext_links():
    train_file = "all_links.txt"
    model = fasttext.train_unsupervised(train_file, dim=10, epoch=10)
    model.save_model(f"{DATA_LOC}/fasttext_links.bin")

def train_word2vec(lang, dim=100):
    print("WORD2VEC", dim)
    train_file = "all_text_he_no_prefixes.txt" if lang == "he" else "all_text_en.txt"

    model = Word2Vec(LineSentence(train_file), size=dim, window=5, min_count=7, workers=12, sg=1, iter=10)
    model.save(f"{DATA_LOC}/word2vec_{lang}_no_prefixes_{dim}.bin")

def train_word2vec_links():
    train_file = "all_links.txt"
    model = Word2Vec(LineSentence(train_file), size=10, window=5, min_count=7, workers=12, sg=1, iter=10)
    model.save(f"{DATA_LOC}/word2vec_links.bin")

def train_custom_link_embedding_thingy():
    import networkx as nx
    from tqdm import tqdm
    G = nx.Graph()
    node_int_mapping = {}
    edges = []
    with open("all_links.txt", "r") as fin:
        for line in fin:
            refs = line.strip().split()
            for ref in refs:
                if ref not in node_int_mapping:
                    node_int_mapping[ref] = len(node_int_mapping)
                edges += [refs]
    for node, int_node in tqdm(node_int_mapping.items(), total=len(node_int_mapping)):
        G.add_node(int_node)
    for edge in tqdm(edges):
        G.add_edge(node_int_mapping[edge[0]], node_int_mapping[edge[1]])
    spl = dict(nx.all_pairs_shortest_path_length(G, 2))

def init_argparse() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser()
    parser.add_argument('algo', help='what algo do you want to do?')
    parser.add_argument('-i', '--input', dest='input')
    parser.add_argument('-d', '--dim', dest='dim', type=int)
    parser.add_argument('-o', '--output', dest='output_stem')
    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    if args.algo == 'fasttext':
        train_fasttext(args.dim, args.input, args.output_stem + '.bin')
        convert_fasttext_bin_to_vec(args.output_stem + '.bin', args.output_stem + '.vec')
    else:
        print(':(')

    # export_library_without_prefixes_as_file()
    # export_links_as_file()
    # train_word2vec_links()
    # train_word2vec('en', dim=20)
    # export_library_as_csv()
    #train_fasttext('he', dim=300, external_file='/home/nss/sefaria/datasets/general/all_text_he_512_lines.txt')
    # convert_fasttext_bin_to_vec("/home/nss/sefaria/datasets/text classification/fasttext_he_no_prefixes_300.bin", "/home/nss/sefaria/datasets/text classification/fasttext_he_no_prefixes_300.vec")
    # train_fasttext('', dim=100, external_file='/home/nss/sefaria/datasets/general/responsa-all.txt')
    # export_responsa_as_file()
# TODO
# compare word2vec, glove, elmo
# elmo: https://github.com/allenai/bilm-tf this seems to be updated https://github.com/ltgoslo/simple_elmo_training

# graphsage implementation and tutorial: https://towardsdatascience.com/using-graphsage-to-learn-paper-embeddings-in-cora-a94bb1e9dc9d