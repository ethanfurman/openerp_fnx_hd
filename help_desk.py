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

    def _get_partner_ids(self, cr, type):
        # type -> one of ['Triage', 'In-House', 'EvS']
        res_users = self.pool.get('res.users')
        return [
                u.partner_id.id
                for u in res_users.browse(
                    cr, SUPERUSER_ID,
                    [('groups_id.name','=',type),('groups_id.category_id.name','=','Fnx Help Desk')],
                    )
                ]

    def onchange_assigned(self, cr, uid, ids, assigned, context=None):
        if not assigned:
            return {}
        user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, assigned, context=context)
        if user.has_group('fnx_hd.fnx_help_desk_evs'):
            state = 'evs'
        elif user.has_group('fnx_hd.fnx_help_desk_inhouse'):
            state = 'in_house'
        else:
            return {}
        res = {'value': {'state':state}}
        return res

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
            domain=[('groups_id.category_id.name','=','Fnx Help Desk'),],
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
        assigned = values.get('assigned_to')
        values['message_follower_ids'] = [
                self.pool.get('res.users').browse(cr, uid, values['reported_by']).partner_id.id
                    ]
        if not assigned:
            values['message_notify_ids'] = self._get_partner_ids(cr, 'Triage')
        else:
            values['message_follower_user_ids'].append[assigned]
            user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, assigned, context=context)
            if user.has_group('fnx_hd.fnx_help_desk_evs'):
                values['state'] = 'evs'
            elif user.has_group('fnx_hd.fnx_help_desk_inhouse'):
                values['state'] = 'in_house'
            else:
                raise ValueError('unrecognized group for %r' % user.login)
        return super(help_desk, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        if context is None:
            context = {}
        assigned = values.get('assigned_to')
        if assigned:
            values['message_follower_user_ids'] = [assigned]
        if 'state' in values:
            state = values['state']
            user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
            if (
                (state == 'evs' and not (user.has_group('fnx_hd.fnx_help_desk_triage') or user.has_group('fnx_hd.fnx_help_desk_evs'))) or
                (state == 'in_house' and not (user.has_group('fnx_hd.fnx_help_desk_triage') or user.has_group('fnx_hd.fnx_help_desk_inhouse'))) or
                (state == 'done' and not (user.has_group('fnx_hd.fnx_help_desk_evs') or user.has_group('fnx_hd.fnx_help_desk_inhouse')))
                ):
                raise ERPError(
                    'Permission Denied',
                    'You do not have permission to change the status to %s.' % state,
                    )
            if not assigned and state != 'done':
                # if no one is assigned, notify the group
                issues = self.read(cr, uid, ids, fields=['id', 'assigned_to'], context=context)
                assigned_issues = []
                unassigned_issues = []
                for issue in issues:
                    if issue['assigned_to']:
                        assigned_issues.append(issue['id'])
                    else:
                        unassigned_issues.append(issue['id'])
                if unassigned_issues:
                    if state == 'new':
                        notify_ids = self._get_partner_ids(cr, 'Triage')
                    elif state == 'in_house':
                        notify_ids = self._get_partner_ids(cr, 'In-House')
                    elif state == 'evs':
                        notify_ids = self._get_partner_ids(cr, 'EvS')
                    vals = values.copy()
                    vals['message_notify_ids'] = notify_ids
                if not super(help_desk, self).write(cr, uid, unassigned_issues, vals, context=context):
                    return False
                ids = assigned_issues
        if ids:
            return super(help_desk, self).write(cr, uid, ids, values, context=context)
        return True
