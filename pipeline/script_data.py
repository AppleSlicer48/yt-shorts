def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "INVENTED BY AN\nACCOUNTANT?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Bubble gum was invented by an accountant!"),
    ws("And its pink color has an even weirder story."),
    [W("In"), W("1928,", "nineteen twenty eight,")] + ws("Walter Diemer kept the books at a Philadelphia gum company."),
    ws("Their first bubble gum, Blibber-Blubber, was so sticky it got shelved."),
    ws("So the accountant started mixing his own recipes."),
    ws("After a year, one batch worked... then hardened overnight!"),
    ws("Four months later, he finally cracked it."),
    ws("A candy store sold all") + [W("100", "one hundred")] + ws("pieces, a penny each, in one day!"),
    ws("They called it Dubble Bubble, and he taught salesmen to blow bubbles!"),
    ws("And the pink? It was the only food coloring in the factory!"),
    ws("That's why bubble gum is still pink... thanks to an accountant."),
]
