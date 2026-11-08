def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

SENTENCES = [
    [W("The"), W("Frisbee"), W("is"), W("named"), W("after"), W("a"), W("PIE"), W("company,"), W("and"), W("its"), W("inventor"), W("HATED"), W("that"), W("name.")],
    [W("In"), W("1871,", "eighteen seventy one,"), W("William"), W("Frisbie"), W("opened"), W("the"), W("Frisbie"), W("PIE"), W("Company.")],
    [W("As"), W("the"), W("story"), W("goes,"), W("college"), W("students"), W("tossed"), W("its"), W("empty"), W("TINS.")],
    [W("In"), W("1937,", "nineteen thirty seven,"), W("Fred"), W("Morrison"), W("and"), W("Lucile"), W("were"), W("tossing"), W("a"), W("CAKE"), W("PAN"), W("on"), W("a"), W("beach.")],
    [W("Someone"), W("offered"), W("them"), W("25", "twenty five"), W("CENTS"), W("for"), W("it,"), W("but"), W("the"), W("pan"), W("cost"), W("a"), W("NICKEL.")],
    [W("By"), W("1948,", "nineteen forty eight,"), W("Morrison"), W("was"), W("making"), W("PLASTIC"), W("discs"), W("called"), W("Flyin-Saucers.", "flying saucers.")],
    [W("The"), W("toy"), W("company"), W("Wham-O", "wham oh"), W("bought"), W("it"), W("and"), W("renamed"), W("it"), W("FRISBEE.")],
    [W("Morrison"), W("called"), W("the"), W("name"), W("a"), W("HORROR,"), W("until"), W("royalties"), W("made"), W("him"), W("RICH.")],
    [W("The"), W("twist?"), W("Ed"), W("Headrick,"), W("who"), W("designed"), W("the"), W("MODERN"), W("Frisbee,"), W("went"), W("even"), W("further.")],
    [W("When"), W("he"), W("died"), W("in"), W("2002,", "two thousand two,"), W("his"), W("ASHES"), W("were"), W("molded"), W("into"), W("DISCS.")],
    [W("Some"), W("were"), W("sold"), W("to"), W("fund"), W("a"), W("MUSEUM,"), W("so"), W("he's"), W("STILL"), W("flying.")],
    [W("All"), W("thanks"), W("to"), W("a"), W("toy"), W("named"), W("after"), W("a"), W("pie"), W("company.")],
]
