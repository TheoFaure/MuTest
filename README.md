# MuTest
MuTest is a research project that aims to find better ways to test chatbots.

# BotTestFk
BotTestFk is a framework written in Django that allows to manage the data and see the results to test the robustness of a chatbot system (Natural Language Understanding). We use the Microsoft API Luis.ai, but any other framework that can compute the intent and the entities of a query can be used.

## Features
The application contains the following features:
- Manage the utterances (queries)
- Create adversarial examples via different generation techniques
- Compute the answers (with Luis.ai) to each of the original queries and the adversarial examples
- See and explore the results, that show the robustness of the application

## Dependencies
To use this application, you need:
- Pyhton3
- Django 1.9
- Postgre SQL
