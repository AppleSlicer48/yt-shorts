def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

SENTENCES = [
    [W("This"), W("window"), W("SHAPE"), W("ripped"), W("the"), W("first"), W("jet"), W("airliner"), W("APART.")],
    [W("In"), W("1952,", "nineteen fifty two,"), W("the"), W("de"), W("Havilland"), W("COMET"), W("started"), W("flying"), W("passengers.")],
    [W("In"), W("1954,", "nineteen fifty four,"), W("one"), W("broke"), W("apart"), W("near"), W("Elba,"), W("killing"), W("all"), W("35", "thirty five"), W("aboard.")],
    [W("Months"), W("later,"), W("ANOTHER"), W("fell"), W("into"), W("the"), W("sea"), W("with"), W("21", "twenty one"), W("people.")],
    [W("Comets"), W("were"), W("GROUNDED,"), W("and"), W("engineers"), W("sank"), W("a"), W("whole"), W("fuselage"), W("in"), W("a"), W("WATER"), W("TANK.")],
    [W("They"), W("pressurized"), W("it"), W("again"), W("and"), W("again,"), W("like"), W("THOUSANDS"), W("of"), W("flights.")],
    [W("Then"), W("it"), W("SPLIT"), W("open,"), W("right"), W("at"), W("a"), W("window"), W("CORNER.")],
    [W("Corners"), W("concentrate"), W("STRESS,"), W("far"), W("more"), W("than"), W("the"), W("designers"), W("expected.")],
    [W("Now"), W("every"), W("airliner"), W("window"), W("has"), W("ROUNDED"), W("corners,"), W("because...", "because")],
]
