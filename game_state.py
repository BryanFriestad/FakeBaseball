from enum import Enum


class PAOutcome(Enum):
    STRIKEOUT = 0
    WALK = 1
    HR = 2
    TRIPLE = 3
    DOUBLE = 4
    SINGLE = 5
    GB = 6
    SF = 7
    DP = 8
    PO = 9
    FC = 10


class GameState:
    def __init__(self):
        self.inning = 1
        self.top = True
        self.score = [0, 0]
        self.outs = 0
        self.strikes = 0
        self.balls = 0
        self.bases = [False, False, False]
        self.outcomes = {outcome: 0 for outcome in PAOutcome}
        self.pa_count = 0

    def _change_inning(self):
        self.bases = [False, False, False]
        self.outs = 0
        if self.top:
            self.top = False
        else:
            self.top = True
            self.inning += 1

    def _end_pa(self, outcome: PAOutcome):
        self.strikes = 0
        self.balls = 0
        self.outcomes[outcome] += 1
        self.pa_count += 1

    def _strikeout(self):
        self.outs += 1
        if self.outs == 3:
            self._change_inning()
        self._end_pa(PAOutcome.STRIKEOUT)

    def strike(self):
        self.strikes += 1
        if self.strikes == 3:
            self._strikeout()

    def ball(self):
        self.balls += 1
        if self.balls == 4:
            self._walk()

    def foul(self):
        if self.strikes < 2:
            self.strikes += 1

    def _walk(self):
        self._advance_forced_runners()
        self.bases[0] = True
        self._end_pa(PAOutcome.WALK)

    def _num_on_base(self):
        return sum(self.bases)

    def _leading_runner_position(self):
        if self.bases[2]:
            return 2
        if self.bases[1]:
            return 1
        if self.bases[0]:
            return 0
        return -1

    def _forced_runner_positions(self):
        '''
        Returns a list of forced runner positions in order from least to most advanced
        '''
        positions = []
        if self.bases[0]:
            positions.append(0)
            if self.bases[1]:
                positions.append(1)
                if self.bases[2]:
                    positions.append(2)
        return positions

    def _leading_forced_runner_position(self):
        forced_runners = self._forced_runner_positions()
        if len(forced_runners) == 0:
            return -1
        return max(forced_runners)

    def _advance_forced_runners(self):
        forced_runners = self._forced_runner_positions()
        for runner in forced_runners:
            self.bases[runner] = False
            if runner == 2:
                self.score[0 if self.top else 1] += 1
            else:
                self.bases[runner + 1] = True

    def home_run(self):
        self.score[0 if self.top else 1] += (self._num_on_base() + 1)
        self.bases = [False, False, False]
        self._end_pa(PAOutcome.HR)

    def triple(self):
        self.score[0 if self.top else 1] += self._num_on_base()
        self.bases = [False, False, True]
        self._end_pa(PAOutcome.TRIPLE)

    def double(self):
        '''
        Runners on second and third score, runner on first moves to third, batter at second
        '''
        runners_home = self.bases[1] + self.bases[2]
        self.bases[2] = self.bases[0]
        self.bases[1] = True
        self.bases[0] = False
        self.score[0 if self.top else 1] += runners_home
        self._end_pa(PAOutcome.DOUBLE)

    def single(self):
        '''
        Anyone on third base scores. 
        Anyone on second base moves to third base. 
        Anyone on first base moves to second base. 
        The batter is placed on first base.
        '''
        runners_home = self.bases[2]
        self.bases[2] = self.bases[1]
        self.bases[1] = self.bases[0]
        self.bases[0] = True
        self.score[0 if self.top else 1] += runners_home
        self._end_pa(PAOutcome.SINGLE)

    def ground_ball(self):
        '''
        Batter is out.
        Any forced runners advance one base.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.GB)
            self._change_inning()
            return
        self._advance_forced_runners()
        self._end_pa(PAOutcome.GB)

    def sac_fly(self):
        '''
        Batter is out.
        Any runner on third base scores.
        All other runners hold.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.SF)
            self._change_inning()
            return
        if self.bases[2]:
            self.score[0 if self.top else 1] += 1
            self.bases[2] = False
        self._end_pa(PAOutcome.SF)

    def double_play(self):
        '''
        Batter is out.
        If there are less than three outs, the leading forced runner is out.
        All other forced runners advance one base.
        All other runners hold.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.DP)
            self._change_inning()
            return

        #  the leading forced runner is out
        lead_forced_runner = self._leading_forced_runner_position()
        if lead_forced_runner != -1:
            self.bases[lead_forced_runner] = False
            self.outs += 1
            if self.outs == 3:
                self._end_pa(PAOutcome.DP)
                self._change_inning()
                return
        
        # all other forced runners advance one base
        self._advance_forced_runners()
        self._end_pa(PAOutcome.DP)

    def pop_out(self):
        '''
        Batter is out. All runners hold.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.PO)
            self._change_inning()
            return
        self._end_pa(PAOutcome.PO)

    def fielders_choice(self):
        '''
        If there are no runners on base, the batter is out.
        Otherwise, the lead runner is out, all forced runners advance one base, and the batter is placed on first base.
        '''
        lead_runner = self._leading_runner_position()
        if lead_runner == -1: # there are no baserunners, instead the batter is out
            self.outs += 1
            if self.outs == 3:
                self._change_inning()
            self._end_pa(PAOutcome.FC)
            return # return early if there are no baserunners
            
        # go for lead runner
        self.bases[lead_runner] = False
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.FC)
            self._change_inning()
            return

        self._advance_forced_runners()
        self.bases[0] = True
        self._end_pa(PAOutcome.FC)
