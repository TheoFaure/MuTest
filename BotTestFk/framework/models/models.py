from django.db import models
from framework.helpers.api_calls import get_luis
from framework.helpers.mutation_methods import mutation_homophones, mutation_swap_letter, mutation_swap_word, mutation_random, \
    mutation_verb_at_end, mutation_w2v, mutation_glove

from framework.helpers.validation_methods import is_valid_true, is_valid_spellcheck


def get_answer(sentence):
    luis_json = get_luis(sentence)

    try:
        intent = str(luis_json['topScoringIntent']['intent'])
    except KeyError as e:
        print("Query not valid, no top scoring intent found")
        raise e

    try:
        application, action = intent.split(".")
    except ValueError as e:
        action = "None"
        application = "default"

    entities = [(e['entity'], e['type']) for e in luis_json['entities']]

    try:
        chatbot = Chatbot.objects.get(name=application)
    except models.ObjectDoesNotExist as e:
        chatbot = Chatbot(name=application)
        chatbot.save()

    try:
        intent = Intent.objects.get(application=chatbot, action=action)
    except models.ObjectDoesNotExist as e:
        intent = Intent(application=chatbot, action=action)
        intent.save()

    answer = Answer(intent=intent)
    answer.save()

    for entity in entities:
        answer.entity.create(value=entity[0], type=entity[1])

    print("Answer computed", intent, answer.entity.all())
    return answer


class Chatbot(models.Model):
    name = models.CharField(max_length=30)
    def __str__(self):
        return self.name


class Intent(models.Model):
    application = models.ForeignKey(Chatbot, null=True, blank=True)
    action = models.CharField(max_length=30)
    def __str__(self):
        return "{}.{}".format(self.application, self.action)

    @property
    def robustness(self):
        robustness = 0
        utt = Utterance.objects.filter(answer__intent=self)
        print(self.__str__(), utt.count())
        if utt.count() > 0:
            for u in utt:
                robustness += u.intent_robustness
            return round(robustness / utt.count(), 2)
        else:
            return 0

    @property
    def nb_mut_ans(self):
        return Mutant.objects.filter(utterance__answer__intent=self).count()


class Entity(models.Model):
    type = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    def __str__(self):
        return "{} : {}".format(self.type, self.value)

    @property
    def robustness(self):
        robustness = 0
        utt = Utterance.objects.filter(answer__entity__type=self.type)
        if utt.count() > 0:
            for u in utt:
                robustness += u.entity_robustness
            return robustness / utt.count()
        else:
            return 0

    def is_same_entity(self, e):
        if self.type == e.type and self.value == e.value:
            return True
        else:
            return False


class Strategy(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

    @property
    def intent_robustness(self):
        robustness = 0
        utt = Utterance.objects.filter(mutant__strategy=self, mutant__answer__isnull=False).distinct()
        print(self.__str__(), utt.count())
        if utt.count() > 0:
            for u in utt:
                robustness += u.intent_robustness_for_strat(self)
            return round(robustness / utt.count(), 2)
        else:
            return 0

    @property
    def nb_mut_ans(self):
        return Mutant.objects.filter(strategy=self, answer__isnull=False).count()

    @property
    def nb_mut_without_ans(self):
        return Mutant.objects.filter(strategy=self, answer__isnull=True).count()


class Validation(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name


class Answer(models.Model):
    intent = models.ForeignKey(Intent, null=True, blank=True)
    entity = models.ManyToManyField(Entity, blank=True)
    def __str__(self):
        return "{} {}".format(self.intent.__str__(), self.entity.values_list())


class Utterance(models.Model):
    sentence = models.CharField(max_length=1000)
    expected_intent = models.ForeignKey(Intent, on_delete=models.CASCADE, default=1) # 1 is the pk for "None"
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)

    dispatcher_mutations = {"homophones": mutation_homophones,
                            "swapletter": mutation_swap_letter,
                            "swapword": mutation_swap_word,
                            "random": mutation_random,
                            "verb-end": mutation_verb_at_end,
                            "w2v": mutation_w2v,
                            "glove": mutation_glove}

    dispatcher_validations = {"none": is_valid_true,
                              "google-spell-check": is_valid_spellcheck}

    def __str__(self):
        return self.sentence

    def compute_answer(self):
        if self.answer == None:
            try:
                self.answer = get_answer(self.sentence)
                self.save()
            except KeyError as e:
                self.delete()
                pass

    def mutate(self, strategy, validation, nb):
        strategy_method = self.dispatcher_mutations[strategy.name]
        validation_method = self.dispatcher_validations[validation.name]

        existing_mutants = self.mutant_set.filter(strategy=strategy, validation=validation)

        nb_mutants_created = 0
        nb_mutants_existing = existing_mutants.count()

        if nb_mutants_existing >= nb:
            look_for_mutants = False
        else:
            look_for_mutants = True

        while look_for_mutants:
            new_mutant = strategy_method(self.sentence, existing_mutants)

            if new_mutant == "no mutant":
                look_for_mutants = False
            else:
                if validation_method(self.sentence, new_mutant):
                    m = Mutant(sentence=new_mutant, utterance=self, strategy=strategy, validation=validation)
                    m.save()
                    nb_mutants_created += 1
                    nb_mutants_existing += 1

                if nb_mutants_existing >= nb:
                    look_for_mutants = False

        return nb_mutants_created

    @property
    def intent_robustness(self):
        mutants_with_answer = self.mutant_set.filter(answer__isnull=False)
        if mutants_with_answer.count() > 0:
            r = 0
            for m in mutants_with_answer:
                if self.answer.intent == m.answer.intent:
                    r += 1
            return round(r / mutants_with_answer.count(), 2)
        else:
            return 1

    @property
    def entity_robustness(self):
        if self.mutant_set.count() > 0:
            score = 0
            for m in self.mutant_set.all():
                score += m.entity_robustness
            return round(score / self.mutant_set.count(), 2)
        else:
            return 1

    def intent_robustness_for_strat(self, strat):
        mutants_with_answer_for_strat = self.mutant_set.filter(answer__isnull=False, strategy=strat)
        if mutants_with_answer_for_strat.count() > 0:
            r = 0
            for m in mutants_with_answer_for_strat:
                if self.answer.intent == m.answer.intent:
                    r += 1
            return r / mutants_with_answer_for_strat.count()
        else:
            return 1


class Mutant(models.Model):
    sentence = models.CharField(max_length=1000)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    validation = models.ForeignKey(Validation, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, blank=True, null=True)
    utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)

    def __str__(self):
        return self.sentence

    def compute_answer(self):
        if self.answer == None:
            try:
                self.answer = get_answer(self.sentence)
                self.save()
            except KeyError as e:
                self.delete()
                pass


    @property
    def entity_robustness(self):
        score = 0
        if self.utterance.answer.entity.all().count() > 0 and self.answer != None:
            for e1 in self.utterance.answer.entity.all():
                available_entities = [e for e in self.answer.entity.all()]
                for e2 in reversed(available_entities):
                    if e1.is_same_entity(e2):
                        score += 1
                        available_entities.remove(e2)
            return round(score / self.utterance.answer.entity.all().count(), 2)
        else:
            return 1