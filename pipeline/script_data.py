def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

# Topic: Why Pocky has a bare handle (2026-11-28)
# Sources: Glico 100th history (glico.com/global/100th_history_contents/highlight/product/006.html): 1966, "handle" so chocolate
#            does not get on the fingers, named after the sound it makes when eaten, Pocky Day 11/11 for the shape (1999), MIKADO (Glico history).
#          Nippon.com cs00045: part uncovered to hold without sticky hands, "named for the pokkin sound", 11/11 looks like the sticks.
#          The Daily Meal + Mental Floss: one end bare to prevent a mess; reportedly inspired by kushikatsu (skewered fried food).
#          Guinness 2020 'largest chocolate-coated biscuit brand' (Glico 100th history, Wikipedia 'Pocky').
#          Tasting Table: pokkin onomatopoeia for the snapping sound; Europe knows it as Mikado.
TITLE = "Why Pocky Has a Bare Handle 🍫"
HOOK_TEXT = "WHY THE\nBARE HANDLE?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Why does Pocky have a bare handle?"),
    ws("It's not to save chocolate."),
    ws("In") + [W("1966,", "nineteen sixty six,")] + ws("a Japanese company called Glico started coating thin biscuit sticks in chocolate."),
    ws("But chocolate melts on warm fingers, and nobody wants sticky hands."),
    ws("So they left one end bare, like a little handle."),
    ws("The idea was reportedly inspired by Japanese fried foods served on skewers."),
    ws("Even the name is a sound. Pocky comes from pokkin, the snap you hear when you bite one."),
    ws("In Europe, it's sold under a totally different name: Mikado."),
    ws("And in") + [W("2020,", "twenty twenty,")] + ws("Guinness World Records named it the biggest chocolate-coated biscuit brand on Earth."),
    ws("Plus, since the sticks look like ones,") + [W("11/11", "November eleventh")] + ws("is Pocky Day!"),
    ws("So next time a friend asks you..."),
]
