def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "DORITOS CAME\nFROM TRASH?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Doritos were born from Disneyland trash!"),
    ws("And the first ones didn't even have cheese."),
    ws("So how did trash turn into a billion-dollar chip?"),
    ws("As the story goes, Disneyland had a Mexican restaurant called Casa de Fritos."),
    ws("And the cooks kept throwing old tortillas in the trash."),
    ws("Then a salesman from their tortilla supplier said: stop, cut them up and fry them!"),
    ws("Guests loved them so much, the chips went on the menu."),
    ws("A Frito-Lay boss named Arch West noticed, and by") + [W("1966,", "nineteen sixty six,")] + ws("they were sold nationwide."),
    ws("But they were just plain toasted corn, until nacho cheese showed up in") + [W("1972.", "nineteen seventy two.")],
    ws("Even the name means little golden things in Spanish."),
    ws("Frito-Lay can't confirm the Disneyland part, but if it's true, your favorite chip started as..."),
]
