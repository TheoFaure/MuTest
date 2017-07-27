import json

from django.db.models import Count
from django.shortcuts import render

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models.models import Utterance, Answer, Intent, Mutant, Strategy
from django.template import loader
from .forms import UploadUtterancesForm, CreateMutantsForm, GetAnsMutantsForm
from .helpers.helpers import add_utterances, get_accuracy, create_mutants_helper
from django.http import HttpResponseRedirect


def manage_utterances(request):
    if request.method == 'POST':
        form = UploadUtterancesForm(request.POST)
        if form.is_valid():
            add_utterances(request.POST['utterances'], request.POST['intent'])
            return render(request, 'framework/manage_utterances.html', {'form': UploadUtterancesForm()}) #HttpResponseRedirect('/framework/utterance_answers/')
    else:
        form = UploadUtterancesForm()
    return render(request, 'framework/manage_utterances.html', {'form': form})


def utterance_answers(request):
    template = loader.get_template('framework/utterance_answers.html')
    nb_missing_answers = Utterance.objects.filter(answer_id__isnull=True).count()
    accuracies = get_accuracy()

    context = { "nb_missing_answers": nb_missing_answers,
                "accuracies": accuracies }
    return HttpResponse(template.render(context, request))


@csrf_exempt
def compute_answers(request):
    utt_without_ans = Utterance.objects.filter(answer_id__isnull=True)
    for utt in utt_without_ans:
        utt.compute_answer()

    nb_missing_answers = Utterance.objects.filter(answer_id__isnull=True).count()
    accuracies = get_accuracy()

    context = { "nb_missing_answers": nb_missing_answers,
                "accuracies": accuracies }
    j = json.dumps(context)
    return HttpResponse(j)


def create_mutants(request):
    if request.method == 'POST':
        form = CreateMutantsForm(request.POST)
        if form.is_valid():
            nb_mutants = create_mutants_helper(form.cleaned_data['strategy'],
                                               form.cleaned_data['validation'],
                                               form.cleaned_data['chatbot'],
                                               form.cleaned_data['nb_per_mutant'])

            nb_missing_answers = Mutant.objects.filter(answer_id__isnull=True).count()

            return render(request, 'framework/create_mutants.html',
                          {'form': CreateMutantsForm(),
                           'nb_mutants': nb_mutants,
                           'nb_missing_answers': nb_missing_answers}) #HttpResponseRedirect('/framework/utterance_answers/')
    else:
        form = CreateMutantsForm()
    nb_missing_answers = Mutant.objects.filter(answer_id__isnull=True).count()
    return render(request, 'framework/create_mutants.html', {'form': form,
                                                             'nb_mutants': -1,
                                                             'nb_missing_answers': nb_missing_answers})


def mutants_answers(request):
    if request.method == 'POST':
        form = GetAnsMutantsForm(request.POST)
        if form.is_valid():
            strat = form.cleaned_data['strategy']
            nb = form.cleaned_data['nb_answers']

            mutants_to_compute = Mutant.objects.filter(answer_id__isnull=True, strategy=strat)[:nb]
            for mut in mutants_to_compute:
                mut.compute_answer()

            return render(request, 'framework/mutants_answers.html',
                          {'form': GetAnsMutantsForm(),
                           'strategies': Strategy.objects.all()})
    else:
        form = GetAnsMutantsForm()
    return render(request, 'framework/mutants_answers.html', {'form': form,
                                                             'strategies': Strategy.objects.all()})


def results_stats(request):
    template = loader.get_template('framework/results_stats.html')

    intents = Intent.objects.all()
    strategies = Strategy.objects.all()

    context = {'intents': intents,
               'strategies': strategies}
    return HttpResponse(template.render(context, request))


def results_detailed(request):
    template = loader.get_template('framework/results_detailed.html')
    utt = Utterance.objects.all()
    utterances = []
    for u in utt:
        if u.intent_robustness < 1 or u.entity_robustness < 1 :
            utterances.append(u)
    context = {'utterances': utterances}
    return HttpResponse(template.render(context, request))


def results_utterance(request, utterance_id):
    template = loader.get_template('framework/results_utterance.html')

    utterance = Utterance.objects.get(id=utterance_id)
    possible_strategies = Strategy.objects.filter(mutant__utterance=utterance_id).distinct()

    context = {
        'utterance': utterance,
        'possible_strategies': possible_strategies
    }
    return HttpResponse(template.render(context, request))


def index(request):
    template = loader.get_template('framework/index.html')
    context = {}
    return HttpResponse(template.render(context, request))
