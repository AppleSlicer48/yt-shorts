def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "TISSUES WEREN'T\nFOR NOSES?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Tissues weren't invented for your nose!"),
    ws("And the company didn't figure out the real use. Its customers did."),
    ws("In World War One, this crinkly paper was made as a filter inside soldiers' gas masks!"),
    ws("After the war, in") + [W("1924,", "nineteen twenty four,")] + ws("it came back as Kleenex... a cold cream remover for wiping off makeup."),
    ws("Ads even said famous movie stars used it for pretty skin."),
    ws("And the name? Kleen meant clean, and the ex was borrowed from Kotex."),
    ws("But customers kept writing in, saying they used it for something totally different."),
    ws("By") + [W("1930,", "nineteen thirty,")] + ws("the letters swamped the company."),
    ws("People were using it to blow their noses!"),
    ws("So it became the handkerchief you can throw away... even though"),
]
