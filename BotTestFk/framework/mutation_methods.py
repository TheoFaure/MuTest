import random
import re
import copy
import csv
from framework.api_calls import syntax_text


def swap(array, i1, i2):
    a2 = copy.deepcopy(array)
    temp = a2[i1]
    a2[i1] = a2[i2]
    a2[i2] = temp
    return a2


def mutation_swap_word(sentence, validation_method, nb):
    mutants = []
    for i in range(nb):
        line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
        line_array = line_formatted.split()
        i1 = random.randint(0, len(line_array) - 1)

        if i1 == len(line_array) - 1:  # If last word, take previous
            i2 = i1 - 1
        else:  # Otherwise, take next
            i2 = i1 + 1

        mutant = " ".join(swap(line_array, i1, i2))  # swap the words

        if validation_method(line_formatted, mutant) and mutant not in mutants:
            mutants.append(mutant)
    return mutants


def position_of_verb(sentence):
    tokens = syntax_text(sentence)
    for i, token in enumerate(tokens):
        if token.part_of_speech == "VERB":
            return i
    return -1


def mutation_verb_at_end(sentence, validation_method, nb):
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
    line_array = line_formatted.split()

    pos_verb = position_of_verb(line_formatted)  # Begin mutation

    if pos_verb >= 0 and pos_verb < len(line_array):
        line_array.append(line_array[pos_verb])
        line_array[pos_verb] = ""
        mutant = " ".join(line_array).replace("  ", " ").strip()
    if validation_method(line_formatted, mutant):
        return [mutant]
    else:
        return []


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


def mutation_swap_letter(sentence, validation_method, nb):
    mutants = []
    for i in range(nb):
        line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
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
            raise ValueError("Error is swapping a letter...")
        mutant = line_formatted[:min(index, swap_index)] + line_formatted[max(index, swap_index)] + \
                    line_formatted[min(index, swap_index)] + line_formatted[max(index, swap_index)+1:]
        if validation_method(line_formatted, mutant) and mutant not in mutants:
            mutants.append(mutant)
    return mutants


def mutation_random(sentence, validation_method, nb):
    mutants = []
    for i in range(nb):
        index = random.randint(0, len(sentence) - 1)
        while re.match(r'[a-z]', sentence[index]) is None and sentence.strip():
            index = random.randint(0, len(sentence) - 1)
        letter = random.choice('abcdefghijklmnopqrstuvwxyz')
        mutant = sentence[:index] + letter + sentence[index + 1:]
        if validation_method(sentence, mutant) and mutant not in mutants:
            mutants.append(mutant)
    return mutants


def nth_repl(s, sub, repl, nth):
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


def mutation_homophones(sentence, validation_method, nb):
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
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
                                if validation_method(line_formatted, mut):
                                    mutants.append(mut)
    return mutants