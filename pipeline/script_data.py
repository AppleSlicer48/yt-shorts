def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "NUTELLA WAS\nA BRICK?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Nutella started out as a brick you had to slice!"),
    ws("And it only exists because there wasn't enough chocolate."),
    ws("So how did a brick become the spread everyone loves?"),
    ws("After World War Two, cocoa was super hard to get."),
    ws("So pastry chef Pietro Ferrero got creative."),
    ws("He used mostly hazelnuts and just a little cocoa."),
    ws("In") + [W("1946,", "nineteen forty six,")] + ws("it was a solid loaf people sliced onto bread. Yep."),
    ws("In") + [W("1951,", "nineteen fifty one,")] + ws("it became a creamy spread called Supercrema."),
    ws("In") + [W("1964,", "nineteen sixty four,")] + ws("his son Michele renamed it Nutella."),
    ws("Nut, for hazelnut, plus") + [W("ella,"), W("a"), W("sweet-sounding", "sweet sounding")] + ws("Italian ending."),
    ws("Now its maker buys about a quarter of the world's hazelnuts, all because of a brick you had to slice."),
]
