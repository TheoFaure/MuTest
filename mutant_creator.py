import re
import csv
import random
import sys
import getopt
from api_calls import spellcheck_google, spellcheck_microsoft, syntax_text
import json
import copy


def file_len(fname):
    """
    Computes the length of the file fname.
    """
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def nth_repl(s, sub, repl, nth):
    """
    Replace the nth occurrence of substring sub by repl on the string s.
    """
    find = s.find(sub)
    # if find is not p1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != nth:
        # find + 1 means we start at the last match start index + 1
        find = s.find(sub, find + 1)
        i += 1
    # if i  is equal to nth we found nth matches so replace
    if i == nth:
        return s[:find]+repl+s[find + len(sub):]
    return s


def validate_true(s1, s2):
    return True


def create_mutant_homophones(file, va_strat=validate_true):
    """
    Creates a file with homonym-based mutants of the sentences in the file given.
    """
    len_file = file_len(file)
    with open(file, 'r') as f, open('{}_mut_homophones_{}'.format(file, va_strat.__name__), 'w') as f2:
        f2.write("{}\n".format(len_file))
        for line in f:
            line_formatted = (re.sub('[\.,!?]', '', line)).lower()
            words = line_formatted.split()
            mutants = []
            with open('resources/homophones.txt', 'r') as homophones:
                homoreader = csv.reader(homophones, delimiter=',', quotechar='|')
                for homo in homoreader:
                    homo_founded = {}
                    for w in words:
                        for h in homo:
                            if h == w:
                                if h in homo_founded: # deal with homophones that appear many times in 1 sentence
                                    homo_founded[h] += 1
                                else:
                                    homo_founded[h] = 1
                                print(w, h)
                                for h2 in homo:
                                    if h2 != h:
                                        mut = nth_repl(line_formatted, w, h2, homo_founded[h])
#                                         mut = line_formatted.replace(w, h2, 1)
                                        if va_strat(line_formatted, mut):
                                            mutants.append(mut)
            if len(mutants) > 0:
                f2.write("{}\n".format(len(mutants)))
                f2.write(line_formatted)
                for m in mutants:
                    f2.write(m)
    print("finnish")


def create_mutant_random(file, va_strat=validate_true, nb_mutants=3):
    len_file = file_len(file)
    with open(file, 'r') as f, open('{}_mut_randomchange_{}'.format(file, va_strat.__name__), 'w') as f2:
        f2.write("{}\n".format(len_file))
        for line in f:
            mutants = []
            for i in range(nb_mutants):
                index = random.randint(0, len(line) - 1)
                while re.match(r'[a-z]', line[index]) is None and line.strip():
                    index = random.randint(0, len(line) - 1)
                letter = random.choice('abcdefghijklmnopqrstuvwxyz')
                line_mut1 = line[:index] + letter + line[index + 1:]

                if va_strat(line, line_mut1): # Validate the mutant
                    mutants.append(line_mut1)

            if len(mutants) > 0:
                f2.write("{}\n".format(nb_mutants))
                f2.write(line)
                for m in mutants:
                    f2.write(m)

    print("finnish")


def valid_swap_index(line, index):
    isletter = re.match(r'[a-zA-Z]', line[index]) is not None
    try:
        previousisletter = re.match(r'[a-zA-Z]', line[index - 1]) is not None
    except Exception as e:
        previousisletter = False

    try:
        nextisletter = re.match(r'[a-zA-Z]', line[index + 1]) is not None
    except Exception as e:
        nextisletter = False

    return isletter, previousisletter, nextisletter


def create_mutant_swap(file, va_strat=validate_true, nb_mutants=5):
    len_file = file_len(file)
    with open(file, 'r') as f, open('{}_mut_swapletter_{}'.format(file, va_strat.__name__), 'w') as f2:
        f2.write("{}\n".format(len_file))
        for line in f:
            line_formatted = (re.sub('[\.,!?]', '', line)).lower()
            mutants = []
            for i in range(nb_mutants):
                valid_index = False
                index = 0
                while not valid_index and line_formatted.strip():
                    index = random.randint(0, len(line_formatted) - 1)
                    isletter, previousisletter, nextisletter = valid_swap_index(line_formatted, index)
                    valid_index = (isletter and (previousisletter or nextisletter))

                isletter, previousisletter, nextisletter = valid_swap_index(line_formatted, index)
                if nextisletter:
                    swap_index = index+1
                elif previousisletter:
                    swap_index = index-1
                else:
                    print("Wrrrroooooong!")
                line_mut1 = line_formatted[:min(index, swap_index)] + line_formatted[max(index, swap_index)] + \
                            line_formatted[min(index, swap_index)] + line_formatted[max(index, swap_index)+1:]

                if va_strat(line_formatted, line_mut1): # Validate the mutant
                    mutants.append(line_mut1)

            if len(mutants) > 0:
                f2.write("{}\n".format(len(mutants)))
                f2.write(line_formatted)
                for m in mutants:
                    f2.write(m)

    print("finnish")


def swap(array, i1, i2):
    a2 = copy.deepcopy(array)
    temp = a2[i1]
    a2[i1] = a2[i2]
    a2[i2] = temp
    return a2


def position_of_verb(sentence):
    tokens = syntax_text(sentence)
    for i, token in enumerate(tokens):
        if token.part_of_speech == "VERB":
            return i
    return -1


def create_mutant_verb_at_end(file, va_strat=validate_true):
    len_file = file_len(file)
    with open(file, 'r') as f, open('{}_mut_posverb_{}'.format(file, va_strat.__name__), 'w') as f2:
        f2.write("{}\n".format(len_file))
        for line in f:
            line_formatted = (re.sub('[\.,!?]', '', line)).lower()
            line_array = line_formatted.split()

            pos_verb = position_of_verb(line_formatted) # Begin mutation
            if pos_verb >= 0 and pos_verb < len(line_array):
                line_array.append(line_array[pos_verb])
                line_array[pos_verb] = ""
                line_mut = " ".join(line_array).replace("  ", " ").strip()

                if va_strat(line_formatted, line_mut): # Validate the mutant
                    f2.write("1\n")
                    f2.write(line_formatted)
                    f2.write("{}\n".format(line_mut))

    print("finnish")


def create_mutant_swap_words(file, va_strat=validate_true, nb_mutants=3):
    len_file = file_len(file)
    with open(file, 'r') as f, open('{}_mut_swapword_{}'.format(file, va_strat.__name__), 'w') as f2:
        f2.write("{}\n".format(len_file))
        for line in f:
            line_formatted = (re.sub('[\.,!?]', '', line)).lower()
            line_array = line_formatted.split()
            mutants = []
            for i in range(nb_mutants): # Create mutants for each line
                i1 = random.randint(0, len(line_array) - 1)

                if i1 == len(line_array) - 1: # If last word, take previous
                    i2 = i1 - 1
                else: # Otherwise, take next
                    i2 = i1 + 1

                line_mut = " ".join(swap(line_array, i1, i2)) # swap the words
                if va_strat(line_formatted, line_mut) and line_mut not in mutants: # Validate the mutant
                    mutants.append(line_mut)

            if len(mutants) > 0:
                f2.write("{}\n".format(len(mutants)))
                f2.write(line_formatted)
                for m in mutants:
                    f2.write("{}\n".format(m))

    print("finnish")


def main(argv):
    input_file = ''
    mut_strat = ''
    va_strat = ''
    try:
        opts, args = getopt.getopt(argv,"hs:v:i:",["mustrat=","vastrat=", "ifile="])
    except getopt.GetoptError:
        print('mutant_creator.py -s <mutationStrategy> -v <validationStrategy> -i <inputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('mutant_creator.py -s <mutationStrategy> -v <validationStrategy> -i <inputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-s", "--mustrat"):
            mut_strat = arg
        elif opt in ("-v", "--vastrat"):
            va_strat = arg

    dispatcher_mutations = {'random': create_mutant_random,
                            'homophones': create_mutant_homophones,
                            'swap_letter': create_mutant_swap,
                            'swap_word' : create_mutant_swap_words,
                            'verb_end': create_mutant_verb_at_end}

    dispatcher_validations = {'spellcheck_google': spellcheck_google,
                              'spellcheck_microsoft': spellcheck_microsoft,
                              'none': validate_true}

    try:
        mutation_function = dispatcher_mutations[mut_strat]
    except KeyError:
        raise ValueError('Possible strategy values: %s'%dispatcher_mutations.keys())

    try:
        validation_function = dispatcher_validations[va_strat]
    except KeyError:
        raise ValueError('Possible validation values: %s'%dispatcher_validations.keys())

    mutation_function(input_file, validation_function)


if __name__ == "__main__":
    main(sys.argv[1:])
    # syntax_text("how high is the eiffel tower?")