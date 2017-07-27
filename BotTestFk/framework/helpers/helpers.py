from django.db.models import Count
from framework.models.models import Utterance, Intent, Answer

#### HELPERS ####
##########################
# Some useful helpers, to make views smaller.
##########################


def add_utterances(utterances, intent_id):
    '''To add the utterances in the database.'''
    lines = utterances.split("\r\n")

    intent = Intent.objects.get(id=intent_id)

    for line in lines:
        if Utterance.objects.filter(sentence=line).count() == 0:
            utt = Utterance(sentence=line, expected_intent=intent)
            utt.save()


def get_accuracy():
    '''Computes the accuracies.
    Accuracy is the difference between the expected intent of a utterance, and the real intent computed.
    This is the only use of the expected intent. For robustness, we use the computed intent.'''
    acc_per_intent = {}
    nb_per_intent = {}

    #get numbers and init dict
    count_per_intent = Utterance.objects.filter(answer_id__isnull=False)\
        .values('expected_intent').annotate(entries=Count('expected_intent'))
    for intent in count_per_intent:
        intent_name = Intent.objects.get(pk=intent['expected_intent']).__str__()
        nb_per_intent[intent_name] = intent['entries']
        acc_per_intent[intent_name] = 0

    # fill the dict
    utterances = Utterance.objects.filter(answer_id__isnull=False).values()
    for utt in utterances:
        intent_name = Intent.objects.get(pk=utt['expected_intent_id']).__str__()
        answers_intent = Answer.objects.get(pk=utt['answer_id']).intent_id
        if utt['expected_intent_id'] == answers_intent:
            acc_per_intent[intent_name] += 1

    accuracies = []

    # divide to get accuracy
    for key in acc_per_intent.keys():
        acc_per_intent[key] /= nb_per_intent[key]
        accuracies.append([key, acc_per_intent[key]])

    return accuracies


def create_mutants_helper(strategy, validation, chatbot, nb):
    '''Link between the view that creates the mutants, and the method in the model to create them.'''
    utt_to_mutate = Utterance.objects.filter(
        expected_intent__application=chatbot
    )
    nb_mutants = 0
    for utt in utt_to_mutate:
        if utt.mutant_set.filter(strategy=strategy, validation=validation).count() < nb:
            nb_mutants += utt.mutate(strategy, validation, nb)

    return nb_mutants