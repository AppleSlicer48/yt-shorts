def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

# Topic: Emoji started with a heart (user-recorded voiceover for 2026-11-27)
# Sources: Emojipedia "Correcting the Record on the First Emoji Set" (SoftBank/J-Phone 90 emoji, Nov 1 1997; Apple's set derives from SoftBank's);
#          Emojipedia "Pocket Bell" (DoCoMo pager heart, popular with Japanese teens, inspired Kurita);
#          MoMA collection 196070 + Wikipedia "Shigetaka Kurita" (176 emoji, 12x12 grid, NTT DoCoMo i-mode 1999, MoMA acquired 2016; heart removal backlash);
#          Wikipedia "Emoji" (e = picture + moji = character; resemblance to "emotion" is coincidental).
TITLE = "Emoji Started Because of One Tiny Heart ❤️"
HOOK_TEXT = "EMOJI STARTED\nWITH A HEART?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Emoji took off because teens loved one tiny heart."),
    ws("And the word emoji has nothing to do with emotion."),
    ws("So what does it actually mean?"),
    ws("In the nineties, a Japanese pager let you send a little heart, and teens were obsessed."),
    ws("As the story goes, when a new model dropped it, people were so upset the company noticed."),
    ws("So in") + [W("1999,", "nineteen ninety nine,")] + ws("a designer named Shigetaka Kurita drew") + [W("176", "a hundred seventy six")] + ws("tiny pictures for phones, each just") + [W("12", "twelve"), W("by"), W("12", "twelve")] + ws("pixels."),
    ws("Today, that set is in New York's Museum of Modern Art."),
    ws("Plot twist: it wasn't even the first."),
    ws("Another Japanese phone had") + [W("90", "ninety")] + ws("emoji back in") + [W("1997,", "nineteen ninety seven,")] + ws("and that's the family your iPhone emoji came from."),
    ws("Now, the name. E means picture, moji means character."),
    ws("Emotion? Total coincidence. And it all started with one tiny heart."),
]
