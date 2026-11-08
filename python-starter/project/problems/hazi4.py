from project.problem import Problem
import re


class RegexProblem(Problem):

    def initialize_parser(self, parser):
        """
        Hozzáadjuk az --rgx parancssori argumentumot, amely egy számot vár (1-től 5-ig).
        """
        parser.add_argument('--rgx', type=int, help='A végrehajtandó regex feladat sorszáma (1-5)')

    def is_chosen_problem(self, args):
        """
        Akkor fut le ez a modul, ha a parancssorban megadták az --rgx kapcsolót.
        """
        return hasattr(args, 'rgx') and args.rgx is not None

    def run(self, args):
        """
        Beolvassa a logfájlt, és a feladat sorszáma alapján meghívja a megfelelő regex feldolgozót.
        """
        with open(args.input, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        results = []

        if args.rgx == 1:
            results = self.task_1(lines)
        elif args.rgx == 2:
            results = self.task_2(lines)
        elif args.rgx == 3:
            results = self.task_3(lines)
        elif args.rgx == 4:
            results = self.task_4(lines)
        elif args.rgx == 5:
            results = self.task_5(lines)

        with open(args.output, 'w', encoding='utf-8') as out_file:
            for res in results:
                out_file.write(f"{res}\n")

    def task_1(self, lines):
        """
        1. feladat: 10 különböző feltétel megszámolása a logban.
        Log sor általános felépítése:
        MM-DD HH:MM:SS.mmm   PID   TID LEVEL TAG: MESSAGE
        """
        patterns = [
            # 1. 10. hónap 15-én jött létre
            re.compile(r'^10-15 '),

            # 2. 10. hónap 15-én 10 óra 18 perc és 51 másodperckor jött létre
            re.compile(r'^10-15 10:18:51\.'),

            # 3. 51 másodperckor jött létre (mindegy a perc)
            re.compile(r'^[0-9-]+\s+[0-9]{2}:[0-9]{2}:51\.'),

            # 4. lowmemorykiller taget tartalmazó sor
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+[IDVEFAW]\s+[^\s:]*lowmemorykiller[^\s:]*\s*:'),

            # 5. 10:18:51-kor keletkező 221-es process id-jú sor
            re.compile(r'^[0-9-]+\s+10:18:51\.[0-9]+\s+221\s+'),

            # 6. hibát tartalmazó sor (E)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+E\s+'),

            # 7. warning (W), amit a PackageManager küld
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+W\s+PackageManager\s*:'),

            # 8. ExoPlayer-es debug (D) infó
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+D\s+[^\s:]*ExoPlayer[^\s:]*\s*:'),

            # 9. java állomány pozíciót tartalmazó hiba és warning (E vagy W ... .java:)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+[EW]\s+.*\.java:'),

            # 10. tartalmazza a Thread szót a message részben (nem a tagben) -> tag: message
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+[IDVEFAW]\s+.+?:\s+.*Thread')
        ]

        counts = [0] * 10
        for line in lines:
            for i, pattern in enumerate(patterns):
                if pattern.search(line):
                    counts[i] += 1

        return [str(c) for c in counts]

    def task_2(self, lines):
        """
        2. feladat: Az összes hiba (E sorok) származási helye (pl. HashMap.java)
        az előfordulásuk sorrendjében.
        """
        # Csak az E szintű sorokban keressük a zárójelben lévő (.java:szám) mintát
        pattern = re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+E\s+.*?\(([A-Za-z0-9_$]+\.java):[0-9]+\)')
        results = []

        for line in lines:
            match = pattern.search(line)
            if match:
                results.append(match.group(1))

        return results

    def task_3(self, lines):
        """
        3. feladat: Az összes különböző process id (PID) az előfordulási sorrendjüket megtartva.
        """
        pattern = re.compile(r'^[0-9-]+\s+[0-9:.]+\s+([0-9]+)\s+[0-9]+\s+[IDVEFAW]')
        seen_pids = set()
        ordered_pids = []

        for line in lines:
            match = pattern.search(line)
            if match:
                pid = match.group(1)
                if pid not in seen_pids:
                    seen_pids.add(pid)
                    ordered_pids.append(pid)

        return ordered_pids

    def task_4(self, lines):
        """
        4. feladat: A legtöbb errort (E) tartalmazó process.
        Forma: PID=xx (xx errors)
        """
        pattern = re.compile(r'^[0-9-]+\s+[0-9:.]+\s+([0-9]+)\s+[0-9]+\s+E\s+')
        error_counts = {}

        for line in lines:
            match = pattern.search(line)
            if match:
                pid = match.group(1)
                error_counts[pid] = error_counts.get(pid, 0) + 1

        if not error_counts:
            return []

        max_pid = max(error_counts, key=error_counts.get)
        max_count = error_counts[max_pid]

        return [f"PID={max_pid} ({max_count} errors)"]

    def task_5(self, lines):
        """
        5. feladat: A fő szálon történt hibák (E) száma (amikor a PID és a TID megegyezik).
        """
        # A \1 visszahivatkozás (backreference) biztosítja, hogy a TID pontosan ugyanaz legyen, mint a PID
        pattern = re.compile(r'^[0-9-]+\s+[0-9:.]+\s+([0-9]+)\s+\1\s+E\s+')
        count = 0

        for line in lines:
            if pattern.search(line):
                count += 1

        return [str(count)]