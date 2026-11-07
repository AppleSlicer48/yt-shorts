def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

SENTENCES = [
    [W("Nobody"), W("wanted"), W("to"), W("use"), W("the"), W("first"), W("shopping"), W("CART,"), W("so"), W("its"), W("inventor"), W("hired"), W("people"), W("to"), W("FAKE"), W("it.")],
    [W("In"), W("the"), W("1930s,", "nineteen thirties,"), W("Sylvan"), W("Goldman"), W("owned"), W("the"), W("Humpty"), W("Dumpty"), W("grocery"), W("stores"), W("in"), W("Oklahoma"), W("City.")],
    [W("He"), W("noticed"), W("shoppers"), W("STOPPED"), W("buying"), W("once"), W("their"), W("baskets"), W("got"), W("too"), W("HEAVY"), W("to"), W("carry.")],
    [W("So,"), W("with"), W("a"), W("mechanic"), W("named"), W("Fred"), W("Young,"), W("he"), W("took"), W("a"), W("FOLDING"), W("CHAIR,"), W("put"), W("WHEELS"), W("on"), W("the"), W("legs,"), W("and"), W("a"), W("BASKET"), W("on"), W("the"), W("seat.")],
    [W("On"), W("June"), W("4th,", "fourth,"), W("1937,", "nineteen thirty seven,"), W("the"), W("carts"), W("rolled"), W("OUT.")],
    [W("And"), W("NOBODY"), W("touched"), W("them.")],
    [W("The"), W("men"), W("thought"), W("pushing"), W("a"), W("cart"), W("looked"), W("UNMANLY.")],
    [W("The"), W("women"), W("said"), W("they"), W("had"), W("pushed"), W("enough"), W("BABY"), W("STROLLERS"), W("already.")],
    [W("So,"), W("Goldman"), W("hired"), W("MODELS,"), W("men"), W("and"), W("women,"), W("to"), W("stroll"), W("the"), W("aisles"), W("pushing"), W("CARTS.")],
    [W("Soon,"), W("real"), W("shoppers"), W("caught"), W("ON,"), W("and"), W("the"), W("cart"), W("made"), W("Goldman"), W("a"), W("MULTIMILLIONAIRE.")],
    [W("The"), W("twist?"), W("The"), W("carts"), W("that"), W("NEST"), W("together"), W("came"), W("from"), W("another"), W("inventor,"), W("Orla"), W("Watson,"), W("and"), W("Goldman"), W("ended"), W("up"), W("LICENSING"), W("his"), W("design.")],
    [W("All"), W("because"), W("of"), W("a"), W("cart"), W("that"), W("nobody"), W("wanted"), W("to"), W("use.")],
]
