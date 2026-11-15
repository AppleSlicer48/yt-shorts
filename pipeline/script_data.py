def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "A FAILED GLUE\nMADE THIS?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Post-it Notes came from a glue that FAILED."),
    [W("In"), W("1968,", "nineteen sixty eight,")] + ws("chemist Spencer Silver was trying to make a super strong glue."),
    ws("Instead, he made the exact opposite: a weak glue so gentle it peeled right off."),
    ws("For five years, he showed it off all over") + [W("3M,","three M,")] + ws("and nobody could find a use for it."),
    ws("Then his coworker Art Fry got fed up at church choir practice."),
    ws("His paper bookmarks kept falling out of his hymn book."),
    ws("So he coated them with that weak glue, and they stuck, then peeled off clean."),
    ws("And the yellow? Pure accident. The lab next door only had yellow scrap paper."),
    ws("But when") + [W("3M","three M")] + ws("tested them in four cities, sales flopped."),
    ws("So they gave free samples in Boise, Idaho, and about") + [W("90%", "ninety percent")] + ws("who tried them said they'd buy."),
    [W("In"), W("1980,", "nineteen eighty,")] + ws("they hit stores nationwide, which is wild, because..."),
]
