import copy
import math
import random
import re

from framework.helpers.api_calls import syntax_text
from framework.models.homophones import Word


def swap(array, i1, i2):
    a2 = copy.deepcopy(array)
    temp = a2[i1]
    a2[i1] = a2[i2]
    a2[i2] = temp
    return a2


def is_possible_new_mutants_swap_word(sentence, existing_mutants):
    nb_words = len(sentence.split(" "))
    if existing_mutants.count() >= nb_words - 1:
        return False
    else:
        return True


def mutation_swap_word(sentence, existing_mutants):
    if not is_possible_new_mutants_swap_word(sentence, existing_mutants):
        return "no mutant"

    while True:
        line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
        line_array = line_formatted.split()
        i1 = random.randint(0, len(line_array) - 1)

        if i1 == len(line_array) - 1:  # If last word, take previous
            i2 = i1 - 1
        else:  # Otherwise, take next
            i2 = i1 + 1

        mutant = " ".join(swap(line_array, i1, i2))  # swap the words
        if mutant not in [a['sentence'] for a in existing_mutants.values('sentence')]:
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
    nb_trials = 0
    while look_for_mutants:
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
            return "no mutant"
        mutant = line_formatted[:min(index, swap_index)] + line_formatted[max(index, swap_index)] + \
                    line_formatted[min(index, swap_index)] + line_formatted[max(index, swap_index)+1:]

        if mutant not in [a['sentence'] for a in existing_mutants.values('sentence')]:
            look_for_mutants = False

        nb_trials += 1
        if nb_trials >= 4:
            return "no mutant"

    return mutant


def mutation_random(sentence, existing_mutants):
    nb_trials = 0
    look_for_mutants = True
    while look_for_mutants:
        index = random.randint(0, len(sentence) - 1)
        while re.match(r'[a-z]', sentence[index]) is None and sentence.strip():
            index = random.randint(0, len(sentence) - 1)
        letter = random.choice('abcdefghijklmnopqrstuvwxyz')
        mutant = sentence[:index] + letter + sentence[index + 1:]
        if mutant not in [a['sentence'] for a in existing_mutants.values('sentence')]:
            look_for_mutants = False
        nb_trials += 1
        if nb_trials >= 4:
            return "no mutant"

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


def mutation_homophones(sentence, existing_mutants):
    line_formatted = (re.sub('[\.,!?]', '', sentence)).lower()
    sentence_words = line_formatted.split()

    nb_existing = existing_mutants.count()
    list_homo_words = [a['word'] for a in Word.objects.values('word')]

    possibilities = []
    nb_possibilities = 0

    for word_index_in_sentence, sentence_word in enumerate(sentence_words):
        if sentence_word in list_homo_words:
            possibilities_for_this = Word.objects.get(word=sentence_word).homophone.word_set.values('word')
            array_possibilities = [a['word'] for a in possibilities_for_this if a['word'] != sentence_word]
            for possible_swap in array_possibilities:
                possibilities.append([word_index_in_sentence, sentence_word, possible_swap])

    if nb_existing >= len(possibilities):
        return "no mutant"

    # create homophone with word at index "nb_existing" in the array possibilities
    sentence_words[possibilities[nb_existing][0]] = possibilities[nb_existing][2]
    mutant = " ".join(sentence_words)

    if mutant in [a['sentence'] for a in existing_mutants.values('sentence')]:
        raise ValueError("Fail, the mutant created already exists... bug in homophones creation")

    return mutant