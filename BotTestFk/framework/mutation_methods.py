import random
import re
import copy


def swap(array, i1, i2):
    a2 = copy.deepcopy(array)
    temp = a2[i1]
    a2[i1] = a2[i2]
    a2[i2] = temp
    return a2


def mutation_swap_word(sentence):
    line_array = (re.sub('[\.,!?]', '', sentence)).lower().split()

    i1 = random.randint(0, len(line_array) - 1)

    if i1 == len(line_array) - 1:  # If last word, take previous
        i2 = i1 - 1
    else:  # Otherwise, take next
        i2 = i1 + 1

    return " ".join(swap(line_array, i1, i2))  # swap the words
