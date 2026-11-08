from project.problem import Problem
import sys
import re

class MiniProblem(Problem):

    def initialize_parser(self, parser):
        """
        Hozzáadjuk a --mini kapcsolót a parancssori argumentumokhoz.
        """
        parser.add_argument('--mini', action='store_true', help='Minimalizálja a DFA automatát')

    def is_chosen_problem(self, args):
        """
        Akkor fut le, ha a --mini flag meg lett adva.
        """
        return hasattr(args, 'mini') and args.mini

    def run(self, args):
        """
        A minimalizálás fő folyamata: beolvasás, elérhető állapotok szűrése,
        partíciófinomítás, majd kiírás.
        """
        dfa_data = self.load_and_validate_dfa(args.input)
        if not dfa_data:
            return

        states, alphabet, start_state, accept_states, transitions = dfa_data

        # Minimalizálás végrehajtása
        min_states, min_start, min_accept, min_transitions = self.minimize_dfa(
            states, alphabet, start_state, accept_states, transitions
        )

        # Eredmény kiírása
        self.save_dfa(args.output, alphabet, min_states, min_start, min_accept, min_transitions)

    def load_and_validate_dfa(self, filepath):
        """
        Beolvassa az automatát és ellenőrzi az állapotok/szimbólumok érvényességét.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]

        if len(lines) < 4:
            print("Hiba: A bemeneti fájl túl rövid.", file=sys.stderr)
            return None

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2]
        accept_states = set(lines[3].split() if lines[3] else [])

        valid_states = set(states)
        valid_alphabet = set(alphabet)

        # Alapvető hibakezelés
        if start_state not in valid_states:
            print(f"Hiba: Érvénytelen kezdőállapot: {start_state}", file=sys.stderr)
            return None

        for acc in accept_states:
            if acc not in valid_states:
                print(f"Hiba: Érvénytelen végállapot: {acc}", file=sys.stderr)
                return None

        transitions = {}
        for line in lines[4:]:
            if not line:
                continue
            parts = line.split()
            if len(parts) == 3:
                src, symbol, dest = parts
                if src not in valid_states or dest not in valid_states:
                    print(f"Hiba: Ismeretlen állapot az átmenetben: {line}", file=sys.stderr)
                    return None
                if symbol not in valid_alphabet:
                    print(f"Hiba: Ismeretlen szimbólum az átmenetben: {line}", file=sys.stderr)
                    return None
                transitions[(src, symbol)] = dest

        return states, alphabet, start_state, accept_states, transitions

    def state_sort_key(self, state_name):
        """
        Segédfüggvény az állapotnevek természetes rendezéséhez (pl. q1 < q2 < q10).
        """
        match = re.match(r'^([a-zA-Z]+)(\d+)$', state_name)
        if match:
            return (match.group(1), int(match.group(2)))
        return (state_name, 0)

    def to_s_name(self, q_name):
        """
        Átalakítja a 'q' kezdetű állapotnevet 's' kezdetűre (pl. q1 -> s1).
        """
        if q_name.startswith('q'):
            return 's' + q_name[1:]
        return 's' + q_name

    def minimize_dfa(self, states, alphabet, start_state, accept_states, transitions):
        """
        DFA minimalizálása ekvivalenciaosztályok (partíciófinomítás) segítségével.
        """
        # 1. Elérhetetlen állapotok eltávolítása (BFS bejárással a kezdőállapotból)
        reachable = set()
        queue = [start_state]
        while queue:
            curr = queue.pop(0)
            if curr not in reachable:
                reachable.add(curr)
                for sym in alphabet:
                    if (curr, sym) in transitions:
                        nxt = transitions[(curr, sym)]
                        if nxt not in reachable:
                            queue.append(nxt)

        # Csak az elérhető állapotokkal dolgozunk tovább
        reachable_states = [s for s in states if s in reachable]
        accept_reachable = set(s for s in accept_states if s in reachable)
        non_accept_reachable = set(reachable_states) - accept_reachable

        # 2. Kezdeti partíció: elfogadó és nem elfogadó állapotok szétválasztása
        partitions = []
        if accept_reachable:
            partitions.append(accept_reachable)
        if non_accept_reachable:
            partitions.append(non_accept_reachable)

        # 3. Partíciók finomítása, amíg van változás
        changed = True
        while changed:
            changed = False
            new_partitions = []

            # Szótár: melyik állapot jelenleg hányadik partícióban van
            state_to_part = {}
            for idx, part in enumerate(partitions):
                for s in part:
                    state_to_part[s] = idx

            for part in partitions:
                if len(part) <= 1:
                    new_partitions.append(part)
                    continue

                # Csoportosítjuk az állapotokat aszerint, hogy az egyes betűkkel melyik partícióba visznek
                subgroups = {}
                for s in part:
                    # Aláírás (signature): minden betűre melyik partícióba jutunk (-1, ha nincs él)
                    sig = []
                    for sym in alphabet:
                        if (s, sym) in transitions:
                            dest = transitions[(s, sym)]
                            sig.append(state_to_part.get(dest, -1))
                        else:
                            sig.append(-1)
                    sig_tuple = tuple(sig)
                    subgroups.setdefault(sig_tuple, set()).add(s)

                if len(subgroups) > 1:
                    changed = True
                new_partitions.extend(subgroups.values())

            partitions = new_partitions

        # 4. Új állapotnevek meghatározása (minden csoport a legkisebb nevű elemről kapja az 's' nevét)
        state_mapping = {}  # eredeti_allapot -> uj_s_allapot
        new_states_set = set()

        for part in partitions:
            # Megkeressük a legkisebb nevű állapotot a partícióban (pl. {q1, q5} -> q1 -> s1)
            min_orig_state = min(part, key=self.state_sort_key)
            s_name = self.to_s_name(min_orig_state)
            new_states_set.add(s_name)
            for s in part:
                state_mapping[s] = s_name

        # Állapotok rendezése
        min_states = sorted(list(new_states_set), key=self.state_sort_key)
        min_start = state_mapping[start_state]

        min_accept_set = {state_mapping[s] for s in accept_reachable}
        min_accept = sorted(list(min_accept_set), key=self.state_sort_key)

        # 5. Átmenetek felépítése (duplikációk nélkül)
        min_transitions_set = set()
        for (src, sym), dest in transitions.items():
            if src in reachable and dest in reachable:
                new_src = state_mapping[src]
                new_dest = state_mapping[dest]
                min_transitions_set.add((new_src, sym, new_dest))

        # Ábécé sorrend: kiindulási állapot, szimbólum, célállapot
        min_transitions = sorted(list(min_transitions_set), key=lambda t: (t[0], t[1], t[2]))

        return min_states, min_start, min_accept, min_transitions

    def save_dfa(self, filepath, alphabet, states, start_state, accept_states, transitions):
        """
        Kiírja a minimalizált DFA-t a kimeneti fájlba.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(" ".join(states) + "\n")
            f.write(" ".join(alphabet) + "\n")
            f.write(start_state + "\n")
            f.write(" ".join(accept_states) + "\n")
            for src, sym, dest in transitions:
                f.write(f"{src} {sym} {dest}\n")