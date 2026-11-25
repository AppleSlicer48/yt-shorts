def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "CROCS WERE\nBOAT SHOES?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Crocs were invented as boat shoes!"),
    ws("And a mom got ten million dollars just for filling the holes."),
    ws("So how did a boat clog end up on everyone's feet?"),
    ws("Three friends from Colorado found a foam clog made by a Canadian company."),
    ws("It floated, it didn't slip, and the holes let air in and water out."),
    ws("In") + [W("2002,", "two thousand two,")] + ws("they brought") + [W("200", "two hundred")] + ws("pairs to a Florida boat show, and every pair sold out."),
    ws("Then a mom named Sheri started sticking charms in her kids' Crocs."),
    ws("She turned it into a basement business called Jibbitz."),
    ws("And in") + [W("2006,", "two thousand six,")] + ws("Crocs bought it for ten million dollars. Seriously."),
    ws("Time magazine even called Crocs one of the") + [W("50", "fifty")] + ws("worst inventions."),
    ws("But the holes made for boats became the fun part, and it all started because..."),
]
