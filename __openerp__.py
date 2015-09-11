{
   'name': 'Fnx Quality Help Desk',
    'version': '0.1',
    'category': 'Generic Modules',
    'description': """\
            Phoenix help desk system.
            """,
    'author': 'Emile van Sebille',
    'maintainer': 'Emile van Sebille',
    'website': 'www.openerp.com',
    'depends': [
        'mail',
        ],
    'js': [
        ],
    'css':[
        # 'static/src/css/fnx_hd.css',
        ],
    'update_xml': [
        'security/help_desk_security.xaml',
        'security/ir.model.access.csv',
        'help_desk_view.xaml',
        ],
    'test': [],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
