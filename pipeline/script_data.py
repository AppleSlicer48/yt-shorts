def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "PLAY-DOH WAS\nWALLPAPER CLEANER?!"

SENTENCES = [
    [W("Play-Doh", "play dough"), W("was"), W("invented"), W("to"), W("clean"), W("WALLPAPER.", "wallpaper.")],
    [W("A"), W("Cincinnati"), W("company"), W("called"), W("KUTOL", "kutol"), W("sold"), W("it"), W("as"), W("a"), W("putty"), W("that"), W("rubbed"), W("COAL", "coal"), W("SOOT", "soot"), W("off"), W("walls.")],
    [W("But"), W("after"), W("World"), W("War"), W("Two,"), W("homes"), W("switched"), W("from"), W("coal"), W("to"), W("GAS", "gas"), W("heat.")],
    [W("No"), W("soot"), W("meant"), W("almost"), W("NO", "no"), W("customers,"), W("and"), W("sales"), W("CRASHED.", "crashed.")],
    [W("Then"), W("nursery"), W("school"), W("teacher"), W("Kay"), W("Zufall,"), W("Joe"), W("McVicker's"), W("sister-in-law,", "sister in law,"), W("tried"), W("it"), W("with"), W("her"), W("class.")],
    [W("The"), W("kids"), W("LOVED", "loved"), W("squishing"), W("and"), W("molding"), W("it,"), W("so"), W("she"), W("pushed"), W("the"), W("company"), W("to"), W("sell"), W("it"), W("as"), W("a"), W("TOY.", "toy.")],
    [W("She"), W("and"), W("her"), W("husband"), W("even"), W("came"), W("up"), W("with"), W("the"), W("name:"), W("PLAY-DOH.", "play dough.")],
    [W("In"), W("1956,", "nineteen fifty six,"), W("it"), W("hit"), W("stores"), W("in"), W("just"), W("ONE", "one"), W("color:"), W("WHITE.", "white.")],
    [W("Red,"), W("yellow"), W("and"), W("blue"), W("came"), W("the"), W("very"), W("next"), W("YEAR.", "year.")],
    [W("And"), W("in"), W("2018,", "twenty eighteen,"), W("its"), W("SMELL", "smell"), W("became"), W("an"), W("official"), W("TRADEMARK.", "trademark.")],
    [W("Sweet"), W("vanilla,"), W("a"), W("hint"), W("of"), W("CHERRY,", "cherry,"), W("and"), W("salty"), W("wheat"), W("DOUGH.", "dough.")],
    [W("Billions"), W("of"), W("cans"), W("later,"), W("almost"), W("nobody"), W("remembers"), W("that...", "that")],
]
