import json

from django.db.models import Count
from django.shortcuts import render

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Utterance, Answer, Intent
from django.template import loader
from .forms import UploadUtterancesForm, CreateMutantsForm
from .helpers import add_utterances, get_accuracy, create_mutants_helper
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
            create_mutants_helper(form.cleaned_data['strategy'],
                                  form.cleaned_data['validation'],
                                  form.cleaned_data['chatbot'],
                                  form.cleaned_data['nb_per_mutant'])

            if request.POST['compute_ans']:
                # TODO compute the answers
                pass
            add_utterances(request.POST['strategy'], request.POST['intent'])


            return render(request, 'framework/create_mutants.html',
                          {'form': CreateMutantsForm()}) #HttpResponseRedirect('/framework/utterance_answers/')
    else:
        form = CreateMutantsForm()
    return render(request, 'framework/manage_utterances.html', {'form': form})


def mutants_answers(request):
    template = loader.get_template('framework/mutants_answers.html')
    context = {}
    return HttpResponse(template.render(context, request))


def results_stats(request, question_id):
    template = loader.get_template('framework/results_stats.html')
    context = {}
    return HttpResponse(template.render(context, request))


def results_detailed(request):
    template = loader.get_template('framework/results_detailed.html')
    context = {}
    return HttpResponse(template.render(context, request))


def results_utterance(request, utterance_id):
    template = loader.get_template('framework/results_utterance.html')
    context = {
        'utterance_id': utterance_id
    }
    return HttpResponse(template.render(context, request))


def index(request):
    template = loader.get_template('framework/index.html')
    context = {}
    return HttpResponse(template.render(context, request))
