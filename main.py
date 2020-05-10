from random import randint
import pandas as pd
import argparse
import yaml

parser = argparse.ArgumentParser()
parser.parse_args()
parser.add_argument("--min_grammar", help="The minimum number of grammar for one sentence (Default: 1)", default=2, required=False)
parser.add_argument("--max_grammar", help="The maximum number of grammar for one sentence (Default: 2)", default=4, required=False)
parser.add_argument("--min_vocab", help="The minimum number of vocabulary for one sentence (Default: 2)", default=2, required=False)
parser.add_argument("--max_vocab", help="The maximum number of vocabulary for one sentence (Default: 4)", default=4, required=False)
parser.add_argument("--max_sentences", help="The maximum number of sentence requests to generate (Default: 5)", default=5, required=False)
parser.add_argument("--max_chapter", help="The maximum Genki chapter to load (Default: 12)", default=2, required=False)
parser.add_argument("--chapter_focus", help="Focus on specific chapter before pulling from others until maximum is met (Default: None)", default=None, required=False)
parser.add_argument("--never_duplicate", help="Do not display Kanji (Default: True)", default=True, required=False)
parser.add_argument("--kana_only", help="Do not display Kanji (Default: False)", default=False, required=False)
parser.add_argument("--print_table", help="Prints character reference table for chapter lookup (Default: False)", default=True, required=False)
args = parser.parse_args()


def process_data(data_type, max_count):
    results = []
    all_chapter_types = [a[data_type] for a in genki.values()]
    key_map = {}
    counter = 1
    for item in all_chapter_types:
        key_map.update({a: counter for a in item.keys()})
        counter += 1

    if args.chapter_focus:
        used_chapters = [args.chapter_focus]
        used_values = []
        records = genki[args.chapter_focus][data_type].copy()
        while len(results) < max_count:
            if records:
                random_key = list(records.keys())[randint(0, len(records) - 1)]
                if random_key in used_values and args.never_duplicate is True:
                    continue
                results.append({**{'value': random_key}, **records[random_key], **{'chapter': args.chapter_focus}})
                used_values.append(random_key)
                records.pop(random_key, None)
            else:
                rand_list = [a for a in range(1, args.max_chapter + 1) if a not in used_chapters]
                if rand_list:
                    new_chapter = rand_list[randint(0, len(rand_list)) - 1]
                    records = genki[new_chapter]['grammar'].copy()
                    used_chapters.append(new_chapter)
                else:
                    print("Exhausted all %s options. Continuing..." % data_type.capitalize())
                    break
    else:
        while len(results) < max_count:
            random_key = list(key_map.keys())[randint(0, len(key_map.keys()) - 1)]
            results.append({**{'value': random_key}, **all_chapter_types[key_map[random_key]-1][random_key], **{'chapter': key_map[random_key]}})
            key_map.pop(random_key)

    return results, key_map


def print_sentences(sentence_requirements, grammar_map, vocab_map):
    print("""Japanese Sentence Thingy Version #something
    Create a sentence using the below grammar and vocabulary.""")
    for number, sentence_data in sentence_requirements.items():
        g = ', '.join([a['value'] for a in sentence_data['grammars']])
        temp = []
        for vocab_line in sentence_data['vocabs']:
            if vocab_line['kanji'] and not args.kana_only:
                temp.append(vocab_line['kanji'])
            else:
                temp.append(vocab_line['value'])
        v = ', '.join(temp)
        print("\nSentence:    %s" % str(number+1))
        print(" Grammar:    %s" % g)
        print(" Vocabulary: %s" % v)
    print("")

    if args.print_table:
        counter = 0
        chapter_list = []
        grammar_list = []
        kana_list = []
        kanji_list = []
        sentences_grammars_list = []
        sentences_vocabs_list = []
        for sentence_data in sentence_requirements.values():
            sentences_grammars_list.extend([a['value'] for a in sentence_data['grammars']])
            sentences_vocabs_list.extend([a['value'] for a in sentence_data['vocabs']])
        while counter < args.max_chapter:
            counter += 1
            for item, ch in grammar_map.items():
                if ch == counter and item in sentences_grammars_list:
                    grammar_list.append(item)
                    chapter_list.append(counter)
                    kana_list.append('-')
                    kanji_list.append('-')

            for item, ch in vocab_map.items():
                if ch == counter and item in sentences_vocabs_list:
                    kana_list.append(item)
                    kanji_list.append(genki[ch]['vocab'][item]['kanji'] or '-')
                    chapter_list.append(counter)
                    grammar_list.append('-')

        table_data = ({'chapter': chapter_list,
                       'grammar': grammar_list,
                       'kana': kana_list,
                       'kanji': kanji_list})
        print("Chapter Reference Table")
        table = pd.DataFrame.from_dict(table_data)
        # print(table.to_markdown())
        print(table.to_string(index=False))


if __name__ == "__main__":
    # Load Data
    with open('genki.yml', 'r') as file:
        genki = yaml.safe_load(file)

    # Check that Args are proper
    if args.min_grammar > args.max_grammar or args.min_vocab > args.max_vocab:
        exit("Minimum values can't be higher than Maximum values.")
    elif args.chapter_focus and (args.chapter_focus > args.max_chapter or args.chapter_focus < 0):
        exit("Specified chapter must be greater than 0 and less than maximum chapter.")
    elif args.max_chapter > len(genki.keys()):
        print("Data set only has %s, adjusted max_chapter to match" % len(genki.keys()))

    # Create Sentence Data
    sentence_requirements = {}
    for sentence in range(0, args.max_sentences):
        rand_grammar_count = randint(args.min_grammar, args.max_grammar)
        rand_vocab_count = randint(args.min_vocab, args.max_vocab)

        grammars, grammar_map = process_data('grammar', rand_grammar_count)
        vocabs, vocab_map = process_data('vocab', rand_vocab_count)
        sentence_requirements[sentence] = {'grammars': grammars, 'vocabs': vocabs}

    # Print Results
    print_sentences(sentence_requirements, grammar_map, vocab_map)
