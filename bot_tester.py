import json
import re
import csv
import random
import sys
import getopt
from api_calls import translate_yandex, get_microsoft_translation,\
    get_token_translation, get_api_ai, get_luis, translate_google

verbose = False


def robustness_simple(original_an, mutants_an):
    """
    :param original_tr: Answer of original sentence. Ex: 'Quel est votre nom?'
    :param mutants_tr: Answer of mutant sentences. Ex: ['Quel est votre nom?', 'Quel est le nom de votre?',
                                                        'Quel est votre nom?', 'Quel est le nom de votre est?']
    :return: Percentage of similarity between original and mutant. Ex: 0.5
    """
    score = 0
    for m in mutants_an:
        if m == original_an:
            score += 1
    return score/len(mutants_an)


def robustness_luis(original_an, mutants_an):
    """
    :param original_tr: Answer of original utterance. Ex: (Intent, [(entity, type), (entity, type)])
    :param mutants_tr: Answer of mutant utterance. Ex: [ (Intent, [(entity, type), (entity, type)]) ]
    :return: Percentage of similarity between original and mutant. Ex: 0.5
    """
    intent_score = 0
    entity_score = len(mutants_an)
    for m in mutants_an:
        if m[0] == original_an[0]:
            intent_score += 1

        cont = True
        if len(original_an[1]) > 0:
            for tuple in m[1]:
                if tuple not in original_an[1]:
                    entity_score -= 1
                    cont = False
                    break

            if cont:
                for tuple in original_an[1]:
                    if tuple not in m[1]:
                        entity_score -= 1
                        break

    return intent_score/len(mutants_an), entity_score/len(mutants_an)


def test_robustness_luis():
    print(1)
    original_an = ("a", [(1, 2), (2, 3)])
    mutant_an = [("a", [(1, 2), (2, 3)])]
    assert ((1, 1) == robustness_luis(original_an, mutant_an)), robustness_luis(original_an, mutant_an)

    print(2)
    original_an = ("a", [(1, 2), (2, 3)])
    mutant_an = [("b", [(2, 2), (2, 4)])]
    assert ((0, 0) == robustness_luis(original_an, mutant_an)), robustness_luis(original_an, mutant_an)

    print(3)
    original_an = ("a", [(1, 2), (2, 3)])
    mutant_an = [("a", [(1, 2)]), ("b", [(1, 2), (2, 3), (4, 5)]),  ("a", [(2, 3), (1, 2)])]
    assert ((2/3, 1/3) == robustness_luis(original_an, mutant_an)), robustness_luis(original_an, mutant_an)


def robustness_apiai(original_an, mutants_an):
    """
    :param original_tr: Answer of original utterance. Ex: (Intent, ['e1', [e2], {e3}, 'e4'])
    :param mutants_tr: Answer of mutant utterance. Ex: [ (Intent, ['e1', [e2], {e3}, 'e4']) ]
    :return: Percentage of similarity between original and mutant. Ex: 0.5
    """
    intent_score = 0
    entity_score = 0
    max_entity_score = 0
    for m in mutants_an:
        max_entity_score += len(m[1])
        if m[0] == original_an[0]:
            intent_score += 1

        if len(original_an[1]) > 0:
            for entity in m[1]:
                if type(entity) == list:
                    max_entity_score += len(entity)-1
                    for e in entity:
                        if e in [i for sub in original_an[1] for i in sub]:
                            entity_score += 1
                elif type(entity) == str:
                    regex = r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
                    if re.match(regex, entity):
                        if entity[:-2] in [i[:-2] for i in original_an[1] if type(i) == str]:
                            entity_score += 1
                    else:
                        if entity in original_an[1]:
                            entity_score += 1

                else:
                    if entity in original_an[1]:
                        entity_score += 1
    return intent_score/len(mutants_an), entity_score/max_entity_score


def test_robustness_apiai():
    print(1)
    original_an = ("a", ["a", ["b", "c"]])
    mutant_an = [("a", ["a", ["b", "c"]]), ("a", ["a", ["b", "c"]])]
    assert ((1, 1) == robustness_apiai(original_an, mutant_an)), robustness_apiai(original_an, mutant_an)

    print(2)
    original_an = ("a", ["a", ["b", "c"]])
    mutant_an = [("b", ["c", ["d", "e"]])]
    assert ((0, 0) == robustness_apiai(original_an, mutant_an)), robustness_apiai(original_an, mutant_an)

    print(3)
    original_an = ("a", ["a", ["b", "c"]])
    mutant_an = [("a", ["a", ["e", "g"]]),("b", ["q", ["c", "b"]]),  ("a", ["a", ["j", "c"]])]
    assert ((2/3, 5/9) == robustness_apiai(original_an, mutant_an)), robustness_apiai(original_an, mutant_an)


def test_bot(file, bot_function, args):
    if bot_function == get_luis:
        robustness_func = robustness_luis
    elif bot_function == get_api_ai:
        robustness_func = robustness_apiai
    else:
        bot_function = robustness_simple

    global verbose
    general_intent_score = 0
    general_entity_score = 0
    nb_ex = 0
    result = []
    with open(file, 'r') as f:
        nb_ex = int(f.readline().split('\n')[0])
        for ex in range(nb_ex):
            try:
                result_ex = {}
                nb_mutants = int(f.readline().split('\n')[0])
                original = f.readline().split('\n')[0] # Utterance
                original_an = bot_function(original, args[0]) # (Intent, [(entity, type), (entity, type)])
                mutants = [] # [Mutated utterance]
                mutants_an = [] # [ (Intent, [(entity, type), (entity, type)]) ]

                #Build json
                result_ex["original"] = {}
                result_ex["original"]["requests"] = original
                result_ex["original"]["intent"] = original_an[0]
                result_ex["original"]["entities"] = original_an[1]
                result_ex["mutants"] = []

                for n in range(nb_mutants):
                    m = f.readline().split('\n')[0]
                    mutants.append(m)
                    this_answer = bot_function(m, args[0])
                    mutants_an.append(this_answer)

                    #Build json
                    this_mutant = {}
                    this_mutant["requests"] = m
                    this_mutant["intent"] = this_answer[0]
                    this_mutant["entities"] = this_answer[1]
                    result_ex["mutants"].append(this_mutant)

                intent_score, entity_score = robustness_func(original_an, mutants_an)
                result_ex["intent_robustness"] = intent_score
                result_ex["entity_robustness"] = entity_score
                result.append(result_ex)

                general_intent_score += intent_score
                general_entity_score += entity_score
                if verbose:
                    print("The robustness rate is: {}, {}".format(intent_score, entity_score))
                    print(original_an, mutants_an)
            except Exception as e:
                pass
    return result


def main(argv):
    input_file = ''
    bot = ''
    args = []
    out = 'out.txt'
    global verbose
    try:
        opts, args = getopt.getopt(argv,"hvb:i:a:o:",["bot=", "ifile=", "args=", "out="])
    except getopt.GetoptError:
        print('bot_tester.py -b <bot> -i <inputfile> -a <args> -o <outfile>[-h(elp)] [-v(erbose)]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('bot_tester.py -b <bot> -i <inputfile> -a <args>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-b", "--bot"):
            bot = arg
        elif opt in ("-a", "--args"):
            args = arg.split()
        elif opt in ("-o", "--out"):
            out = arg.split()
        elif opt == '-v':
            verbose = True

    dispatcher_bot = {'luis': get_luis,
                      'api_ai': get_api_ai,
                      'translation_micro': get_microsoft_translation,
                      'translation_goog': translate_google,
                      'translation_yand': translate_yandex}

    print("Testing bot %s on %s. Verbose=%s"%(bot,input_file,verbose))

    try:
        bot_function = dispatcher_bot[bot]
    except KeyError:
        raise ValueError('Possible strategy values: %s'%dispatcher_bot.keys())

    result = test_bot(input_file, bot_function, args)

    with open(out[0], 'w') as outfile:
        json.dump(result, outfile)


if __name__ == "__main__":
    # test_robustness_apiai()
    main(sys.argv[1:])
    # print(get_api_ai("c"))

# Results:
#
# Testing bot luis on resources/luis_meeting.txt_mut_swap. Verbose=True
# The robustness rate is: 1.0, 0.0
# ('Calendar.Add', [('nashville gym', 'Calendar.Location'), ('tomorrow morning', 'builtin.datetimeV2.datetimerange')]) [('Calendar.Add', [('anshville gym', 'Calendar.Location'), ('tomorrow morning', 'builtin.datetimeV2.datetimerange')]), ('Calendar.Add', [('nashville gym', 'Calendar.Location'), ('morning', 'builtin.datetimeV2.timerange')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Add', [('restaurant', 'Calendar.Location'), ('8pm', 'builtin.datetimeV2.time')]) [('Calendar.Add', [('restaurant', 'Calendar.Location'), ('8pm', 'builtin.datetimeV2.time')]), ('Calendar.Add', [('restaurant', 'Calendar.Location'), ('8pm', 'builtin.datetimeV2.time')]), ('Calendar.Add', [('restaurant', 'Calendar.Location'), ('8pm', 'builtin.datetimeV2.time')])]
# The robustness rate is: 1.0, 0.3333333333333333
# ('Calendar.Add', [('dunmore pa sonic sounds', 'Calendar.Location'), ('friday morning', 'builtin.datetimeV2.datetimerange')]) [('Calendar.Add', [('dunmore pa sonic sounds', 'Calendar.Location'), ('morning', 'builtin.datetimeV2.timerange')]), ('Calendar.Add', [('dunmore pa sonic sounds', 'Calendar.Location'), ('friday morning', 'builtin.datetimeV2.datetimerange')]), ('Calendar.Add', [('dunmore pa sonic sounds', 'Calendar.Location'), ('friday', 'builtin.datetimeV2.date')])]
# The robustness rate is: 1.0, 0.6666666666666666
# ('Calendar.Add', [('imax theater', 'Calendar.Subject')]) [('Calendar.Add', [('imax theater', 'Calendar.Subject')]), ('Calendar.Add', []), ('Calendar.Add', [('imax theater', 'Calendar.Subject')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Add', [('nashville gym', 'Calendar.Location')]) [('Calendar.Add', [('nashville gym', 'Calendar.Location')]), ('Calendar.Add', [('nashville gym', 'Calendar.Location')])]
# The robustness rate is: 1.0, 0.0
# ('Calendar.Add', [('meeting my manager', 'Calendar.Subject')]) [('Calendar.Add', [('meeting ym manager', 'Calendar.Subject')]), ('Calendar.Add', []), ('Calendar.Add', [])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Add', [('tomorrow', 'builtin.datetimeV2.date')]) [('Calendar.Add', [('tomorrow', 'builtin.datetimeV2.date')]), ('Calendar.Add', [('tomorrow', 'builtin.datetimeV2.date')]), ('Calendar.Add', [('tomorrow', 'builtin.datetimeV2.date')])]


# Testing bot luis on resources/luis_meeting.txt_mut_homophones. Verbose=True
# The robustness rate is: 1.0, 0.5
# ('Calendar.Add', [('finish assignment', 'Calendar.Subject')]) [('Calendar.Add', [('finish assignment', 'Calendar.Subject')]), ('Calendar.Add', [])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Add', [('imax theater', 'Calendar.Subject')]) [('Calendar.Add', [('imax theater', 'Calendar.Subject')]), ('Calendar.Add', [('imax theater', 'Calendar.Subject')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Add', [('nashville gym', 'Calendar.Location')]) [('Calendar.Add', [('nashville gym', 'Calendar.Location')]), ('Calendar.Add', [('nashville gym', 'Calendar.Location')]), ('Calendar.Add', [('nashville gym', 'Calendar.Location')])]
# The robustness rate is: 0.0, 0.6666666666666666
# ('Calendar.Add', [('one hour', 'builtin.datetimeV2.duration')]) [('Calendar.Edit', [('one hour', 'builtin.datetimeV2.duration')]), ('Calendar.Edit', [('one hour', 'builtin.datetimeV2.duration')]), ('Calendar.Edit', [])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Add', [('tomorrow', 'builtin.datetimeV2.date')]) [('Calendar.Add', [('tomorrow', 'builtin.datetimeV2.date')]), ('Calendar.Add', [('tomorrow', 'builtin.datetimeV2.date')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Add', [('27-apr', 'builtin.datetimeV2.date')]) [('Calendar.Add', [('27-apr', 'builtin.datetimeV2.date')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Find', []) [('Calendar.Find', [])]
# The robustness rate is: 1.0, 0.0
# ('Calendar.Find', [('this week', 'builtin.datetimeV2.daterange')]) [('Calendar.Find', [])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Find', [('between march 13th 2015 and today', 'builtin.datetimeV2.daterange')]) [('Calendar.Find', [('between march 13th 2015 and today', 'builtin.datetimeV2.daterange')]), ('Calendar.Find', [('between march 13th 2015 and today', 'builtin.datetimeV2.daterange')]), ('Calendar.Find', [('between march 13th 2015 and today', 'builtin.datetimeV2.daterange')])]
# The robustness rate is: 0.0, 1.0
# ('Calendar.Find', [('november 1948', 'builtin.datetimeV2.daterange')]) [('Calendar.Add', [('november 1948', 'builtin.datetimeV2.daterange')]), ('Calendar.Add', [('november 1948', 'builtin.datetimeV2.daterange')]), ('Calendar.Add', [('november 1948', 'builtin.datetimeV2.daterange')])]
# The robustness rate is: 1.0, 0.5
# ('Calendar.CheckAvailability', [('tonight', 'builtin.datetimeV2.datetimerange')]) [('Calendar.CheckAvailability', [('tonight', 'builtin.datetimeV2.datetimerange')]), ('Calendar.CheckAvailability', [('four a', 'builtin.datetimeV2.time'), ('tonight', 'builtin.datetimeV2.datetimerange')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.CheckAvailability', []) [('Calendar.CheckAvailability', [])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.CheckAvailability', [('this afternoon', 'builtin.datetimeV2.datetimerange')]) [('Calendar.CheckAvailability', [('this afternoon', 'builtin.datetimeV2.datetimerange')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.CheckAvailability', [('be with friends', 'Calendar.Subject'), ('saturday', 'builtin.datetimeV2.date')]) [('Calendar.CheckAvailability', [('be with friends', 'Calendar.Subject'), ('saturday', 'builtin.datetimeV2.date')]), ('Calendar.CheckAvailability', [('be with friends', 'Calendar.Subject'), ('saturday', 'builtin.datetimeV2.date')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Delete', [('my meeting', 'Calendar.Subject')]) [('Calendar.Delete', [('my meeting', 'Calendar.Subject')])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Delete', []) [('Calendar.Delete', [])]
# The robustness rate is: 1.0, 1.0
# ('Calendar.Delete', []) [('Calendar.Delete', [])]
# The robustness rate is: 1.0, 0.75
# ('Calendar.Edit', [('next week', 'builtin.datetimeV2.daterange')]) [('Calendar.Edit', [('next week', 'builtin.datetimeV2.daterange')]), ('Calendar.Edit', [('next week', 'builtin.datetimeV2.daterange')]), ('Calendar.Edit', [('next week', 'builtin.datetimeV2.daterange')]), ('Calendar.Edit', [])]
# The robustness rate is: 1.0, 1.0
# Traceback (most recent call last):
# ('Calendar.Edit', [('marketing meetings', 'Calendar.Subject'), ('tuesdays', 'builtin.datetimeV2.date'), ('every wednesday', 'builtin.datetimeV2.set'), ('now', 'builtin.datetimeV2.datetime')]) [('Calendar.Edit', [('marketing meetings', 'Calendar.Subject'), ('tuesdays', 'builtin.datetimeV2.date'), ('every wednesday', 'builtin.datetimeV2.set'), ('now', 'builtin.datetimeV2.datetime')]), ('Calendar.Edit', [('marketing meetings', 'Calendar.Subject'), ('tuesdays', 'builtin.datetimeV2.date'), ('every wednesday', 'builtin.datetimeV2.set'), ('now', 'builtin.datetimeV2.datetime')]), ('Calendar.Edit', [('marketing meetings', 'Calendar.Subject'), ('tuesdays', 'builtin.datetimeV2.date'), ('every wednesday', 'builtin.datetimeV2.set'), ('now', 'builtin.datetimeV2.datetime')])]
