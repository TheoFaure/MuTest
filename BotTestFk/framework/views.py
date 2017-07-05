import json

from django.db.models import Count
from django.shortcuts import render

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models.models import Utterance, Answer, Intent, Mutant, Strategy
from django.template import loader
from .forms import UploadUtterancesForm, CreateMutantsForm
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


@csrf_exempt
def mutants_answers(request):
    mut_without_ans = Mutant.objects.filter(answer_id__isnull=True)
    for mut in mut_without_ans:
        mut.compute_answer()

    nb_missing_answers = Mutant.objects.filter(answer_id__isnull=True).count()

    context = {"nb_missing_answers": nb_missing_answers}
    j = json.dumps(context)
    return HttpResponse(j)


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
