from django.db.models import Count

from .models import Utterance, Intent, Answer, Strategy


def add_utterances(utterances, intent_id):
    lines = utterances.split("\r\n")

    intent = Intent.objects.get(id=intent_id)

    for line in lines:
        utt = Utterance(sentence=line, expected_intent=intent)
        utt.save()


def get_accuracy():
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
    utt_to_mutate = Utterance.objects.filter(
        expected_intent__application=chatbot
    ).exclude(
        mutant__strategy=strategy,
        mutant__validation=validation
    )
    for utt in utt_to_mutate:
        utt.mutate(strategy, validation, nb)