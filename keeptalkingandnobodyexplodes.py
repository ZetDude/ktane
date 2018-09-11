import sys
import datetime
import pathfinder
import easygui

# Whether to log every action you take
LOG = True


##### V   LONG CONSTS   V
KEYPAD_HELP = """Abstractions of keypad buttons:
lo | loop; swirl
so | soft sign; yat
p  | paragraph
sh | shock; lightning
co | copyright
cy | cyrillic; iotified big yus
ks | ksi; reverse ksi with caron
rc | reverse c with dot
c  | c with dot
i  | i kratkoye with tail
tr | triangle; small yus
s  | white star
e  | e with diaresis
zh | zhe with tail
q  | upside-down question mark
t  | face with tongue sticking out; teh with ring
h  | h with swirl
l  | lambda
lp | lollipop
b  | b
pz | puzzle
r  | droopy capital r; capital komi dzje
ps | psi
ae | aesc
o  | capital omega
w  | cyrillic omega with titlo
bs | black star"""

COMPLICATED_KEYPAD_HELP = """Abstractions of complicated keypad buttons:
e  | epsilon
ho | hook
ha | half of.. a shape
p  | pi
m  | mu
bd | capital delta
o  | omega
g  | capital gamma
x  | capital xi
up | opening up with dot
z  | zeta
le | opening left
ph | phi
th | theta
ck | cyrillic k
a  | alpha
ps | psi
b  | beta
n  | eta, looks like n
d  | delta
s  | sigma
"""

# 1 - cut, 0 - no cut, 2 - serial even, 3 - parallel, 4 - 2 or more batteries
COMPLICATED_WIRES_DIAGRAM = {"x": 1, "r": 2, "b": 2, "br": 2, "rs": 1, "brs": 3, "blrs": 0,
                             "blr": 2, "lr": 4, "s": 1, "bl": 3, "bls": 3, "ls": 4, "lrs": 4,
                             "bs": 0, "l": 0}

##### ^   LONG CONSTS   ^

##### V   UTIL CONSTS   V

MODULES = {}

class MalformedInput(Exception):
    pass

class UnfinishedAction(Exception):
    pass

class GameOver(Exception):
    pass

class GameState:
    def __init__(self):
        self.strike = 0
        self.battery = 0
        self.ind = {}
        self.lit = {}
        self.memory = {}
        self.play = "unstarted"
        self.code = ""
        self.odd = False
        self.even = False
        self.vowel = False

def log(msg):
    if LOG:
        print(f"LOG {datetime.datetime.utcnow()}: {msg}")

def parse_wire_module(wires, state):
    """Parses the wires and outputs the index of the wire to cut.

    Arguments:
    wires (list of string): A list of the colors of the wires on the module.
    state (GameState object): Current game state.

    Outputs:
    int of the index of the wire to cut (1-indexed)

    Throws:
    MalformedInput if the amount of wires isn't 3-6

    Example:
    parse_wire_module(["yellow", "yellow", "black"], game_state) -> 2

    Reference:
    Page 5, On the Subject of Wires
    """

    def last_occurence(value, iterable):
        return max(loc for loc, val in enumerate(iterable) if val == value) + 1

    if len(wires) == 3:  # 3 wires:
        if "red" not in wires:  # If there are no red wires,
            return 2            # cut the second wire.
        elif wires[-1] == "white":  # Otherwise, if the last wire is white,
            return 3                # cut the last wire.
        elif wires.count("blue") > 1:             # Otherwise, if there is more than one blue wire,
            return last_occurence("blue", wires)  # cut the last blue wire.
        else:         # Otherwise,
            return 3  # cut the last wire.
    elif len(wires) == 4:  # 4 wires:
        if wires.count("red") > 1 and state.odd:  # If there is more than one red wire and the last
                                                  # digit of the serial number is odd, 
            return last_occurence("red", wires)   # cut the last red wire.
        elif wires[-1] == "yellow" and "red" not in wires: # Otherwise, if the last wire is yellow
                                                           # and there are no red wires,
            return 1                                       # cut the first wire.
        elif wires.count("blue") == 1:  # Otherwise, if there is exactly one blue wire,
            return 1                    # cut the first wire.
        elif wires.count("yellow") > 1:  # Otherwise, if there is more than one yellow wire,
            return 4                     # cut the last wire.
        else:         # Otherwise,
            return 2  # cut the second wire.
    elif len(wires) == 5:  # 5 wires:
        if wires[-1] == "black" and state.odd:  # If the last wire is black and the last digit of
                                                # the serial number is odd,
            return 4                            # cut the fourth wire.
        elif (wires.count("red") == 1 and  # Otherwise, if there is exactly one red wire and
              wires.count("yellow") > 1):  # there is more than one yellow wire,
            return 1                       # cut the first wire.
        elif "black" not in wires:  # Otherwise, if there are no black wires,
            return 2                # cut the second wire.
        else:         # Otherwise,
            return 1  # cut the first wire.
    elif len(wires) == 6:  # 6 wires:
        if "yellow" not in wires and state.odd:  # If there are no yellow wires and the last digit
                                                 # of the serial number is odd,
            return 3                             # cut the third wire.
        elif (wires.count("yellow") == 1 and  # Otherwise, if there is exactly one yellow wire and
              wires.count("white") > 1):      # there is more than one white wire,
            return 4                          # cut the fourth wire.
        elif "red" not in wires:  # Otherwise, if there are no red wires,
            return 6              # cut the last wire.
        else:         # Otherwise,
            return 4  # cut the fourth wire.
    else:
        raise MalformedInput(
            "Simple Wires module can only contain 3-6 wires, got {} instead".format(
                len(wires)))

def parse_button_module_initial(color, text, state):
    """Parses the button module based on the information available on the first overlook.

    Arguments:
    color (str): The color of the button.
    text (str): The text on the button.
    state (GameState object): Current game state.

    Outputs:
    bool, True if button must be tapped, False if button must be held.
    In the case of a False output, data must be passed on to parse_button_module_final().

    Throws:

    Example:
    parse_button_module_initial("red", "hold", game_state) -> True

    Reference:
    Page 6, On the Subject of The Button
    """

    if color == "blue" and text == "abort":  # 1. If the button is blue and the button says "Abort",
        return False                         # hold the button.
    elif state.battery > 1 and text == "detonate":  # 2. If there is more than 1 battery on the bomb
                                                    # and the button says "Detonate",
        return True                                 # press and immediately release the button.
    elif color == "white" and state.lit.get("CAR"):  # 3. If the button is white and there is a lit
                                                     # indicator with label CAR,
        return False                                 # hold the button.
    elif state.battery > 2 and state.lit.get("FRK"):  # 4. If there are more than 2 batteries on the
                                                      # bomb and a lit indicator with label FRK
        return True                                   # press and immediately release the button.
    elif color == "yellow":  # 5. If the button is yellow,
        return False         # hold the button.
    elif color == "red" and text == "hold":  # 6. If the button is red and the button says "Hold",
        return True                          # press and immediately release the button.
    else:             # 7. If none of the above apply,
        return False  # hold the button.

def parse_button_module_final(color, state):


    if color == "blue":
        return 4
    elif color == "white":
        return 1
    elif color == "yellow":
        return 5
    else:
        return 1

def parse_keypad_module(options, state):


    columns = [["lp", "tr", "l",  "sh", "cy", "h",  "rc"],
               ["e",  "lp", "rc", "lo", "s",  "h",  "q"],
               ["co", "w",  "lo", "zh", "r",  "l",  "s"],
               ["b",  "p",  "so", "cy", "zh", "q",  "t"],
               ["ps", "t",  "so", "c",  "p",  "ks", "bs"],
               ["b",  "e",  "pz", "ae", "ps", "i",  "o"]]

    for i in columns:
        for j in options:
            if j not in i:
                break
        else:
            correct = i
            break

    order = []

    for i in correct:
        for j in options:
            if i == j:
                order.append(str(options.index(j)+1))

    return order

def parse_simon_says_module(sequence, state):


    vowel = {0: {"red": "blue",
                 "blue": "red",
                 "green": "yellow",
                 "yellow": "green"},
             1: {"red": "yellow",
                 "blue": "green",
                 "green": "blue",
                 "yellow": "red"},
             2: {"red": "green",
                 "blue": "red",
                 "green": "yellow",
                 "yellow": "blue"}}

    no_vowel = {0: {"red": "blue",
                    "blue": "yellow",
                    "green": "green",
                    "yellow": "red"},
                1: {"red": "red",
                    "blue": "blue",
                    "green": "yellow",
                    "yellow": "green"},
                2: {"red": "yellow",
                    "blue": "green",
                    "green": "blue",
                    "yellow": "red"}}

    replaced = []
    if state.vowel:
        for i in sequence:
            replaced.append(vowel[state.strike][i])
    else:
        for i in sequence:
            replaced.append(no_vowel[state.strike][i])

    return replaced

def parse_memory_module(stage, label, options, memory, state):

    stages = [
        {1: options[1],
         2: options[1],
         3: options[2],
         4: options[3]},
        {1: 4,
         2: options[memory.get(1, [0,0])[1]-1],
         3: options[0],
         4: options[memory.get(1, [0,0])[1]-1]},
        {1: memory.get(2, [0,0])[0],
         2: memory.get(1, [0,0])[0],
         3: options[2],
         4: 4},
        {1: options[memory.get(1, [0,0])[1]-1],
         2: options[0],
         3: options[memory.get(2, [0,0])[1]-1],
         4: options[memory.get(2, [0,0])[1]-1]},
        {1: memory.get(1, [0,0])[0],
         2: memory.get(2, [0,0])[0],
         3: memory.get(4, [0,0])[0],
         4: memory.get(3, [0,0])[0]}]

    print(stage)
    print(state.memory)
    target_label = stages[stage-1][label]
    target_pos = options.index(target_label)+1

    memory[stage] = (target_label, target_pos)
    if stage == 5:
        memory = {}

    return (target_label, target_pos, memory)
         
def parse_won_module(label, options, state):

    read = {"yes": 2, "first": 1, "display": 5, "okay": 1, "says": 5, "nothing": 2, "-": 4,
            "blank": 3, "no": 5, "led": 2, "lead": 5, "read": 3, "red": 3, "reed": 4, "leed": 4,
            "holdon": 5, "you": 3, "youare": 5, "your": 3, "you're": 3, "ur": 0, "there": 5,
            "they're": 4, "their": 3, "theyare": 2, "see": 5, "c": 1, "cee": 5}

    choose = {'ready': ['yes', 'okay', 'what', 'middle', 'left', 'press', 'right', 'blank', 'ready', 'no', 'first', 'uhhh', 'nothing', 'wait'],
              'first': ['left', 'okay', 'yes', 'middle', 'no', 'right', 'nothing', 'uhhh', 'wait', 'ready', 'blank', 'what', 'press', 'first'],
              'no': ['blank', 'uhhh', 'wait', 'first', 'what', 'ready', 'right', 'yes', 'nothing', 'left', 'press', 'okay', 'no', 'middle'],
              'blank': ['wait', 'right', 'okay', 'middle', 'blank', 'press', 'ready', 'nothing', 'no', 'what', 'left', 'uhhh', 'yes', 'first'],
              'nothing': ['uhhh', 'right', 'okay', 'middle', 'yes', 'blank', 'no', 'press', 'left', 'what', 'wait', 'first', 'nothing', 'ready'],
              'yes': ['okay', 'right', 'uhhh', 'middle', 'first', 'what', 'press', 'ready', 'nothing', 'yes', 'left', 'blank', 'no', 'wait'],
              'what': ['uhhh', 'what', 'left', 'nothing', 'ready', 'blank', 'middle', 'no', 'okay', 'first', 'wait', 'yes', 'press', 'right'],
              'uhhh': ['ready', 'nothing', 'left', 'what', 'okay', 'yes', 'right', 'no', 'press', 'blank', 'uhhh', 'middle', 'wait', 'first'],
              'left': ['right', 'left', 'first', 'no', 'middle', 'yes', 'blank', 'what', 'uhhh', 'wait', 'press', 'ready', 'okay', 'nothing'],
              'right': ['yes', 'nothing', 'ready', 'press', 'no', 'wait', 'what', 'right', 'middle', 'left', 'uhhh', 'blank', 'okay', 'first'],
              'middle': ['blank', 'ready', 'okay', 'what', 'nothing', 'press', 'no', 'wait', 'left', 'middle', 'right', 'first', 'uhhh', 'yes'],
              'okay': ['middle', 'no', 'first', 'yes', 'uhhh', 'nothing', 'wait', 'okay', 'left', 'ready', 'blank', 'press', 'what', 'right'],
              'wait': ['uhhh', 'no', 'blank', 'okay', 'yes', 'left', 'first', 'press', 'what', 'wait', 'nothing', 'ready', 'right', 'middle'],
              'press': ['right', 'middle', 'yes', 'ready', 'press', 'okay', 'nothing', 'uhhh', 'blank', 'left', 'first', 'what', 'no', 'wait'],
              'you': ['sure', 'youare', 'your', "you're", 'next', 'uhhuh', 'ur', 'hold', 'what?', 'you', 'uhuh', 'like', 'done', 'u'],
              'youare': ['your', 'next', 'like', 'uhhuh', 'what?', 'done', 'uhuh', 'hold', 'you', 'u', "you're", 'sure', 'ur', 'youare'],
              'your': ['uhuh', 'youare', 'uhhuh', 'your', 'next', 'ur', 'sure', 'u', "you're", 'you', 'what?', 'hold', 'like', 'done'],
              "you're": ['you', "you're", 'ur', 'next', 'uhuh', 'youare', 'u', 'your', 'what?', 'uhhuh', 'sure', 'done', 'like', 'hold'],
              'ur': ['done', 'u', 'ur', 'uhhuh', 'what?', 'sure', 'your', 'hold', "you're", 'like', 'next', 'uhuh', 'youare', 'you'],
              'u': ['uhhuh', 'sure', 'next', 'what?', "you're", 'ur', 'uhuh', 'done', 'u', 'you', 'like', 'hold', 'youare', 'your'],
              'uhhuh': ['uhhuh', 'your', 'youare', 'you', 'done', 'hold', 'uhuh', 'next', 'sure', 'like', "you're", 'ur', 'u', 'what?'],
              'uhuh': ['ur', 'u', 'youare', "you're", 'next', 'uhuh', 'done', 'you', 'uhhuh', 'like', 'your', 'sure', 'hold', 'what?'],
              'what?': ['you', 'hold', "you're", 'your', 'u', 'done', 'uhuh', 'like', 'youare', 'uhhuh', 'ur', 'next', 'what?', 'sure'],
              'done': ['sure', 'uhhuh', 'next', 'what?', 'your', 'ur', "you're", 'hold', 'like', 'you', 'u', 'youare', 'uhuh', 'done'],
              'next': ['what?', 'uhhuh', 'uhuh', 'your', 'hold', 'sure', 'next', 'like', 'done', 'youare', 'ur', "you're", 'u', 'you'],
              'hold': ['youare', 'u', 'done', 'uhuh', 'you', 'ur', 'sure', 'what?', "you're", 'next', 'hold', 'uhhuh', 'your', 'like'],
              'sure': ['youare', 'done', 'like', "you're", 'you', 'hold', 'uhhuh', 'ur', 'sure', 'u', 'what?', 'next', 'your', 'uhuh'],
              'like': ["you're", 'next', 'u', 'ur', 'hold', 'done', 'uhuh', 'what?', 'uhhuh', 'you', 'like', 'sure', 'youare', 'your']}

    order = choose[options[read[label]]]
    correct = []
    for i in order:
        for j in options:
            if i == j:
                return j

def parse_comp_wires_module(wires, state):

    solved = []
    for i in wires:
        i = ''.join(sorted(i))
        solution = COMPLICATED_WIRES_DIAGRAM[i]
        if solution == 2:
            solution = state.even
        elif solution == 3:
            solution = state.ind.get("PARALLEL", False)
        elif solution == 4:
            solution = (state.battery > 1)
        else:
            solution = bool(solution)
        solved.append(solution)

    return solved

def parse_modded_complex_keypad_initial(state):

    if state.battery > 2 and state.ind.get("PARALLEL", False):
        return 2
    elif state.ind.get("DVI-D", False) and state.lit.get("BOB", False):
        return True
    return False

def parse_modded_complex_keypad_module(options, reverse, state):
    
    columns = [["a", "e", "th", "ps", "m", "x", "z", "s", "b", "bd"],
               ["p", "a", "z", "o", "d", "g", "n", "ho", "ma", "ck"],
               ["ph", "ck", "o", "g", "th", "b", "e", "p", "ha", "bd"],
               ["ha", "ho", "ph", "e", "m", "o", "a", "s", "ck", "up"],
               ["g", "o", "m", "d", "up", "le", "x", "a", "n", "b"]]

    for i in columns:
        for j in options:
            if j not in i:
                break
        else:
            correct = i
            break

    order = []

    for i in correct:
        for j in options:
            if i == j:
                order.append(str(options.index(j)+1))

    if reverse:
        order = reversed(order)
    return order

def parse_modded_caesar_cipher_module(letters, state):

    converted = ""
    letters = letters.upper()
    
    offset = 0
    offset -= 1 * state.vowel
    offset += state.battery
    offset += 1 * state.even
    offset += 1 * state.ind.get("CAR", False)
    if state.ind.get("PARALLEL") and state.lit.get("NSA"):
        offset = 0

    for letter in letters:
        letter = ord(letter) + offset
        letter = letter + 26 if letter < 65 else letter
        letter = letter - 26 if letter > 90 else letter
        letter = chr(letter)
        converted += letter

    return converted
    

def run_gui_mode():
    playing = True
    while playing:
        state = GameState()
        bat_hold = easygui.enterbox(msg=('Amount of batteries and holders, '
                                         'seperated by a space'), title='Setup')
        if not bat_hold:
            state.battery = 0
            state.holder = 0
        else:
            state.battery, state.holder = bat_hold.split()
        log("SETUP Batteries: " + str(state.battery))
        log("SETUP Holders: " + str(state.holder))

        valid_lit = ("FRK", "CAR", "BOB", "NSA")
        valid_ind = valid_lit + ("", "PARALLEL", "DVI-D")
        indicators = easygui.multchoicebox(msg='Indicators', title='Setup',
                                           choices=valid_ind, preselect=len(valid_lit))
        if not indicators:
            indicators = {}
            state.ind = indicators
        indicators = [i for i in indicators if i != ""]
        for i in indicators:
            state.ind[i] = True
        log("SETUP Indicators: " + " ".join(state.ind.keys()))

        can_be_lit = list(set(valid_lit).intersection(indicators))
        can_be_lit = [""] + can_be_lit
        if len(can_be_lit) == 1:
            state.lit = {}
        else:
            lit = easygui.multchoicebox(msg='Which of these are lit?', title='Setup',
                                        choices=can_be_lit, preselect=0)
            if not lit:
                state.lit = {}
            else:
                for i in lit:
                    if i == "":
                        continue
                    state.lit[i] = True
        
        serial_code = easygui.enterbox(msg="Serial Number", title='Setup')
        if not serial_code:
            serial_code = "a0"
        state.code = serial_code.upper()
        log("SETUP Serial Number: " + state.code)
        state.odd = bool(int(state.code[-1]) % 2 == 1)
        state.even = not state.odd
        for i in "AEIOU":
            if i in state.code:
                state.vowel = True
                break
        else:
            state.vowel = False
        state.play = "waiting"
        state.memory = {}
        lastchoice = 0
        info = ""

        defusing = True
        while defusing:
            try:
                aboutbomb = (f"Status: {state.play}\n"
                             f"Indicators:"
                             f"{', '.join(state.ind.keys()) if state.ind else 'none significant'}\n"
                             f"Lit indicators:"
                             f"{', '.join(state.lit.keys()) if state.lit else 'none significant'}\n"
                             f"Batteries: {state.battery}\nSerial#: {state.code} "
                             f"({'odd' if state.odd else 'even'}, "
                             f"{'vowel' if state.vowel else 'no vowel'})")

                title = "X" * state.strike
                if state.play == "waiting":
                    choices = ["[defused]",
                               "---= VANILLA MODULES =---",
                               "Wires", "Button", "Keypad",
                               "Simon Says", "Memory", "Maze",
                               "Who's on First", "Complicated Wires",
                               "---= MODDED MODULES =---",
                               "Complex Keypad", "Caesar Cipher"]
                    message = (f"<<< {info}\n{aboutbomb}\n"
                               "Choose a module to defuse")
                choices = ["[x]", "[time ran out]"] + choices
                choice = easygui.choicebox(msg=message, title=title, choices=choices,
                                           preselect = lastchoice)
                lastchoice = choices.index(choice)
                log("Chose: " + choice)
                if choice == "[x]":
                    state.strike += 1
                    log("Got strike number " + str(state.strike))
                    if state.strike == 3:
                        defusing = False
                        log("Game over. Blew up due to 3 strikes")
                        easygui.msgbox(msg="Not my fault", title="Game over")
                elif choice == "[time ran out]":
                    defusing = False
                    log("Game over. Blew up due to no time remaining")
                    easygui.msgbox(msg=(f"I thought you were supposed to be faster...\n"
                                        f"{state.strike} strike(s)!"), title="Game over")
                elif choice == "[defused]":
                    defusing = False
                    log("Game over. Bomb was defused")
                    easygui.msgbox(msg=f"Good job!\n{state.strike} strike(s)!", title="Game over")

                if state.play == "waiting":
                    if choice == "Wires":
                        log("Wires Module")
                        wires = easygui.enterbox(msg="Order of wires", title="Simple Wires Module")
                        log("Wires >>> " + wires)
                        wires = wires.split()
                        result = parse_wire_module(wires, state)
                        log("Wires <<< " + str(result))
                        ordinals = {1: "first", 2: "second", 3: "third",
                                    4: "fourth", 5: "fifth", 6: "sixth"}
                        info = f"Cut the {ordinals[result]} wire! ({wires[result-1]})\n"
                        
                    elif choice == "Button":
                        log("Button Module")
                        args = easygui.enterbox(msg="Button description",
                                                title="Button Module Initial")
                        log("Button (Initial) >>>: " + args)
                        args = args.split()
                        result = parse_button_module_initial(*args, state)
                        log(f"Button (Initial) <<<: {result} (True if tap)")
                        if result:
                            info = "Press and release!"
                        else:
                            followup = easygui.enterbox(msg="Hold and report color!",
                                                        title="Button Module Final")
                            log("Button (Final) >>>: " + followup)
                            result = parse_button_module_final(followup, state)
                            log("Button (Final) <<<: Release on " + str(result))
                            info = f"Release on {result}"
                    elif choice == "Keypad":
                        buttons = easygui.enterbox(msg="Keypad choices", title="Keypad Module")
                        log("Keypad >>>: " + buttons)
                        if buttons == "?":
                            easygui.codebox(title="Keypad Help", text=KEYPAD_HELP)
                        else:
                            buttons = buttons.split()
                            result = parse_keypad_module(buttons, state)
                            log("Keypad <<<: " + ', '.join(result))
                            info = f"Order: {', '.join(result)}"
                    elif choice == "Simon Says":
                        args = easygui.enterbox(msg=("Enter flashing color.\n"
                                                     "'!' is substituted with the last sequence"),
                                                title="Simon Says Module")
                        log("Simon Says >>>: " + args)
                        args = args.split()
                        
                        if args[0] == "!":
                            log("Simon Says Memory (!): " + " ".join(state.memory.get("simon", [])))
                            args = state.memory.get("simon", []) + args[1:]

                        result = parse_simon_says_module(args, state)
                        log("Simon Says <<<: " + ', '.join(result))

                        info = f"New order: {', '.join(result)}\n"
                        state.memory["simon"] = args
                    elif choice == "Memory":

                        memory = state.memory.get("memory", {})
                        stage = state.memory.get("memory stage", 1)
                        log("Memory Memory (Stage): " + str(stage))
                        log("Memory Memory (Memory): " + str(memory))

                        args = easygui.enterbox(msg=(f"Memory stage {stage}\n"
                                                     "Enter label and options, "
                                                     "seperated by spaces.\nEnter 'r' to reset"),
                                                title="Memory Module")
                        log("Memory >>>: " + args)
                        if args == "r":
                            log("Memory Reset!")
                            state.memory["memory"] = {}
                            state.memory["memory stage"] = 1
                        else:
                            args = args.split()
                            args = [int(x) for x in args]
                            label = args[0]
                            args = args[1:]

                            lab, pos, mem = parse_memory_module(stage, label, args, memory, state)
                            log(f"Memory <<<: position {pos} label {lab}")
                            log("Memory new Memory <<<: " + str(mem))

                            if stage == 5:
                                log("Memory Reset!")
                                state.memory["memory stage"] = 1
                            else:
                                log("Memory new Stage <<<: " + str(stage + 1))
                                state.memory["memory stage"] = stage + 1
                            state.memory["memory"] = mem

                            info = f"Press the button in position {pos} (label {lab})"
                    elif choice == "Maze":
                        args = easygui.enterbox(msg=("Enter a circle location, start location and "
                                                     "end location, seperated by spaces."),
                                                title="Maze Module")
                        log("Maze >>>: " + args)
                        args = args.split()
                        argsint = [int(x) for x in args]
                        circle = " ".join(args[0:2])
                        start = argsint[2:4]
                        end = argsint[4:6]
                        matrix_circles = { # TODO: Constant
                            "1 2": 0, "6 3": 0,
                            "2 4": 1, "5 2": 1,
                            "4 4": 2, "6 4": 2,
                            "1 1": 3, "1 4": 3,
                            "5 3": 4, "4 6": 4,
                            "5 1": 5, "3 5": 5,
                            "2 1": 6, "2 6": 6,
                            "4 1": 7, "3 4": 7,
                            "3 2": 8, "1 5": 8}

                        matrix_id = matrix_circles.get(circle, None)
                        if matrix_id is None:
                            raise MalformedInput(f"Maze circle {circle} is unknown")
                        log("Maze Matrix ID >>>: " + str(matrix_id))

                        result, maze = pathfinder.get_path(matrix_id, start, end)
                        log(f"Maze <<<: {result}\n{maze}")
                        info = f"Maze:\n{maze}\nPath: {result}"
                    elif choice == "Who's on First":
                        args = easygui.enterbox(msg="Enter label and options, seperated by spaces.",
                                                title="Who's on First Module")
                        log(f"Who's on First >>>: " + args)
                        args = args.split()
                        label = args[0]
                        args = args[1:]

                        result = parse_won_module(label, args, state)
                        log(f"Who's on First <<<: " + result)
                        info = f"Answer: {result}"
                                                
                    elif choice == "Complicated Wires":
                        args = easygui.enterbox(msg=("Enter wires seperated by spaces.\n"
                                                     "R = Red wire, B = Blue wire, S = Star, "
                                                     "L = LED; X for nothing"),
                                                title="Complicated Wires Module")
                        log("Complicated Wires >>>: " + args)
                        args = args.split()
                        result = parse_comp_wires_module(args, state)
                        log("Complicated Wires <<<: " + str(result))
                        result = [str(i+1) for i, j in enumerate(result) if j]
                        info = f"Cut: {' '.join(result)}"

                    elif choice == "Complex Keypad":
                        order = parse_modded_complex_keypad_initial(state)
                        log((f"Complex Keypad (Initial) <<<: {order} "
                             "(2 if disregard, True if reverse"))
                        if order == 2:
                            easygui.msgbox(msg=(f"Press the keypad in order, "
                                                "left to right, up to down."),
                                           title="Complicated Keypad Module")
                        else:
                            buttons = easygui.enterbox(msg="Keypad choices",
                                                       title="Complicated Keypad Module")
                            log("Complex Keypad >>>: " + buttons)
                            if buttons == "?":
                                easygui.codebox(title="Complicated Keypad Help",
                                                text=COMPLICATED_KEYPAD_HELP)
                            else:
                                buttons = buttons.split()
                                result = parse_modded_complex_keypad_module(
                                    buttons, order, state)
                                log("Complex Keypad <<<: " + ', '.join(result))
                                info = f"Order: {', '.join(result)}"
                    elif choice == "Caesar Cipher":
                        text = easygui.enterbox(msg="Enter original message",
                                                title="Caesar Cipher Module")
                        text = text.upper()
                        result = parse_modded_caesar_cipher_module(text, state)
                        info = f"Next text: {result}"
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                easygui.exceptionbox(msg=aboutbomb)

run_gui_mode()
