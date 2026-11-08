from project.problem import Problem
import re


class RegexProblem(Problem):

    def initialize_parser(self, parser):
        parser.add_argument('--rgx', type=int, help='A végrehajtandó regex feladat sorszáma (1-5)')

    def is_chosen_problem(self, args):
        return hasattr(args, 'rgx') and args.rgx is not None

    def run(self, args):
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
        """
        patterns = [
            # 1. az összes sort, amelyik 10. hónap 15-én jött létre (15554)
            re.compile(r'^10-15 '),

            # 2. az összes sort, amelyik 10. hónap 15-én 10 óra 18 perc és 51 másodperckor jött létre (2816)
            re.compile(r'^10-15 10:18:51\.'),

            # 3. az összes sort, amelyik 51 másodperckor jött létre (mindegy a perc) (2825)
            re.compile(r'^[0-9-]+\s+[0-9]{2}:[0-9]{2}:51\.'),

            # 4. az összes lowmemorykiller taget tartalmazó sor (10)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+[IDVEFAW]\s+lowmemorykiller\s*:'),

            # 5. az összes 10:18:51 kor keletkező 221-es process id-jú sort (1)
            re.compile(r'^[0-9-]+\s+10:18:51\.[0-9]+\s+221\s+'),

            # 6. az összes hibát tartalmazó sort (E) (3196)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+E\s+'),

            # 7. az összes warningot (W) amit a PackageManager küld (104)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+W\s+PackageManager\s*:'),

            # 8. az összes ExoPlayer-es debug (D) infót (54)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+D\s+.*ExoPlayer'),

            # 9. az összes java állomány pozíciót tartalmazó hibát és warningot (EW .java:) (645)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+[EW]\s+.*\.java:'),

            # 10. az összes olyan sort, ami tartalmazza a Thread szót a message részben (nem a tagben) (244)
            re.compile(r'^[0-9-]+\s+[0-9:.]+\s+[0-9]+\s+[0-9]+\s+[IDVEFAW]\s+.+?:\s+.*Thread')
        ]

        counts = [0] * 10
        for line in lines:
            for i, pattern in enumerate(patterns):
                if pattern.search(line):
                    counts[i] += 1

        return [str(c) for c in counts]

    def task_2(self, lines):
        pattern = re.compile(r'^[0-9-]+ +[0-9:.]+ +[0-9]+ +[0-9]+ +E +.*?\(([^():]+\.java):[0-9]+\)')
        results = []
        for line in lines:
            match = pattern.search(line)
            if match:
                results.append(match.group(1))
        return results

    def task_3(self, lines):
        pattern = re.compile(r'^[0-9-]+ +[0-9:.]+ +([0-9]+) +[0-9]+ +[IDVEFAW]\b')
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
        pattern = re.compile(r'^[0-9-]+ +[0-9:.]+ +([0-9]+) +[0-9]+ +E\b')
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
        pattern = re.compile(r'^[0-9-]+ +[0-9:.]+ +([0-9]+) +\1 +E\b')
        count = 0
        for line in lines:
            if pattern.search(line):
                count += 1
        return [str(count)]