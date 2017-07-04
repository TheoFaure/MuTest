import random
import re
import copy
import csv
import math
from BotTestFk import settings
from framework.api_calls import syntax_text
import os


def swap(array, i1, i2):
    a2 = copy.deepcopy(array)
    temp = a2[i1]
    a2[i1] = a2[i2]
    a2[i2] = temp
    return a2


def is_possible_new_mutants_swap_word(sentence, existing_mutants):
    nb_words = len(sentence.split(" "))
    if math.factorial(nb_words) >= existing_mutants.count():
        return False
    else:
        return True


def mutation_swap_word(sentence, existing_mutants):
    look_for_mutant = True
    mutant = "no mutant"
    while look_for_mutant:
        line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
        line_array = line_formatted.split()
        i1 = random.randint(0, len(line_array) - 1)

        if i1 == len(line_array) - 1:  # If last word, take previous
            i2 = i1 - 1
        else:  # Otherwise, take next
            i2 = i1 + 1

        mutant = " ".join(swap(line_array, i1, i2))  # swap the words
        if mutant not in existing_mutants.values('sentence'):
            look_for_mutant = False

        if not is_possible_new_mutants_swap_word(sentence, existing_mutants):
            look_for_mutant = False
            mutant = "no mutant"

    return mutant


def position_of_verb(sentence, index):
    tokens = syntax_text(sentence)
    verb_positions = []
    for i, token in enumerate(tokens):
        if token.part_of_speech == "VERB":
            verb_positions.append(i)

    try:
        return verb_positions[index]
    except IndexError as e:
        return -1


def mutation_verb_at_end(sentence, existing_mutants):
    index_verb = existing_mutants.count()
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
    line_array = line_formatted.split()
    pos_verb = position_of_verb(line_formatted, index_verb)  # Begin mutation

    if pos_verb >= 0 and pos_verb < len(line_array):
        line_array.append(line_array[pos_verb])
        line_array[pos_verb] = ""
        mutant = " ".join(line_array).replace("  ", " ").strip()
        return mutant
    else:
        return "no mutant" # No more verbs, so we cannot create a mutant


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


def mutation_swap_letter(sentence, existing_mutants):
    look_for_mutants = True
    while look_for_mutants:
        #TODO look for mutants not fininshed
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
            raise ValueError("Error in swapping a letter...")
        mutant = line_formatted[:min(index, swap_index)] + line_formatted[max(index, swap_index)] + \
                    line_formatted[min(index, swap_index)] + line_formatted[max(index, swap_index)+1:]
    return mutant


def mutation_random(sentence):
    index = random.randint(0, len(sentence) - 1)
    while re.match(r'[a-z]', sentence[index]) is None and sentence.strip():
        index = random.randint(0, len(sentence) - 1)
    letter = random.choice('abcdefghijklmnopqrstuvwxyz')
    mutant = sentence[:index] + letter + sentence[index + 1:]
    return mutant


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


def mutation_homophones(sentence):
    # TODO make it work
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
    words = line_formatted.split()
    homoreader = csv.reader(homophones, delimiter=',', quotechar='|')
    for homo in homoreader:
        homo_found = {}
        for w in words:
            for h in homo:
                if h == w:
                    if h in homo_found: # deal with homophones that appear many times in 1 sentence
                        homo_found[h] += 1
                    else:
                        homo_found[h] = 1
                    for h2 in homo:
                        if h2 != h:
                            mut = nth_repl(line_formatted, w, h2, homo_found[h])
    return mutants


def mutation_homophones(sentence):
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
    words = line_formatted.split()
    with open(os.path.join(settings.BASE_DIR, 'framework/static/framework/homophones.txt'), 'r') as homophones:
        homoreader = csv.reader(homophones, delimiter=',', quotechar='|')
        for homo in homoreader:
            homo_found = {}
            for w in words:
                for h in homo:
                    if h == w:
                        if h in homo_found: # deal with homophones that appear many times in 1 sentence
                            homo_found[h] += 1
                        else:
                            homo_found[h] = 1
                        for h2 in homo:
                            if h2 != h:
                                mut = nth_repl(line_formatted, w, h2, homo_found[h])
#                                         mut = line_formatted.replace(w, h2, 1)
                                if validation_method(line_formatted, mut):
                                    mutants.append(mut)
    return mutants