import threading
import string
import openerp
from collections import defaultdict
from fnx import translator, grouped
from openerp import SUPERUSER_ID
from osv.osv import except_osv as ERPError
from osv import fields, osv, orm
from psycopg2 import ProgrammingError
from xaml import Xaml

POS_NEG_NA = (
    ('negative', 'Negative'),
    ('positive', 'Positive'),
    )

class help_desk(osv.Model):
    _name = 'fnx.help_desk'
    _description = 'problem and solution'
    _inherit = ['mail.thread']
    _inherits = {}
    _mirrors = {}

    _columns = {
        'name': fields.char('Short Summary', size=256, required=True),
        'description': fields.text('Detailed Description', required=True),
        'problem': fields.text('Problem'),
        'user_solution': fields.text('User Solution'),
        'tech_solution': fields.text('Tech Solution'),
        'state': fields.selection(
            (('new', 'New'), ('in_house', 'In House'), ('evs', 'EvS'),  ('done', 'Resolved')),
            string='Status',
            track_visibility='change_only',
            ),
        'reported_by': fields.many2one('res.users', 'Reported By', required=True),
        'assigned_to': fields.many2one(
            'res.users',
            'Assigned To',
            domain=[('groups_id.category_id.name','=','Help Desk'),],
            track_visibility='change_only',
            ),
        }

    _defaults = {
        'state': lambda *a: 'new',
        'reported_by': lambda obj,cr,uid,ctx: uid != 1 and uid or False
        }

    def create(self, cr, uid, values, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['help_desk_creation'] = True
        assigned = values.get('assigned_to')
        if assigned:
            values['message_follower_user_ids'] = [assigned]
        new_id = super(help_desk, self).create(cr, uid, values, context=ctx)
        # issue has been created, notify Triage
        res_users = self.pool.get('res.users')
        user = res_users.browse(cr, uid, uid, context=context)
        triage_ids = [u.id for u in user.company_id.triage_ids]
        print 'triage ids', triage_ids
        if triage_ids:
            print 'notifying...'
            res_users.message_notify(
                    cr, uid, triage_ids,
                    body="Issue created",
                    type='email',
                    model=self._name,
                    res_id=new_id,
                    context=ctx)
        return new_id

    def onchange_assigned(self, cr, uid, ids, assigned, context=None):
        print assigned
        return {}

    def write(self, cr, uid, ids, values, context=None):
        if context is None:
            context = {}
        assigned = values.get('assigned_to')
        if 'state' in values:
            if context.get('help_desk_creation') and values['state'] == 'new':
                pass
            else:
                user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
                if (
                    (values['state'] == 'evs' and not user.has_group('fnx_hd.fnx_help_desk_manager')) or
                    (values['state'] != 'evs' and not user.has_group('fnx_hd.fnx_help_desk_user'))
                    ):
                    raise ERPError(
                        'Permission Denied',
                        'You do not have permission to change the status to %s.' % values['state'],
                        )
        if assigned and not context.get('help_desk_creation'):
            self.message_subscribe_users(cr, uid, ids, [assigned], context=context)
        return super(help_desk, self).write(cr, uid, ids, values, context=context)
