def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

SENTENCES = [
    [W("The"), W("safety"), W("pin"), W("was"), W("invented"), W("to"), W("pay"), W("off"), W("a"), W("$15", "fifteen dollar"), W("DEBT.")],
    [W("In"), W("1849,", "eighteen forty nine,"), W("a"), W("New"), W("York"), W("inventor"), W("named"), W("Walter"), W("Hunt"), W("owed"), W("someone"), W("FIFTEEN"), W("DOLLARS,"), W("and"), W("he"), W("needed"), W("to"), W("pay"), W("it"), W("BACK.")],
    [W("As"), W("the"), W("story"), W("goes,"), W("he"), W("picked"), W("up"), W("a"), W("piece"), W("of"), W("WIRE"), W("and"), W("started"), W("twisting"), W("it.")],
    [W("About"), W("THREE"), W("HOURS"), W("later,"), W("he"), W("had"), W("a"), W("brand"), W("new"), W("kind"), W("of"), W("pin.")],
    [W("Ordinary"), W("pins"), W("back"), W("then"), W("could"), W("JAB"), W("you.")],
    [W("A"), W("COIL"), W("at"), W("one"), W("end"), W("worked"), W("like"), W("a"), W("spring,"), W("and"), W("a"), W("CLASP"), W("covered"), W("the"), W("sharp"), W("point.")],
    [W("No"), W("more"), W("stabbed"), W("FINGERS.")],
    [W("On"), W("April"), W("10th,", "tenth,"), W("1849,", "eighteen forty nine,"), W("he"), W("received"), W("PATENT"), W("number"), W("6,281.", "sixty two eighty one.")],
    [W("Then"), W("he"), W("sold"), W("the"), W("rights"), W("for"), W("just"), W("$400.", "four hundred dollars.")],
    [W("That's"), W("more"), W("than"), W("26", "twenty six"), W("TIMES"), W("what"), W("he"), W("owed.")],
    [W("The"), W("twist?"), W("Hunt"), W("had"), W("also"), W("built"), W("one"), W("of"), W("the"), W("world's"), W("first"), W("SEWING"), W("MACHINES,"), W("and"), W("ended"), W("up"), W("in"), W("a"), W("patent"), W("FIGHT"), W("with"), W("Elias"), W("Howe.")],
    [W("But"), W("the"), W("invention"), W("we"), W("still"), W("use"), W("every"), W("day"), W("is"), W("the"), W("one"), W("he"), W("twisted"), W("up"), W("because"), W("he"), W("owed"), W("someone"), W("fifteen"), W("dollars.")],
]
