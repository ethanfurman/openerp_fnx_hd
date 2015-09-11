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
    _inherit = []
    _inherits = {}
    _mirrors = {}
    # _order = 'lot_no'

    _columns = {
        'name': fields.char('Short Summary', size=64),
        'description': fields.text('Detailed Description'),
        'problem': fields.text('Problem'),
        'user_solution': fields.text('User Solution'),
        'tech_solution': fields.text('Tech Solution'),
        'state': fields.selection(
            (('new', 'New'), ('in_house', 'In House'), ('evs', 'EvS'),  ('done', 'Resolved')),
            string='Status',
            ),
        }

    _defaults = {
        'state': lambda *a: 'new',
        }

    def write(self, cr, uid, ids, values, context=None):
        print 'help_desk.write', uid, values
        if 'state' in values:
            user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
            if (
                not user.has_group('fnx_hd.user')
                or (state == 'evs' and not user.has_group('fnx_hd.manager'))
                ):
                raise ERPError('Permission Denied', 'You do not have permission to change the status to %s.' % values['state'])
        return super(help_desk, self).write(cr, uid, ids, values, context=context)
