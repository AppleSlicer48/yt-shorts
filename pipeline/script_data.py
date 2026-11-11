def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

SENTENCES = [
    [W("NASA", "nasa"), W("lost"), W("a"), W("$125", "hundred twenty five"), W("MILLION", "million"), W("spacecraft"), W("to"), W("a"), W("math"), W("MISTAKE.", "mistake.")],
    [W("Its"), W("Mars"), W("Climate"), W("Orbiter"), W("flew"), W("NINE", "nine"), W("months"), W("to"), W("Mars.")],
    [W("Lockheed"), W("Martin's"), W("software"), W("measured"), W("thruster"), W("pushes"), W("in"), W("POUND-SECONDS.", "pound seconds.")],
    [W("But"), W("NASA's", "nasa's"), W("navigators"), W("read"), W("them"), W("as"), W("METRIC", "metric"), W("newton-seconds.", "newton seconds.")],
    [W("One"), W("pound-force", "pound force"), W("is"), W("4.45", "four point four five"), W("newtons,"), W("so"), W("every"), W("push"), W("was"), W("UNDERESTIMATED.", "underestimated.")],
    [W("The"), W("twist?"), W("A"), W("lopsided"), W("solar"), W("panel"), W("made"), W("them"), W("fire"), W("about"), W("TEN", "ten"), W("times"), W("more"), W("than"), W("expected.")],
    [W("Navigators"), W("saw"), W("odd"), W("data,"), W("but"), W("assumed"), W("it"), W("was"), W("a"), W("GLITCH.", "glitch.")],
    [W("In"), W("1999,", "nineteen ninety nine,"), W("it"), W("skimmed"), W("Mars"), W("at"), W("just"), W("57", "fifty seven"), W("KILOMETERS,", "kilometers,"), W("not"), W("226.", "two twenty six.")],
    [W("It"), W("likely"), W("BURNED", "burned"), W("up,"), W("and"), W("that's"), W("how...", "how")],
]
