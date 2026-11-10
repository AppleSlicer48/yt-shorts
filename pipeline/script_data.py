def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

SENTENCES = [
    [W("A"), W("25-FOOT", "twenty five foot"), W("wave"), W("of"), W("MOLASSES"), W("swallowed"), W("a"), W("Boston"), W("street.")],
    [W("In"), W("January"), W("1919,", "nineteen nineteen,"), W("a"), W("giant"), W("tank"), W("in"), W("the"), W("North"), W("End"), W("BURST"), W("open.")],
    [W("It"), W("held"), W("2.3", "two point three"), W("MILLION"), W("gallons"), W("of"), W("thick,"), W("sticky"), W("syrup.")],
    [W("The"), W("wave"), W("raced"), W("out"), W("at"), W("about"), W("35", "thirty five"), W("miles"), W("per"), W("HOUR.")],
    [W("It"), W("knocked"), W("buildings"), W("off"), W("their"), W("foundations"), W("and"), W("bent"), W("an"), W("ELEVATED"), W("railway.")],
    [W("The"), W("twist?"), W("The"), W("tank"), W("LEAKED"), W("so"), W("badly,"), W("it"), W("was"), W("painted"), W("BROWN"), W("to"), W("hide"), W("it.")],
    [W("In"), W("the"), W("winter"), W("cold,"), W("it"), W("thickened,"), W("trapping"), W("people"), W("like"), W("GLUE.")],
    [W("21", "Twenty one"), W("people"), W("died,"), W("and"), W("about"), W("150", "a hundred fifty"), W("were"), W("hurt.")],
    [W("For"), W("decades,"), W("locals"), W("said"), W("on"), W("hot"), W("days"), W("you"), W("could"), W("still"), W("smell"), W("the"), W("day...", "day")],
]
