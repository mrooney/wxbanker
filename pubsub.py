class Publisher:
    subscribers = {"": []}

    def subscribe(self, callable, message=""):
        if self.subscribers.has_key(message):
            self.subscribers[message].append(callable)
        else:
            self.subscribers[message] = [callable]

    def sendMessage(self, message, data=None):
        specificSubs = self.subscribers.get(message, [])
        genericSubs = self.subscribers[""]
        #iterate over all the subscribers, but don't duplicate
        for subscriber in set(specificSubs + genericSubs):
            try:
                subscriber(message, data)
            except:
                import traceback
                traceback.print_exc()