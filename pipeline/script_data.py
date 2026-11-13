def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "AN 11-YEAR-OLD\nINVENTED THIS?!"

SENTENCES = [
    [W("An"), W("11-year-old", "eleven year old"), W("invented"), W("the"), W("Popsicle"), W("by"), W("ACCIDENT.", "accident.")],
    [W("In"), W("1905,", "nineteen oh five,"), W("Frank"), W("Epperson"), W("stirred"), W("sugary"), W("soda"), W("powder"), W("into"), W("WATER.", "water.")],
    [W("Then"), W("he"), W("left"), W("it"), W("outside"), W("OVERNIGHT,", "overnight,"), W("with"), W("the"), W("wooden"), W("stick"), W("still"), W("in"), W("it.")],
    [W("That"), W("night,"), W("as"), W("the"), W("story"), W("goes,"), W("it"), W("dropped"), W("below"), W("FREEZING.", "freezing.")],
    [W("By"), W("morning,"), W("his"), W("drink"), W("was"), W("frozen"), W("SOLID", "solid"), W("around"), W("the"), W("stick.")],
    [W("So"), W("he"), W("pulled"), W("it"), W("out"), W("and"), W("LICKED", "licked"), W("it"), W("right"), W("off.")],
    [W("But"), W("here's"), W("the"), W("crazy"), W("part:"), W("he"), W("waited"), W("about"), W("18", "eighteen"), W("YEARS", "years"), W("to"), W("sell"), W("it.")],
    [W("In"), W("1923,", "nineteen twenty three,"), W("he"), W("sold"), W("them"), W("at"), W("an"), W("amusement"), W("park"), W("called"), W("NEPTUNE", "neptune"), W("BEACH.", "beach.")],
    [W("He"), W("named"), W("it"), W("the"), W("EPSICLE:", "epsicle:"), W("his"), W("name"), W("plus"), W("ICICLE.", "icicle.")],
    [W("But"), W("his"), W("own"), W("KIDS", "kids"), W("called"), W("it"), W("POP'S", "pop's"), W("'SICLE,", "sicle,"), W("and"), W("THAT", "that"), W("name"), W("stuck.")],
    [W("He"), W("patented"), W("it"), W("in"), W("1924,", "nineteen twenty four,"), W("but"), W("a"), W("year"), W("later"), W("he"), W("was"), W("so"), W("BROKE", "broke"), W("he"), W("sold"), W("the"), W("rights.")],
    [W("Years"), W("later"), W("he"), W("said,"), W('"I', 'I'), W("haven't"), W("been"), W("the"), W("same"), W('SINCE."', "since.")],
    [W("Now"), W("it's"), W("everywhere,"), W("and"), W("it"), W("all"), W("started"), W("because...", "because")],
]
