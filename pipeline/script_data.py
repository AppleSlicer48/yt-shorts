def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "SOLD FOR\nJUST $1?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("This cookie recipe was sold for just") + [W("$1!", "one dollar!")],
    [W("In"), W("the"), W("1930s,", "nineteen thirties,")] + ws("Ruth Wakefield ran the Toll House Inn in Massachusetts."),
    ws("One day, she grabbed a Nestlé chocolate bar and chopped it up... with an ice pick!"),
    ws("She stirred the pea-sized chunks into her cookie dough, and the chocolate chip cookie was born."),
    ws("The cookies got so popular that Nestlé made her a deal."),
    ws("They would print her recipe right on their chocolate wrappers."),
    ws("Her payment? Reportedly one dollar... and free chocolate for life!"),
    ws("Soon, Nestlé was selling bars pre-scored for chopping, and then tiny chocolate morsels."),
    ws("And her recipe is still printed on the bag today."),
    ws("The twist? The famous story calls it a lucky accident, but historians say Ruth knew exactly what she was doing."),
    ws("So the next time you bite into a chocolate chip cookie, remember..."),
]
