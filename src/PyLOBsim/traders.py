'''
Created on 15 Apr 2013

@author: Ash Booth

TODO:


'''

class Trader(object):
    '''
    Trader superclass. All Traders have:
    - a trader id
    - bank balance
    - blotter
    - list of orders to execute
    '''

    def __init__(self, ttype, tid, balance):
        self.ttype = ttype
        self.tid = tid
        self.balance = balance
        self.blotter = []
        self.outstandingOrders = []
        self.willing = 1
        self.able = 1
        self.lastquote = None

    def bookkeep(self, trade, side, verbose):
        self.blotter.append(trade)  # add trade record to trader's blotter
        # NB What follows is **LAZY** -- assumes all orders are quantity=1
        transactionPrice = trade['price']
        prevBalance = self.balance
        if side == 'bid':
            self.balance -= transactionPrice
        else:
            self.balance += transactionPrice
        if verbose: print('previous balance=%f, new balance=%f ' % 
                          (prevBalance, self.balance))
        
    def respond(self, time, lob, trade, verbose):
        '''
        Specify how trader responds to events in the market. This is a null 
        action, expect it to be overloaded with clever things by specific 
        algorithms
        '''
        return None

    def __str__(self):
        return ('[TID %s type %s balance %s blotter %s orders %s]' % 
                (self.tid, self.ttype, 
                 self.balance, self.blotter, 
                 self.outstandingOrders))
        
        
class MarketMaker(Trader):
    '''
    Intermediaries, that post prices on both sides of the order book and
    try to maintain their position throughout the day, making their income from
    the difference between their bid and offer price.
    '''
    
    def getOrder(self):
        pass
    

class HFT(Trader):
    '''
    High Frequency Traders, who have a relatively low net position throughout
    the day, compared to their activity. They are similar MarketMakers, but
    have much higher trading activity and much shorter holding periods.
    '''
    
    def getOrder(self):
        pass
    

class FBuyers(Trader):
    '''
    Fundamental Buyers, who try to build a long position during the day.
    '''
    
    def getOrder(self):
        pass


class FSellers(Trader):
    '''
    Fundamental Sellers, who try to build a short position during the day.
    '''
    
    def getOrder(self):
        pass
    
    
class Opportunistic(Trader):
    '''
    Opportunistic Traders, who may behave as intermediaries at times, or as
    fundamental traders at times when they see significant directional moves.
    '''
    
    def getOrder(self):
        pass
    
    
    
    
    
    
    
    
        