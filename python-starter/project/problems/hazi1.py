from project.problem import Problem


class DFAProblem(Problem):

    def initialize_parser(self, parser):
        """
        Itt adjuk hozzá a feladatspecifikus parancssori argumentumokat.
        A --input és --output már hozzá van adva a __main__.py-ban,
        így nekünk csak a --check kapcsolót kell definiálnunk.
        """
        parser.add_argument('--check', help='Ellenőrizendő szavak vesszővel elválasztva (DFA)')

    def is_chosen_problem(self, args):
        """
        Ez a metódus dönti el, hogy ez a feladat lett-e meghívva.
        Ha a parancssorban szerepel a --check argumentum, akkor
        visszatérünk True-val, ami jelzi a Main-nek, hogy ezt a feladatot kell futtatni.
        """
        return args.check is not None

    def run(self, args):
        """
        Ez a fő függvény, ami akkor fut le, ha az is_chosen_problem True-t adott vissza.
        Az args tartalmazza a bemeneti fájlt (args.input), a kimeneti fájlt (args.output),
        és a szavakat (args.check).
        """
        # 1. Beolvasás és DFA felépítése
        start_state, accept_states, transitions = self.load_dfa(args.input)

        # Ha a fájl üres vagy hibás volt, kilépünk
        if start_state is None:
            return

        # 2. Szavak szétválasztása
        words_to_check = args.check.split(',')
        results = []

        # 3. Szimuláció minden szóra
        for word in words_to_check:
            if self.simulate_dfa(word, start_state, accept_states, transitions):
                results.append("IGEN")
            else:
                results.append("NEM")

        # 4. Eredmény kiírása az output fájlba
        with open(args.output, 'w', encoding='utf-8') as out_file:
            for res in results:
                out_file.write(res + "\n")

    def load_dfa(self, filepath):
        """Beolvassa a DFA adatait a fájlból."""
        transitions = {}

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]

        if len(lines) < 4:
            return None, None, None

        start_state = lines[2]
        accept_states = set(lines[3].split())  # Halmaz a gyors kereséshez

        # Átmenetek beolvasása az sortól
        for line in lines[4:]:
            if not line:
                continue
            parts = line.split()
            if len(parts) == 3:
                src, symbol, dest = parts
                transitions[(src, symbol)] = dest

        return start_state, accept_states, transitions

    def simulate_dfa(self, word, start_state, accept_states, transitions):
        """Végrehajtja a determinisztikus véges automata szimulációját egy szón."""
        current_state = start_state

        for char in word:
            # Megnézzük a szótárban, hova kell lépnünk az aktuális állapotból a betű hatására
            if (current_state, char) in transitions:
                current_state = transitions[(current_state, char)]
            else:
                # Nincs definiált átmenet (csapda állapot), a szó elutasítva
                return False

        # Ha végigértünk a szón, elfogadó állapotban vagyunk-e?
        return current_state in accept_states