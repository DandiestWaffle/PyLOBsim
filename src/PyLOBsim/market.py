'''
Created on 16 Apr 2013

@author: Ash Booth
'''
import sys
import random
from PyLOB import OrderBook
from datareader import DataModel 
from traders import MarketMaker, HFT, FBuyer, FSeller

class Market(object):
    '''
    classdocs
    '''

    def __init__(self, usingAgents, symbol, filename=None):
        '''
        Constructor
        '''
        self.usingAgents = usingAgents
        self.dataModel = None
        self.inDatafile = filename
        self.symbol  = symbol.ljust(6)
        self.traders = {}
        self.exchange = OrderBook()
        self.dataLOB = OrderBook()
        self.dataOnlyPrices = {}
        self.beforePrices = []
        self.afterPrices = []
        
    def initiateDataModel(self, verbose):
        '''
        Creates the traders from traders_spec. 
        Returns tuple (buyers, sellers).
        '''
        self.dataModel = DataModel(self.symbol)
        self.dataModel.readFile(self.inDatafile, verbose)
        
    def populateMarket(self, tradersSpec, verbose):
        '''
        Creates the traders from traders_spec. 
        Returns tuple (buyers, sellers).
        '''
        def traderType(agentType, name):
            if agentType == 'MM':
                return MarketMaker('MM', name, 0.00)
            elif agentType == 'HFT':
                    return HFT('HFT', name, 0.00)
            elif agentType == 'FBYR':
                    return FBuyer('FBYR', name, 0.00)
            elif agentType == 'FSLR':
                    return FSeller('FSLR', name, 0.00)
            else:
                sys.exit("FATAL: don't know agent type %s\n" % agentType)
        if self.usingAgents:
            n_agents = 0
            for agentType in tradersSpec:
                ttype = agentType[0]
                for a in range(agentType[1]):
                    tname = 'B%02d' % n_agents  # Trader i.d. string
                    self.traders[tname] = traderType(ttype, tname)
                    n_agents += 1
            if n_agents < 1:
                print 'WARNING: No agents specified\n'
        if self.usingAgents and verbose :
            for t in range(n_agents):
                name = 'B%02d' % t
                print(self.traders[name])
                
    
    def tradeStats(self, expid, dumpfile, time):
        '''
        Dumps CSV statistics on self.exchange data and trader population to 
        file for later analysis.
        '''
        if self.usingAgents:
            trader_types = {}
            for t in self.traders:
                ttype = self.traders[t].ttype
                if ttype in trader_types.keys():
                    t_balance = (trader_types[ttype]['balance_sum'] + 
                                 self.traders[t].balance)
                    n = trader_types[ttype]['n'] + 1
                else:
                    t_balance = self.traders[t].balance
                    n = 1
                trader_types[ttype] = {'n':n, 'balance_sum':t_balance}
    
            dumpfile.write('%s, %06d, ' % (expid, time))
            for ttype in sorted(list(trader_types.keys())):
                    n = trader_types[ttype]['n']
                    s = trader_types[ttype]['balance_sum']
                    dumpfile.write('%s, %d, %d, %f, ' % 
                                   (ttype, s, n, s / float(n)))
    
            dumpfile.write('\n');
    
    def plotPrices(self):
        import pylab
        prices = []
        times = []
        print "Num of trades = ", len(self.exchange.tape)
        for tapeitem in self.exchange.tape:
            prices.append(tapeitem['price'])
            times.append(tapeitem['time'])
        pylab.plot(times,prices,'k')
        pylab.show()
    
    def run(self, sessId, startTime, endTime, traderSpec, dumpFile, agentProb):
        '''
        One day run of the market
        ''' 
        
#         def printTime(milliseconds):
#             x = milliseconds / 1000
#             seconds = x % 60
#             x /= 60
#             minutes = x % 60
#             x /= 60
#             hours = x % 24
        
        self.dataModel.resetModel()
        self.populateMarket(traderSpec, False)
        
        processVerbose = False
        respondVerbose = False
        bookkeepVerbose = False
        
        time = startTime
        time = 0
        day_ended = False
        while not day_ended:
            timeLeft = (endTime - time) / endTime
            if time % 10000 == 0:
                print "time is %d" % time
            trades = []
            if self.usingAgents and random.random() < agentProb:
                # Get action from agents
                tid = random.choice(self.traders.keys())
                action = self.traders[tid].getAction(time, 
                                                     timeLeft, 
                                                     self.exchange)
                fromData = False
            else:
                # Get action from data
                action, day_ended = self.dataModel.getNextAction(self.exchange)
                fromData = True
            if action != None:
                if 'timestamp' in action:
                    time = action['timestamp']
                atype = action['type']
                if atype == 'market' or atype =='limit':
                    if fromData:
                        if atype == 'limit':
                            oriBA = self.dataLOB.getBestAsk()
                            oriBB = self.dataLOB.getBestBid()
                            newBA = self.exchange.getBestAsk()
                            newBB = self.exchange.getBestBid()
                            if (oriBA != None and oriBB != None and 
                                newBA != None and newBB != None):
                                oriMid = oriBB + (oriBA-oriBB)/2.0
                                newMid = newBB + (newBA-newBB)/2.0
                                deviation = ((action['price']-oriMid) / oriMid)
                                newPrice = newMid + (newMid*deviation)
                                if newPrice != action['price']:
                                    print newPrice
                                    print action['price']
                                    print '\n'
                                    pass
                                action['price'] = newPrice
                        self.dataLOB.processOrder(action, 
                                                  True, 
                                                  processVerbose)
                    res_trades, orderInBook = self.exchange.processOrder(action, 
                                                                fromData, 
                                                                processVerbose)
                    if res_trades:
                        for t in res_trades:
                            trades.append(t)
                elif action['type'] == 'cancel':
                    if fromData:
                        self.exchange.cancelOrder(action['side'], 
                                                  action['idNum'],
                                                  time = action['timestamp'])
                        self.dataLOB.cancelOrder(action['side'], 
                                             action['idNum'],
                                             time = action['timestamp'])
                    else:
                        self.exchange.cancelOrder(action['side'], 
                                                  action['idNum'])
                elif action['type'] == 'modify':
                    if fromData:
                        self.exchange.modifyOrder(action['idNum'], 
                                                  action,
                                                  time = action['timestamp'])
                        self.dataLOB.modifyOrder(action['idNum'], 
                                             action,
                                             time = action['timestamp'])
                    else:
                        self.exchange.modifyOrder(action['idNum'], 
                                                  action)
                # Does the originating trader need to be informed of limit 
                # orders that have been put in the book?
                if orderInBook and not fromData:
                    self.traders[tid].orderInBook(orderInBook)
                    
                for trade in trades:
                    # Counter-parties update order lists and blotters
                    if trade['party1'][0] != -1:
                        self.traders[trade['party1'][0]].bookkeep(trade,
                                                                  trade['party1'][1],
                                                                  trade['party1'][2],
                                                                  bookkeepVerbose)
                    if trade['party2'][0] != -1:
                        self.traders[trade['party2'][0]].bookkeep(trade, 
                                                                  trade['party2'][1],
                                                                  trade['party2'][2],
                                                                  bookkeepVerbose)
                    # Traders respond to whatever happened
                    if self.usingAgents:
                        for t in self.traders.keys():
                            self.traders[t].respond(time, self.exchange, 
                                                    trade, respondVerbose)
            time+=1
        print "experiment finished..."
        # end of an experiment -- dump the tape
        self.exchange.tapeDump('transactions.csv', 'w', 'keep')
 
        # write trade_stats for this experiment NB end-of-session summary only
        self.tradeStats(sessId, dumpFile, time)
   
    def genDataMap(self, startTime, endTime, verbose):
        '''
        Runs the market with the order book data to create a map of times to
        prices.
        '''
        
        def storePrice(action, lob):
            bestAsk = lob.getBestAsk()
            bestBid = lob.getBestBid()
            midPrice = None
            if bestAsk!=None and bestBid!=None:
                midPrice = bestBid + (bestAsk-bestBid)/2.0
                self.dataOnlyPrices[action['uei']] = midPrice

        self.initiateDataModel(verbose)
        dataLOB = OrderBook()
        processVerbose = False
        
        if verbose: print "\nCreating data map..."

        l = 0
        c = 0
        m = 0
        ma = 0
        time = 0
        dayEnded = False
        while not dayEnded:
            if time % 10000 == 0:
                print "time is %d" % time
            action, dayEnded = self.dataModel.getNextAction(dataLOB)
            if action != None:
                atype = action['type']
                if atype == 'market': 
                    ma+=1
                    dataLOB.processOrder(action, True, processVerbose)
                elif atype =='limit':
                    storePrice(action, dataLOB)
                    l+=1
                    dataLOB.processOrder(action, True, processVerbose)
                elif action['type'] == 'cancel':
                    dataLOB.cancelOrder(action['side'], 
                                        action['idNum'],
                                        time = action['timestamp'])
                    c+=1
                elif action['type'] == 'modify':
                    dataLOB.modifyOrder(action['idNum'], 
                                        action,
                                        time = action['timestamp'])
                    m+=1
            time += 1
        if verbose:
            print "\nCreated data map..."
            print "Limits: %d" % l
            print "Cancels: %d" % c
            print "Modifys: %d" % m
            print "Markets: %d" % ma
        







        