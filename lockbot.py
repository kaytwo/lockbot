from errbot import BotPlugin, botcmd, arg_botcmd
import time

class Lockbot(BotPlugin):
  """Lockbot plugin for Err"""

  def activate(self):
    '''deal with persistence and start the lock expirer'''
    super().activate()
    if 'locks' not in self:
      self.locks = {}
      self['locks'] = self.locks
    else:
      self.locks = self['locks']

    # lock expiration
    self.start_poller(15,self.expire_locks)

  def get_lock(self,channel,resource):
    k = self.get_key(resource,channel=channel)
    if k in self.locks:
      return self.locks[k]
    else:
      return None

  def set_lock(self,channel,resource,owner,duration):
    # todo: don't clobber someone else's lock
    old_lock = self.get_lock(channel,resource)
    
    # successful case
    k = self.get_key(channel,resource)
    self.locks[k] = (channel,resource,owner,time.time() + duration*60)
    self['locks'] = self.locks
    return True

  def remove_lock(self,channel,resource,owner):
    k = self.get_key(resource,channel)
    if k in self.locks:
      _,_,lock_owner,_ = self.locks[k]
      if lock_owner == owner:
        del self[k]
        self['locks'] = self.locks
        return True
    else:
      return False

  def get_key(self,resource,channel):
    return channel + ',' + resource

  def remove_all(self,channel,speaker):
    return False

  @arg_botcmd('duration',type=int,default=30,nargs='?')
  @arg_botcmd('resource',type=str)
  def lock(self, msg, resource=None,duration=None):
    """Lock a resource. Duration defaults to 30 minutes.
    """
    channel = msg.to.channelname
    speaker = msg.frm.nick
    if resource is None:
      return "@{}: please specify a resource to lock.".format(speaker)
    else:
      # allow multiple channels by keying off of what channel + what resource
      if self.set_lock(channel,resource,speaker,duration):
        return "You have successfully locked {} for {} minutes.".format(resource,duration)
      else:
        return "@{}: {} is owned by {} for another {} minutes.".format(speaker,resource,error.owner,error.duration)
        
  
  @arg_botcmd('resource',type=str)
  def unlock(self, msg, resource=None):
    """Unlock a resource. """
    speaker = msg.frm.nick
    channel = msg.to.channelname
    if resource is None:
      return "@{}: please specify a resource to unlock.".format(speaker)
    else:
      if self.remove_lock(channel,resource,speaker):
        # todo: alert anyone that tried to lock this while it was locked
        return "`{}` now unlocked.".format(resource)
      else:
        return "@{}: you don't own {}! Don't clobber anybody else's edits!".format(speaker,resource)

  @botcmd
  def unlockall(self, msg, args):
    """Unlock everything you have locked.
    Takes no arguments.
    """
    speaker = msg.frm.nick
    channel = msg.to.channelname
    unlocked = self.remove_all(channel,speaker)
    if len(unlocked) == 0:
      return "/shrug Uhhhhhhhhh you didn't have any locks, so you didn't unlock anything."
    else:
      return "`{}` now unlocked.".format(','.join(unlocked))

  @botcmd
  def showlocks(self, msg, args):
    """show who owns what and for how much longer.
    Takes no arguments.
    """
    outputs = []
    for v in self.locks.values():
      outputs.append("channel: {} resource: {} owner: {} duration: {}".format(*v))
    return "Here's who owns what: {}".format(' '.join(outputs))

  def expire_locks(self):
    self.log.debug("lock cleanup called")
