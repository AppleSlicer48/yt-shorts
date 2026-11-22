def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "FIRST BAND-AID:\n18 INCHES?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("One wife's kitchen accidents gave us the Band-Aid!"),
    ws("And the first ones were so weird, almost nobody bought them."),
    ws("In") + [W("1920,", "nineteen twenty,")] + ws("Earle Dickson's wife Josephine kept nicking her fingers while cooking."),
    ws("Earle bought cotton for Johnson and Johnson, and he had an idea."),
    ws("He stuck little gauze pads along sticky tape, so she could snip one off."),
    ws("His bosses weren't impressed... until he showed it on himself."),
    ws("But the first ones were handmade strips,") + [W("18", "eighteen")] + ws("inches long!"),
    ws("The first year, they sold just") + [W("$3,000", "three thousand dollars")] + ws("worth."),
    ws("So they gave free ones to Boy Scouts, and machines made them smaller."),
    ws("Earle became vice president, and over") + [W("100", "a hundred")] + ws("billion have been made, all because..."),
]
