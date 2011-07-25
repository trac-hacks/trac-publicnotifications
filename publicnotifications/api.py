from trac.core import *
from trac.config import Option
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionCache
from trac.ticket import notification as ticketnotification

smtp_public_always_cc = None
saved_get_recipients = None

def get_recipients(self, tktid):
    """
    Returns a pair of list of not opt-out subscribers to the ticket `tktid`.
    
    First list represents the direct recipients (To:), second list
    represents the recipients in carbon copy (Cc:).
    """

    def build_addresses(rcpts):
        """Format and remove invalid addresses"""
        return filter(lambda x: x, [self.get_smtp_address(addr) for addr in rcpts])

    (to, cc) = saved_get_recipients(self, tktid)

    # Can ticket be viewed by an anonymous user?
    if 'TICKET_VIEW' in PermissionCache(self.env, None, self.ticket.resource):
        always_cc = smtp_public_always_cc and build_addresses(smtp_public_always_cc.replace(',', ' ').split()) or []

        for addr in always_cc:
            if addr not in to and addr not in cc:
                cc.append(addr)

    return (to, cc)

class PublicNotifications(Component):
    """
    This component allows to define CC address(es) used only for public tickets notifications.
    """

    smtp_public_always_cc = Option('notification', 'smtp_public_always_cc', '',
        """Email address(es) to always send notifications for public tickets to,
           addresses can be seen by all recipients (Cc:).""")
    
    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        global smtp_public_always_cc
        global saved_get_recipients

        if self.compmgr.enabled[self.__class__]:
            if saved_get_recipients is None:
                saved_get_recipients = ticketnotification.TicketNotifyEmail.get_recipients
                ticketnotification.TicketNotifyEmail.get_recipients = get_recipients

        smtp_public_always_cc = self.smtp_public_always_cc
    
    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        """
        Called when a new Trac environment is created.
        """

        pass

    def environment_needs_upgrade(self, db):
        """
        Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        
        """

        return False

    def upgrade_environment(self, db):
        """
        Actually performs an environment upgrade.

        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """

        pass
