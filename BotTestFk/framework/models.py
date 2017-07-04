from django.db import models
from framework.api_calls import get_luis
from framework.mutation_methods import mutation_homophones, mutation_swap_letter, mutation_swap_word, mutation_random, \
    mutation_verb_at_end
from framework.validation_methods import is_valid_true, is_valid_spellcheck
from django.db.models import Avg


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
        if utt.count() > 0:
            for u in utt:
                robustness += u.intent_robustness
            return robustness / utt.count()
        else:
            return 0


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


class Strategy(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

    @property
    def intent_robustness(self):
        robustness = 0
        utt = Utterance.objects.filter(mutant__strategy=self)
        if utt.count() > 0:
            for u in utt:
                robustness += u.intent_robustness
            return robustness / utt.count()
        else:
            return 0


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
                            "verb-end": mutation_verb_at_end}

    dispatcher_validations = {"none": is_valid_true,
                              "google-spell-check": is_valid_spellcheck}

    def __str__(self):
        return self.sentence

    def compute_answer(self):
        if self.answer == None:
            self.answer = get_answer(self.sentence)
            self.save()

    def mutate(self, strategy, validation, nb):
        strategy_method = self.dispatcher_mutations[strategy.name]
        validation_method = self.dispatcher_validations[validation.name]

        existing_mutants = self.mutant_set.all()

        nb_mutants_created = existing_mutants.count()

        if nb_mutants_created >= nb:
            look_for_mutants = True
        else:
            look_for_mutants = False

        while look_for_mutants:
            new_mutant = strategy_method(self.sentence, existing_mutants)

            if new_mutant == "no mutant":
                look_for_mutants = False
            else:
                if validation_method(self.sentence, new_mutant):
                    m = Mutant(sentence=new_mutant, utterance=self, strategy=strategy, validation=validation)
                    m.save()
                    nb_mutants_created += 1

                if nb_mutants_created >= nb:
                    look_for_mutants = False

        return nb_mutants_created

    @property
    def intent_robustness(self):
        r = 0
        for m in self.mutant_set.all():
            if self.answer.intent == m.answer.intent:
                r += 1
        return r / self.mutant_set.count()

    @property
    def entity_robustness(self):
        # TODO fix this
        entity_score = self.mutant_set.count()
        for m in self.mutant_set.all():
            cont = True
            if self.answer.entity.count() > 0:
                for mutant_entity in m.answer.entity.all():
                    if mutant_entity not in self.answer.entity.all():
                        entity_score -= 1
                        cont = False
                        break

                if cont:
                    for mutant_entity in self.answer.entity.all():
                        if mutant_entity not in m.answer.entity.all():
                            entity_score -= 1
                            break

        return entity_score / self.mutant_set.count()


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
            self.answer = get_answer(self.sentence)
            self.save()


class Homophone(models.Model):
    def __str__(self):
        return self.word_set.all()


class Word(models.Model):
    word = models.CharField(max_length=30)
    homophone = models.ForeignKey(Homophone, on_delete=models.CASCADE)
    def __str__(self):
        return self.word
