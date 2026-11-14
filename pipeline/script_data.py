def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "THIS TOY WAS\nFOR WARSHIPS?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("The Slinky was invented for Navy ships, not kids."),
    [W("In"), W("1943,", "nineteen forty three,")] + ws("engineer Richard James was making springs to keep ship instruments steady in rough seas."),
    ws("Then one day, he knocked a spring off a shelf."),
    ws("But instead of just falling, it WALKED."),
    ws("It flipped end over end, like it was alive."),
    ws("His wife Betty flipped through a dictionary and found the perfect name: slinky, meaning sleek and graceful."),
    [W("In"), W("1945,", "nineteen forty five,")] + ws("a Philadelphia department store let them show it off for Christmas."),
    ws("Richard set them walking down a sloped board, and all") + [W("400", "four hundred"), W("sold"), W("out"), W("in"), W("90", "ninety")] + ws("minutes, at a dollar each."),
    ws("Then it went to war: soldiers in Vietnam used Slinkys as radio antennas."),
    ws("Since then, over") + [W("250", "two hundred fifty"), W("MILLION", "million")] + ws("have been sold."),
    ws("Not bad for a toy that was never meant for kids, because..."),
]
