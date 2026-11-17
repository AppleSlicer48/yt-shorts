def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "KETCHUP WAS\nMEDICINE?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Ketchup was once sold as medicine... in pill form!"),
    ws("And the first ketchup didn't even have tomatoes."),
    ws("It started as a salty fish sauce from China and Southeast Asia, called") + [W("kê-tsiap.", "kay chap.")],
    ws("Sailors carried it to Europe, where cooks made ketchup from anchovies, walnuts, and even oysters."),
    [W("In"), W("1812,", "eighteen twelve,")] + ws("a Philadelphia scientist published one of the first tomato ketchup recipes."),
    ws("But lots of Americans were still scared of tomatoes."),
    [W("Then"), W("in"), W("the"), W("1830s,", "eighteen thirties,")] + ws("an Ohio doctor claimed tomatoes could treat diarrhea and indigestion."),
    ws("Suddenly, sellers were packing tomato extract into pills."),
    ws("The twist? Many pills had no tomato at all, and some were just laxatives."),
    [W("By"), W("about"), W("1850,", "eighteen fifty,")] + ws("the craze was over, and ketchup went back to the dinner table."),
    ws("So before it landed on your fries..."),
]
