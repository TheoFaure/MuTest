from django.db import models
from framework.api_calls import get_luis


class Chatbot(models.Model):
    name = models.CharField(max_length=30)
    def __str__(self):
        return self.name


class Intent(models.Model):
    application = models.ForeignKey(Chatbot, null=True, blank=True)
    action = models.CharField(max_length=30)
    def __str__(self):
        return "{}.{}".format(self.application, self.action)


class Entity(models.Model):
    type = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    def __str__(self):
        return "{} : {}".format(self.type, self.value)


class Strategy(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.sentence

    def compute_answer(self):
        try:
            luis_json = get_luis(self.sentence)
            intent = str(luis_json['topScoringIntent']['intent'])
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

            self.answer = answer
            self.save()

            print("Answer computed", intent, answer.entity.all())
        except KeyError as e:
            print("Query not valid, no top scoring intent found")
            raise e

    def mutate(self, strategy, validation, nb):
        #TODO do the mutation using the mutation method and validation method



class Mutant(models.Model):
    sentence = models.CharField(max_length=1000)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    validation = models.ForeignKey(Validation, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, blank=True, null=True)
    utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)
    def __str__(self):
        return self.sentence
