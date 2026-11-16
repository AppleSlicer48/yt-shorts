def W(s, spoken=None):
    return (s, spoken if spoken is not None else s)

HOOK_TEXT = "A DOG\nINVENTED THIS?!"

def ws(text):
    return [W(x) for x in text.split()]

SENTENCES = [
    ws("Velcro was invented because of a dog."),
    [W("In"), W("1941,", "nineteen forty one,")] + ws("Swiss engineer George de Mestral took his dog on a hunting trip in the Alps."),
    ws("When they got home, his pants and his dog's fur were covered in sticky burrs."),
    ws("Most people would just pull them off, but he put one under a microscope."),
    ws("It was covered in thousands of tiny hooks, grabbing every little loop of fabric and fur."),
    ws("So he set out to copy a weed with cloth."),
    ws("Cotton wore out way too fast, so he switched to nylon, and it took nearly ten years."),
    ws("He named it Velcro, from the French words for velvet and hook."),
    ws("But at first, almost nobody cared about it."),
    ws("Then NASA used it on Apollo missions to stop things floating away, and suddenly everyone wanted it."),
    ws("That's why so many people think NASA invented it. But nope, the truth is..."),
]
