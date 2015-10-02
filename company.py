from openerp.osv import fields, osv

class res_company(osv.Model):
    _inherit = "res.company"
    _columns = {
        'triage_ids': fields.many2many(
		    'res.users',
		    'fnx_hd_rescompany_triage_rel',
		    'fnx_hd_tg_cid',
		    'fnx_hd_tg_uid',
		    string='Triage Users',
		    ),
        'inhouse_ids': fields.many2many(
		    'res.users',
		    'fnx_hd_rescompany_inhouse_rel',
		    'fnx_hd_ih_cid',
		    'fnx_hd_ih_uid',
		    string='In House Users',
		    ),
        'evs_ids': fields.many2many(
		    'res.users',
		    'fnx_hd_rescompany_evs_rel',
		    'fnx_hd_es_cid',
		    'fnx_hd_es_uid',
		    string='EvS Users',
		    ),
        }