def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "THIS TOY\nFAILED IN WWII?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("This toy was a failed World War") + [W("II", "Two"), W("experiment!")],
    ws("During the war, America needed a cheap rubber substitute."),
    ws("At General Electric, engineer James Wright mixed boric acid with silicone oil."),
    ws("The goo bounced even higher than rubber!"),
    ws("But the government rejected it... nobody could find a use!"),
    ws("Then a toy store sold it as a gift for adults, called Bouncing Putty."),
    ws("The store's ad man, Peter Hodgson, had Yale students pack it into plastic eggs."),
    ws("He renamed it Silly Putty, and sold each egg for one dollar."),
    ws("It flopped at a toy fair."),
    ws("Then The New Yorker mentioned it, and over") + [W("250,000", "two hundred fifty thousand")] + ws("orders poured in within three days!"),
    [W("In"), W("1968,", "nineteen sixty eight,"), W("Apollo"), W("8", "eight")] + ws("astronauts even took it to space, to hold their tools down!"),
    ws("Not bad for a blob nobody wanted, because remember..."),
]
