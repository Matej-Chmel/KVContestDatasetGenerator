from collections import defaultdict, Counter
from recordclass import recordclass
from src.common import Ptw
from src.common.math import percentage, percentage_str

# abbreviation: ccs
CmdChainSample = recordclass(
    'CmdChainSample',
    'chain_lengths, repeated, not_repeated'
)

class CommandChain:
    """Computes statistics of consecutive commands (chains) 
    and chances of command repetition."""
    def __init__(self):
        self.wtab = None
        self.S_ocs = 0
        self.H_ocs = 0
        self.H_more_than_S = False
        self.last_cmd = ''
        self.chain_len = 0
        self.current_ccs = CmdChainSample([], 0, 0)
        self.ccs_by_key = defaultdict(lambda: CmdChainSample([], 0, 0))
        self.final_ccs_by_key = defaultdict(list)
    def comp_all(self, line):
        if not self.H_more_than_S:
            if line.cmd == 'H':
                self.H_ocs += 1
            elif line.cmd == 'S':
                self.S_ocs += 1
        if line.cmd == self.last_cmd:
            self.chain_len += 1
            self.current_ccs.repeated += 1
        else:
            self.current_ccs.not_repeated += 1
            self.current_ccs.chain_lengths.append(self.chain_len)
            self.last_cmd = line.cmd
            self.chain_len = 1
            self.current_ccs = self.ccs_by_key[self.last_cmd]
        if not self.H_more_than_S and self.H_ocs > self.S_ocs:
            self.H_more_than_S = True
            self.end_of_dataset(None)
    def end_of_dataset(self, last_line):
        for cmd in self.ccs_by_key:
            self.final_ccs_by_key[cmd].append(self.ccs_by_key[cmd])
            if last_line is None:
                self.ccs_by_key[cmd] = CmdChainSample([], 0, 0)
    def _create_wtab(self):
        if self.wtab is not None:
            return
        self.wtab = Ptw(
            [
                'Command',
                'Repeated', '% from total',
                'Not repeated', '% from total ',
                'Chains 1, 2, 3 and longest'
            ],
            sortby=0, aligns='crrrrC', common_formatter=((2, 4), percentage_str)
        )
        for cmd in self.final_ccs_by_key:
            for idx, sample in enumerate(self.final_ccs_by_key[cmd]):
                total_ocs = sample.repeated + sample.not_repeated
                chain_counter = Counter(sample.chain_lengths)
                longest_chain = max(sample.chain_lengths, default=0)
                self.wtab.write_raw([
                    f'{cmd} {idx}',
                    sample.repeated, percentage(sample.repeated, total_ocs),
                    sample.not_repeated, percentage(sample.not_repeated, total_ocs),
                    f'''{', '.join([
                            str((chain, chain_counter[chain])) 
                            for chain in [1, 2, 3, longest_chain]
                    ])}'''
                ])
            self.wtab.add_raw_to_table()
            self.wtab.sort_raw()
    def output(self):
        self._create_wtab()
        return self.wtab.table
