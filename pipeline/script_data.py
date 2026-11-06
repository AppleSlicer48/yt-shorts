def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

SENTENCES = [
    [W("Super"), W("Glue"), W("was"), W("invented"), W("by"), W("ACCIDENT."), W("TWICE.")],
    [W("In"), W("1942,", "nineteen forty two,"), W("chemist"), W("Harry"), W("Coover"), W("was"), W("trying"), W("to"), W("make"), W("clear"), W("plastic"), W("GUN"), W("SIGHTS"), W("for"), W("World"), W("War"), W("2.", "two.")],
    [W("But"), W("one"), W("chemical"), W("stuck"), W("to"), W("EVERYTHING"), W("it"), W("touched,"), W("even"), W("its"), W("own"), W("CONTAINERS.")],
    [W("So"), W("they"), W("GAVE"), W("UP"), W("on"), W("it.")],
    [W("Nine"), W("years"), W("later,"), W("his"), W("team"), W("was"), W("testing"), W("plastics"), W("for"), W("JET"), W("canopies.")],
    [W("A"), W("coworker,"), W("Fred"), W("Joyner,"), W("put"), W("that"), W("same"), W("chemical"), W("between"), W("two"), W("glass"), W("PRISMS,"), W("and"), W("they"), W("got"), W("STUCK"), W("for"), W("good.")],
    [W("This"), W("time,"), W("Coover"), W("realized"), W("it"), W("was"), W("an"), W("incredible"), W("GLUE.")],
    [W("It"), W("hardens"), W("when"), W("it"), W("touches"), W("tiny"), W("amounts"), W("of"), W("WATER,"), W("even"), W("moisture"), W("in"), W("the"), W("AIR.")],
    [W("In"), W("1958,", "nineteen fifty eight,"), W("it"), W("went"), W("on"), W("sale"), W("as"), W("Eastman"), W("910.", "nine ten.")],
    [W("Coover"), W("even"), W("went"), W("on"), W("TV"), W("and"), W("used"), W("one"), W("drop"), W("to"), W("LIFT"), W("the"), W("host"), W("off"), W("the"), W("ground.")],
    [W("Not"), W("bad"), W("for"), W("a"), W("chemical"), W("they"), W("once"), W("GAVE"), W("UP"), W("on.")],
]
