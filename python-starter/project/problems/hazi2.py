from project.problem import Problem
import sys


class DetProblem(Problem):

    def initialize_parser(self, parser):
        """
        Hozzáadjuk a determinizálásért felelős parancssori kapcsolót.
        Mivel a --det egy 'flag' (nincs utána érték, csak önmagában áll),
        az action='store_true' beállítást használjuk.
        """
        parser.add_argument('--det', action='store_true', help='Determinizálja az NFA automatát')

    def is_chosen_problem(self, args):
        """
        Akkor vagyunk kiválasztva, ha a parancssorban ott a --det flag.
        (A keretrendszer minden Problem osztály esetén meghívja ezt).
        """
        # A hasattr biztosítja, hogy ne adjon hibát, ha valamiért az args-ban nincs det
        return hasattr(args, 'det') and args.det

    def run(self, args):
        """
        Itt fut le maga a feladat logikája.
        """
        # 1. Beolvasás és alapvető hibakezelés
        nfa_data = self.load_and_validate_nfa(args.input)

        # Ha hiba volt a beolvasáskor (pl. érvénytelen szimbólum), kilépünk
        if not nfa_data:
            return

        states, alphabet, start_state, accept_states, transitions = nfa_data

        # 2. Determinizálás algoritmus (Subset construction)
        dfa_states, dfa_accept_states, dfa_transitions = self.determinize(
            alphabet, start_state, accept_states, transitions
        )

        # 3. Kimenet kiírása a megadott formátumban
        self.save_dfa(args.output, alphabet, dfa_states, dfa_accept_states, dfa_transitions)

    def load_and_validate_nfa(self, filepath):
        """Beolvassa az NFA-t és leellenőrzi az inkonzisztenciákat."""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]

        if len(lines) < 4:
            print("Hiba: A bemeneti fájl túl rövid.", file=sys.stderr)
            return None

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2]

        # Lehet, hogy nincs végállapot, ezt is kezeljük
        accept_states = set(lines[3].split() if lines[3] else [])

        valid_states = set(states)
        valid_alphabet = set(alphabet)

        # --- ALAPVETŐ HIBAKEZELÉS ---
        if start_state not in valid_states:
            print(f"Hiba: A kezdőállapot ({start_state}) nem szerepel az állapotok között.", file=sys.stderr)
            return None

        for acc in accept_states:
            if acc not in valid_states:
                print(f"Hiba: A végállapot ({acc}) nem szerepel az állapotok között.", file=sys.stderr)
                return None

        # NFA esetén egy állapotból egy betű hatására TÖBB helyre is mehetünk!
        # Ezért az érték egy halmaz (set) lesz.
        transitions = {}
        for s in valid_states:
            for a in valid_alphabet:
                transitions[(s, a)] = set()

        # Átmenetek beolvasása az 5. sortól
        for line in lines[4:]:
            if not line:
                continue
            parts = line.split()
            if len(parts) == 3:
                src, symbol, dest = parts

                # Ellenőrizzük, hogy érvényesek-e az adatok
                if src not in valid_states:
                    print(f"Hiba: Ismeretlen forrás állapot a szabályban: {src}", file=sys.stderr)
                    return None
                if dest not in valid_states:
                    print(f"Hiba: Ismeretlen cél állapot a szabályban: {dest}", file=sys.stderr)
                    return None
                if symbol not in valid_alphabet:
                    print(f"Hiba: Ismeretlen szimbólum a szabályban: {symbol}", file=sys.stderr)
                    return None

                transitions[(src, symbol)].add(dest)

        return states, alphabet, start_state, accept_states, transitions

    def determinize(self, alphabet, start_state, accept_states, transitions):
        """Az NFA átalakítása DFA-vá a halmazkonstrukció (subset construction) algoritmussal."""

        # Kezdetben csak a start állapotot tartalmazó halmazból indulunk
        # Frozenset-et (megváltoztathatatlan halmazt) használunk, mert dictionary kulcs lesz belőle.
        start_subset = frozenset([start_state])

        # Ebbe a listába gyűjtjük azokat a halmazokat, amiknek a kimeneteit még meg kell vizsgálni
        unprocessed = [start_subset]

        # Leképezés: Részhalmaz -> Új DFA állapot (pl. {q1, q2} -> 's1')
        state_map = {start_subset: 's0'}

        # DFA átmeneteinek listája
        dfa_transitions = []
        state_counter = 1

        while unprocessed:
            current_subset = unprocessed.pop(0)
            current_s_name = state_map[current_subset]

            # Minden lehetséges betűre megvizsgáljuk, hova jutunk
            for symbol in alphabet:
                next_subset = set()

                # A részhalmaz minden egyes eleméből megnézzük a célállapotokat
                for q in current_subset:
                    next_subset.update(transitions.get((q, symbol), set()))

                # Ha nem üres halmazba jutottunk (tehát van átmenet)
                if next_subset:
                    next_subset_frozen = frozenset(next_subset)

                    # Ha ez egy teljesen új állapot, amit még nem láttunk
                    if next_subset_frozen not in state_map:
                        state_map[next_subset_frozen] = f"s{state_counter}"
                        state_counter += 1
                        unprocessed.append(next_subset_frozen)

                    # Átmenet regisztrálása
                    dfa_transitions.append((current_s_name, symbol, state_map[next_subset_frozen]))

        # Összeszedjük a létrehozott új DFA állapotokat számozás szerinti sorrendben
        # Így biztosítjuk, hogy a kimeneten s0 s1 s2 s3 ... s10 legyen a sorrend
        sorted_subsets = sorted(state_map.keys(), key=lambda subset: int(state_map[subset][1:]))

        dfa_states = []
        dfa_accept_states = []

        for subset in sorted_subsets:
            s_name = state_map[subset]
            dfa_states.append(s_name)

            # Egy DFA állapot (halmaz) akkor elfogadó, ha TARTALMAZ legalább egy eredeti NFA elfogadó állapotot
            if subset.intersection(accept_states):
                dfa_accept_states.append(s_name)

        # A feladat kéri, hogy az átmeneteket ÁBÉCÉ SORRENDBEN írjuk ki:
        # Előbb forrás, aztán szimbólum, aztán cél.
        # A tuple-ök (a, b, c) rendezése Pythonban alapból pontosan ezt a lexikografikus rendezést csinálja.
        dfa_transitions.sort(key=lambda t: (t[0], t[1], t[2]))

        return dfa_states, dfa_accept_states, dfa_transitions

    def save_dfa(self, filepath, alphabet, states, accept_states, transitions):
        """A DFA kiírása a megadott kimeneti formátumba."""
        with open(filepath, 'w', encoding='utf-8') as f:
            # 1. sor: Állapotok
            f.write(" ".join(states) + "\n")
            # 2. sor: Ábécé (megegyezik a bemenetivel)
            f.write(" ".join(alphabet) + "\n")
            # 3. sor: Kezdőállapot (mindig s0 a fenti logika alapján)
            f.write(states[0] + "\n")
            # 4. sor: Elfogadó állapotok
            f.write(" ".join(accept_states) + "\n")

            # 5. sortól: Átmenetek
            for src, symbol, dest in transitions:
                f.write(f"{src} {symbol} {dest}\n")