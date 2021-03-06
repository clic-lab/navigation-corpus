# Natural Language Toolkit: Earley Parser Demo
#
# Copyright (C) 2003 University of Pennsylvania
# Author: Robert Berwick <berwick@ai.mit.edu>
# URL: <http://nltk.sf.net>
# For license information, see LICENSE.TXT
#
# $Id: earley.py,v 1.1.1.1 2004/02/25 17:16:48 adastra Exp $

import Tkinter
import math

from nltk.parser.earley import *
from nltk.parser.chart import *
from nltk.cfg import *
from nltk.tokenizer import WSTokenizer
from nltk.token import Token, Location
from nltk.tree import TreeToken
from nltk.draw import ShowText
from nltk.draw.chart import *

############################ EARLEY EDGE RULES ##############################
#(let you select an edge, and apply 
    
class EdgeRule(ChartRuleI):
    def __init__(self, edge): self._edge = edge

class EarleyEdgeScanner(EdgeRule):
    def apply(self, chart, grammar):
        nextcat = self._edge.next()
        if grammar.isPartOfSpeech(nextcat) and not self._edge.complete():
            word = chart.wordAt(self._edge.loc().end())
            if nextcat in grammar.getPartsOfSpeech(word):
                prod = cfg.CFGProduction(nextcat, word)
                loc = self._edge.loc().end_loc()                    
                return [chartmod.self_loop_edge(prod, loc)]
        return []
    def __str__(self): return 'Earley Scanner'

class EarleyEdgePredictor(EdgeRule):
    def apply(self, chart, grammar):
        nextcat = self._edge.next()
        if not grammar.isPartOfSpeech(nextcat) and not self._edge.complete():
            for prod in grammar.getRules(nextcat):
                loc = self._edge.loc().end_loc()
                return [chartmod.self_loop_edge(prod, loc)]
        return []
    def __str__(self): return 'Earley Predictor'

class EarleyEdgeCompleter(chartmod.ChartRuleI):
    def apply(self, chart, grammar):
        edges = []
        if not self._edge.complete():
            for edge2 in chart.complete_edges():
                if (self._edge.next() == edge2.lhs() and
                    self._edge.end() == edge2.start()):
                    edges.append(chartmod.fr_edge(self._edge, edge2))
        return edges
    def __str__(self): return 'Earley Completer Rule'

############################## CHART VIEWER ##################################

class FullChartViewer:
    RULENAME = {'FundamentalRule': 'Fundamental Rule',
                'FundamentalEdgeRule': 'Fundamental Rule',

                'TopDownInitRule': 'Top-down Initialization',
                
                'TopDownRule': 'Top-down Rule',
                'TopDownEdgeRule': 'Top-down Rule',
                
                'BottomUpRule': 'Bottom-up Rule',
                'BottomUpEdgeRule': 'Bottom-up Rule',
                }
    
    def __init__(self, grammar, text, title):
        self.root = None
        try:
            # Create the root window.
            self._root = Tkinter.Tk()
            self._root.title(title)
            self._root.bind('q', self.destroy)
            buttons3 = Tkinter.Frame(self._root)
            buttons3.pack(side='bottom', fill='none')
            buttons2 = Tkinter.Frame(self._root)
            buttons2.pack(side='bottom', fill='none')
            buttons1 = Tkinter.Frame(self._root)
            buttons1.pack(side='bottom', fill='x')

            self._lexiconview = self._grammarview = None
    
            self._grammar = grammar
            self._tok_sent = text
            self._cp = SteppingEarleyParser(self._grammar)
            self._cp.initialize(self._tok_sent)

            # Keep track of whether we're stepping & animating.
            self._step = Tkinter.IntVar(self._root)
            self._step.set(1)
            self._animate = Tkinter.IntVar(self._root)
            self._animate.set(2)

            self._chart = self._cp.chart()
            self._cv = ChartView(self._chart, self._tok_sent,
                                 self._root, draw_tree=1, draw_source=1)

            ruletxt = 'Last edge generated by:'
            Tkinter.Label(buttons1,text=ruletxt).pack(side='left')
            self._rulelabel = Tkinter.Label(buttons1, width=30,
                                            font=('helvetica', 30, 'bold'),
                                            relief='groove', anchor='w')
            self._rulelabel.pack(side='left')
            step = Tkinter.Checkbutton(buttons1, variable=self._step,
                                       text='Step')
            step.pack(side='right')

            ## Set up buttons for rules & strategies
            Tkinter.Button(buttons2, text='Top Down\nStrategy',
                           background='#a0c0c0', foreground='black',
                           command=self.top_down_strategy).pack(side='left')
            Tkinter.Button(buttons2, text='Bottom Up\nStrategy',
                           background='#a0c0c0', foreground='black',
                           command=self.bottom_up_strategy).pack(side='left')
            Tkinter.Button(buttons2, text='Top Down Init\nRule',
                           background='#a0d0a0', foreground='black',
                           command=self.top_down_init).pack(side='left')
            Tkinter.Button(buttons2, text='Top down\nRule',
                           background='#a0d0a0', foreground='black',
                           command=self.top_down).pack(side='left')
            Tkinter.Button(buttons2, text='Bottom Up\nInit Rule',
                           background='#a0d0a0', foreground='black',
                           command=self.bottom_up_init).pack(side='left')
            Tkinter.Button(buttons2, text='Fundamental\nRule',
                           background='#a0d0a0', foreground='black',
                           command=self.fundamental).pack(side='left')

            Tkinter.Label(buttons3,text="Earley:").pack(side='left')
            Tkinter.Button(buttons3, text='Earley\nStrategy',
                           background='#a0c0c0', foreground='black',
                           command=self.earley_strategy).pack(side='left')
            Tkinter.Button(buttons3, text='Earley\nInit Rule',
                           background='#a0d0a0', foreground='black',
                           command=self.earley_init).pack(side='left')
            Tkinter.Button(buttons3, text='Earley\nScanner',
                           background='#a0d0a0', foreground='black',
                           command=self.earley_scanner).pack(side='left')
            Tkinter.Button(buttons3, text='Earley\nPredictor',
                           background='#a0d0a0', foreground='black',
                           command=self.earley_predictor).pack(side='left')
            Tkinter.Button(buttons3, text='Earley\nCompleter',
                           background='#a0d0a0', foreground='black',
                           command=self.earley_completer).pack(side='left')
    
            # For animations..
            self._animating = 0  # are we animating right now?
        
            # Initialize the rule-label font.
            size = self._cv.get_font_size()
            self._rulelabel.configure(font=('helvetica', -size, 'bold'))

            # Set up a menu bar.
            self._init_menubar()

            # Set up keyboard bindings.
            self._init_bindings()
            
            # Enter mainloop.
            Tkinter.mainloop()
        except:
            print 'Error creating Tree View'
            self.destroy()
            raise

    def _init_bindings(self):
        self._root.bind('<Up>', self._cv.scroll_up)
        self._root.bind('<Down>', self._cv.scroll_down)
        self._root.bind('q', self.destroy)
        self._root.bind('x', self.destroy)
        self._root.bind('<F1>', self.help)
        
        self._root.bind('<Control-s>', self.save)
        self._root.bind('<Control-o>', self.load)
        self._root.bind('<Control-r>', self.reset)
        
        self._root.bind('t', self.top_down_strategy)
        self._root.bind('b', self.bottom_up_strategy)
        self._root.bind('e', self.earley_strategy)
        self._root.bind('f', self.fundamental)

        # Animation speed control
        self._root.bind('-', lambda e,a=self._animate:a.set(1))
        self._root.bind('=', lambda e,a=self._animate:a.set(2))
        self._root.bind('+', lambda e,a=self._animate:a.set(3))

        # Step control
        self._root.bind('s', lambda e,s=self._step:s.set(not s.get()))

    def _init_menubar(self):
        menubar = Tkinter.Menu(self._root)
        
        filemenu = Tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Save Chart', underline=0,
                             command=self.save, accelerator='Ctrl-s')
        filemenu.add_command(label='Open Chart', underline=0,
                             command=self.load, accelerator='Ctrl-o')
        filemenu.add_command(label='Reset Chart', underline=0,
                             command=self.reset, accelerator='Ctrl-r')
        filemenu.add_command(label='Exit', underline=1,
                             command=self.destroy,
                             accelerator='x')
        menubar.add_cascade(label='File', underline=0,
                            menu=filemenu)
        
        rulemenu = Tkinter.Menu(menubar, tearoff=0)
        rulemenu.add_command(label='Top Down Strategy', underline=0,
                             command=self.top_down_strategy,
                             accelerator='t')
        rulemenu.add_command(label='Bottom Up Strategy', underline=0,
                             command=self.bottom_up_strategy,
                             accelerator='b')
        rulemenu.add_command(label='Earley Strategy', underline=0,
                             command=self.earley_strategy,
                             accelerator='e')
        rulemenu.add_separator()
        rulemenu.add_command(label='Bottom Up Init Rule',
                             command=self.bottom_up_init)
        rulemenu.add_command(label='Top Down Init Rule',
                             command=self.top_down_init)
        rulemenu.add_command(label='Top Down Rule',
                             command=self.top_down_init)
        rulemenu.add_command(label='Fundamental Rule', underline=0,
                             command=self.fundamental, accelerator='f')
        rulemenu.add_command(label='Earley Init Rule',
                             command=self.earley_init)
        rulemenu.add_command(label='Earley Scanner',
                             command=self.earley_scanner)
        rulemenu.add_command(label='Earley Predictor',
                             command=self.earley_predictor)
        rulemenu.add_command(label='Earley Completer',
                             command=self.earley_completer)

        menubar.add_cascade(label='Apply', underline=0,
                            menu=rulemenu)

        animatemenu = Tkinter.Menu(menubar, tearoff=0)
        animatemenu.add_checkbutton(label="Step", underline=0,
                                    variable=self._step,
                                    accelerator='s')
        animatemenu.add_separator()
        animatemenu.add_radiobutton(label="No Animation", underline=0,
                                    variable=self._animate, value=0)
        animatemenu.add_radiobutton(label="Slow Animation", underline=0,
                                    variable=self._animate, value=1,
                                    accelerator='-')
        animatemenu.add_radiobutton(label="Normal Animation", underline=0,
                                    variable=self._animate, value=2,
                                    accelerator='=')
        animatemenu.add_radiobutton(label="Fast Animation", underline=0,
                                    variable=self._animate, value=3,
                                    accelerator='+')
        menubar.add_cascade(label="Animate", underline=1, menu=animatemenu)
        
        zoommenu = Tkinter.Menu(menubar, tearoff=0)
        self._size = Tkinter.IntVar(self.root)
        self._size.set(self._cv.get_font_size())
        zoommenu.add_radiobutton(label='Smallest', variable=self._size,
                                 underline=1, value=10, command=self.resize)
        zoommenu.add_radiobutton(label='Small', variable=self._size,
                                 underline=0, value=12, command=self.resize)
        zoommenu.add_radiobutton(label='Medium', variable=self._size,
                                 underline=0, value=14, command=self.resize)
        zoommenu.add_radiobutton(label='Large', variable=self._size,
                                 underline=0, value=18, command=self.resize)
        zoommenu.add_radiobutton(label='Biggest', variable=self._size,
                                 underline=0, value=24, command=self.resize)
        menubar.add_cascade(label='Zoom', underline=0,
                            menu=zoommenu)

        helpmenu = Tkinter.Menu(menubar, tearoff=0)
        helpmenu.add_command(label='Instructions', underline=0,
                             command=self.help, accelerator='F1')
        menubar.add_cascade(label='Help', underline=0, menu=helpmenu)
        
        self._root.config(menu=menubar)

    def help(self, *e):
        self._animating = 0
        # The default font's not very legible; try using 'fixed' instead. 
        try:
            ShowText(self._root, 'Help: Chart Parser Demo',
                     (__doc__).strip(), width=75, font='fixed')
        except:
            ShowText(self._root, 'Help: Chart Parser Demo',
                     (__doc__).strip(), width=75)

    def load(self, *e):
        "Load a chart from a pickle file"
        import pickle
        from tkFileDialog import askopenfilename
        ftypes = [('Pickle file', '.pickle'),
                  ('All files', '*')]
        filename = askopenfilename(filetypes=ftypes,
                                   defaultextension='.pickle')
        if not filename: return
        chart = pickle.load(open(filename, 'r'))
        self._chart = chart
        self._cv.update(chart)
        self._cp.set_chart(chart)

    def save(self, *e):
        "Save a chart to a pickle file"
        import pickle
        from tkFileDialog import asksaveasfilename
        ftypes = [('Pickle file', '.pickle'),
                  ('All files', '*')]
        filename = asksaveasfilename(filetypes=ftypes,
                                     defaultextension='.pickle')
        if not filename: return
        pickle.dump(self._chart, open(filename, 'w'))
            
    def resize(self):
        self._animating = 0
        size = self._size.get()
        self._cv.set_font_size(size)
        self._rulelabel['font'] = ('helvetica', -size, 'bold')

    def view_grammar(self, *e):
        self._animating = 0
        self._grammarview = ProductionView(self._grammar.productions(),
                                           'Grammar')

    def reset(self, *e):
        self._animating = 0
        self._cp = SteppingEarleyParser(self._grammar)
        self._cp.initialize(self._tok_sent)
        self._chart = self._cp.chart()
        self._cv.update(self._chart)

    def display_rule(self, rule):
        if rule == None:
            self._rulelabel['text'] = ''
        else:
            name = FullChartViewer.RULENAME.get(rule.__class__.__name__,
                                          rule.__class__.__name__)
            self._rulelabel['text'] = name
            size = self._cv.get_font_size()
            self._rulelabel['font'] = ('helvetica', -size, 'bold')
            
    def apply_strategy(self, strategy, edge_strategy=None):
        if self._animating:
            self._animating = 0
            return
        self.display_rule(None)
        self._cv.unmark()
        if self._step.get():
            edge = self._cv.selected_edge()
            if (edge is not None) and (edge_strategy is not None):
                if self._apply_strategy([edge_strategy(edge)]) is None:
                    # Unselect it (select_edge toggles selection)
                    self._cv.select_edge(edge)
            else:
                self._apply_strategy(strategy)
        else:
            if self._animate.get():
                self._animating = 1
                self._animate_strategy(strategy)
            else:
                while self._cp.step(strategy=strategy):
                    self._cv.update()

    def _animate_strategy(self, strategy, speed=1):
        if self._animating == 0: return
        new_edge = self._cp.step(strategy=strategy)
        self._cv.unmark()
        if new_edge is not None:
            self.display_rule(self._cp.current_chartrule())
            self._cv.update()
            self._cv.view_edge(new_edge)
            if self._animate.get() == 0 or self._step.get() == 1:
                return
            if self._animate.get() == 1:
                self._cv.select_edge(new_edge)
                self._root.after(3000, self._animate_strategy, strategy)
            elif self._animate.get() == 2:
                self._cv.select_edge(new_edge)
                self._root.after(1000, self._animate_strategy, strategy)
            else:
                self._cv.mark_edge(new_edge)
                self._root.after(20, self._animate_strategy, strategy)
        
    def _apply_strategy(self, strategy):
        new_edge = self._cp.step(strategy=strategy)
                               
        if new_edge is not None:
            self.display_rule(self._cp.current_chartrule())
            self._cv.update()
            self._cv.mark_edge(new_edge)
            self._cv.view_edge(new_edge)
        return new_edge

    def top_down_init(self, *e):
        self.apply_strategy([TopDownInitRule()], None)

    def top_down_strategy(self, *e):
        self.apply_strategy([TopDownInitRule(), TopDownRule(),
                             FundamentalRule()], TopDownEdgeRule)

    def top_down(self, *e):
        self.apply_strategy([TopDownRule()], TopDownEdgeRule)

    def fundamental(self, *e):
        self.apply_strategy([FundamentalRule()], FundamentalEdgeRule)

    def bottom_up_init(self, *e):
        self.apply_strategy([BottomUpRule()], BottomUpEdgeRule)

    def bottom_up_strategy(self, *e):
        self.apply_strategy([BottomUpRule(), FundamentalRule()],
                            BottomUpEdgeRule)

    def earley_strategy(self, *e):
        self.apply_strategy([EarleyInitRule(), EarleyPredictor(),
                             EarleyScanner(), EarleyCompleter()],
                            EarleyEdgeScanner)

    def earley_init(self, *e):
        self.apply_strategy([EarleyInitRule()], None)

    def earley_scanner(self, *e):
        self.apply_strategy([EarleyScanner()], EarleyEdgeScanner)

    def earley_predictor(self, *e):
        self.apply_strategy([EarleyPredictor()], EarleyEdgePredictor)

    def earley_completer(self, *e):
        self.apply_strategy([EarleyCompleter()], EarleyEdgeCompleter)

        
    def destroy(self, *args):
        if self._lexiconview: self._lexiconview.destroy()
        if self._grammarview: self._grammarview.destroy()
        if self._root is None: return
        self._root.destroy()
        self._root = None


############################# GRAMMAR INPUT ##################################
from ScrolledText import ScrolledText

class GrammarGUI:
    def __init__(self, grammar, text, title='Input Grammar'):
        self.root = None
        try:
            self._root = Tkinter.Tk()
            self._root.title(title)

            level1 = Tkinter.Frame(self._root)
            level1.pack(side='top', fill='none')
            Tkinter.Frame(self._root).pack(side='top', fill='none')
            level2 = Tkinter.Frame(self._root)
            level2.pack(side='top', fill='x')            
            buttons = Tkinter.Frame(self._root)
            buttons.pack(side='top', fill='none')

            self.sentence = Tkinter.StringVar()            
            Tkinter.Label(level2, text="Sentence:").pack(side='left')
            Tkinter.Entry(level2, background='white', foreground='black',
                          width=60, textvariable=self.sentence).pack(
                side='left')

            lexiconFrame = Tkinter.Frame(level1)
            Tkinter.Label(lexiconFrame, text="Lexicon:").pack(side='top',
                                                              fill='x')
            Tkinter.Label(lexiconFrame, text="  ex. 'dog N':").pack(
                side='top', fill='x')
            self.lexicon = ScrolledText(lexiconFrame, background='white',
                                              foreground='black', width=30)
            self.lexicon.pack(side='top')


            grammarFrame = Tkinter.Frame(level1)
            Tkinter.Label(grammarFrame, text="Grammar:").pack(side='top',
                                                              fill='x')
            Tkinter.Label(grammarFrame,
                          text="  ex. 'S -> NP VP':").pack(side='top',fill='x')
            self.grammarRules = ScrolledText(grammarFrame, background='white',
                                              foreground='black', width=30)
            self.grammarRules.pack(side='top')
            
            lexiconFrame.pack(side='left')
            grammarFrame.pack(side='left')


            Tkinter.Button(buttons, text='Clear',
                           background='#a0c0c0', foreground='black',
                           command=self.clear).pack(side='left')
            Tkinter.Button(buttons, text='Parse',
                           background='#a0c0c0', foreground='black',
                           command=self.parse).pack(side='left')

            self.init_menubar()
            
            # Enter mainloop.
            Tkinter.mainloop()
        except:
            print 'Error creating Tree View'
            self.destroy()
            raise

    def init_menubar(self):
        menubar = Tkinter.Menu(self._root)
        
        filemenu = Tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Save Rules', underline=0,
                             command=self.save, accelerator='Ctrl-s')
        self._root.bind('<Control-s>', self.save)
        filemenu.add_command(label='Load Rules', underline=0,
                             command=self.load, accelerator='Ctrl-o')
        self._root.bind('<Control-o>', self.load)
        filemenu.add_command(label='Clear Rules', underline=0,
                             command=self.clear, accelerator='Ctrl-r')
        self._root.bind('<Control-r>', self.clear)
        filemenu.add_command(label='Exit', underline=1,
                             command=self.destroy, accelerator='Ctrl-q')
        self._root.bind('<Control-q>', self.destroy)
        menubar.add_cascade(label='File', underline=0,
                            menu=filemenu)
        self._root.config(menu=menubar)

    def getRules(self, makegrammar=True):
        """
        Takes the currently typed in rules and turns them from text into
        a list of either string rules or Earley CFGs
        """
        text = self.grammarRules.get(1.0, Tkinter.END)
        rules = []
        for item in text.split("\n"):
            moreitems = item.split(",")
            for furtheritem in moreitems:
                furtheritem = furtheritem.strip()
                if not furtheritem:
                    continue
                tokens = furtheritem.split()
                if not (len(tokens)>=3 and tokens[1] == "->"):
                    print "Invalid rule: %s"%furtheritem
                else:
                    if makegrammar:
                        rules.append(Rule(cfg.Nonterminal(tokens[0]),
                                          *map(lambda x: cfg.Nonterminal(x),
                                               tokens[2:])))
                    else:
                        rules.append(furtheritem.strip())
        return rules

    def getLexicon(self, makegrammar=True):
        """
        Takes the currently typed in lexicon and turns them from text into
        a list of either string lexical definitions or Earley CFGs
        """
        text = self.lexicon.get(1.0, Tkinter.END)
        lex = []
        for item in text.split("\n"):
            moreitems = item.split(",")
            for furtheritem in moreitems:
                furtheritem = furtheritem.strip()
                if not furtheritem:
                    continue
                tokens = furtheritem.split()
                if not len(tokens)>=2:
                    print "Invalid lexical mapping: %s"%furtheritem
                else:
                    if makegrammar:
                        word = tokens[0]
                        for pos in tokens[1:]:
                            lex.append(Rule(cfg.Nonterminal(pos), word))
                    else:
                        lex.append(furtheritem.strip())
        return lex

    def parse(self, *args):
        """
        Calls the FullChartViewer with the given grammar and lexicon to parse
        the given sentence
        """
        grammar = EarleyCFG(cfg.Nonterminal('S'),
                            self.getRules(), self.getLexicon())

        sent = self.sentence.get().strip()
        tok_sent = WSTokenizer().tokenize(sent)
        print "Starting chart parsing viewer"
        FullChartViewer(grammar, tok_sent, 'Parsing "%s"'%sent)

    def save(self, *args):
        "Save a rule/lexicon set to a text file"
        from tkFileDialog import asksaveasfilename
        ftypes = [('Text file', '.txt'),
                  ('All files', '*')]
        filename = asksaveasfilename(filetypes=ftypes,
                                     defaultextension='.txt')
        if not filename: return
        f = open(filename, 'w')
        f.write('---- Rules -----\n%s\n' % '\n'.join(self.getRules(False)))
        f.write('---- Lexicon -----\n%s\n' % '\n'.join(self.getLexicon(False)))
        f.close()
        
    def load(self, *args):
        "Load rule/lexicon set from a text file"
        from tkFileDialog import askopenfilename
        ftypes = [('Text file', '.txt'),
                  ('All files', '*')]
        filename = askopenfilename(filetypes=ftypes,
                                   defaultextension='.txt')
        if not filename: return
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()

        rules = []
        lexicon = []
        state = 'rules'
        for line in lines:
            line = line.strip()
            if not line:
                continue
            elif line.startswith("-"):
                if line.find("Rules")>0: state = 'rules'
                else: state = 'lexicon'
            else:
                toks = line.split()
                if state == 'rules' and len(toks)>=3 and toks[1]=='->':
                    rules.append(line)
                elif state == 'lexicon' and len(toks)>=2:
                    lexicon.append(line)
                    
        self.clear()
        self.grammarRules.insert(1.0, '\n'.join(rules))
        self.lexicon.insert(1.0, '\n'.join(lexicon))

    def clear(self, *args):
        "Clears the grammar and lexical and sentence inputs"
        self.grammarRules.delete(1.0, Tkinter.END)
        self.lexicon.delete(1.0, Tkinter.END)
        self.sentence.set('')

    def destroy(self, *args):
        if self._root is None: return
        self._root.destroy()
        self._root = None
        print self.sentence.get()


def testChartViewer():
    grammar = EarleyCFG(cfg.Nonterminal('S'),
                        map(lambda x:parseRule(x),
                            ["S -> NP VP", "NP -> N", "NP -> Det N",
                             "VP -> V", "VP -> V NP"]),
                        map(lambda x:parseLexicon(x),
                            ["Poirot N", "sent V", "the Det", "solutions N"]))

    sent = 'Poirot sent the solutions'
    tok_sent = WSTokenizer().tokenize(sent)

    print 'grammar= ('
    for rule in grammar.productions():
        print '    ', repr(rule)+','
    print ')'
    print 'sentence = %r' % sent
    print 'Calling "FullChartViewer(grammar, tok_sent)"...'
    FullChartViewer(grammar, tok_sent, "Earley Parser")


if __name__ == '__main__':
    GrammarGUI(None, None)

#    testChartViewer()
